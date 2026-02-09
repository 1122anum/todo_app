/**
 * WebSocket client for real-time task synchronization.
 *
 * Features:
 * - Automatic connection with JWT authentication (T071)
 * - Automatic reconnection with exponential backoff (T072)
 * - Heartbeat/ping-pong for connection health
 * - Event handling and callbacks
 * - Connection state management
 */

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error';

export interface WebSocketMessage {
  type: 'connected' | 'event' | 'heartbeat' | 'pong' | 'error';
  data?: any;
  timestamp: string;
}

export interface TaskUpdateEvent {
  event_id: string;
  event_type: 'task.created' | 'task.updated' | 'task.completed' | 'task.deleted';
  task_id: number;
  changes?: Record<string, any>;
  task_data?: any;
}

export interface WebSocketClientOptions {
  url: string;
  getToken: () => string | null;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onEvent?: (event: TaskUpdateEvent) => void;
  onError?: (error: Error) => void;
  onStateChange?: (state: ConnectionState) => void;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  reconnectDecay?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private options: Required<WebSocketClientOptions>;
  private state: ConnectionState = 'disconnected';
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private shouldReconnect = true;

  constructor(options: WebSocketClientOptions) {
    this.options = {
      url: options.url,
      getToken: options.getToken,
      onConnect: options.onConnect || (() => {}),
      onDisconnect: options.onDisconnect || (() => {}),
      onEvent: options.onEvent || (() => {}),
      onError: options.onError || (() => {}),
      onStateChange: options.onStateChange || (() => {}),
      reconnectInterval: options.reconnectInterval || 1000,
      maxReconnectInterval: options.maxReconnectInterval || 30000,
      reconnectDecay: options.reconnectDecay || 1.5,
      maxReconnectAttempts: options.maxReconnectAttempts || Infinity,
      heartbeatInterval: options.heartbeatInterval || 30000,
    };
  }

  /**
   * Connect to WebSocket server.
   */
  connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      console.warn('WebSocket already connected or connecting');
      return;
    }

    const token = this.options.getToken();
    if (!token) {
      this.handleError(new Error('No authentication token available'));
      return;
    }

    this.setState('connecting');
    this.shouldReconnect = true;

    try {
      const wsUrl = `${this.options.url}?token=${encodeURIComponent(token)}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleWebSocketError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      this.handleError(error as Error);
    }
  }

  /**
   * Disconnect from WebSocket server.
   */
  disconnect(): void {
    this.shouldReconnect = false;
    this.clearReconnectTimeout();
    this.clearHeartbeat();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.setState('disconnected');
  }

  /**
   * Get current connection state.
   */
  getState(): ConnectionState {
    return this.state;
  }

  /**
   * Check if connected.
   */
  isConnected(): boolean {
    return this.state === 'connected' && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Send a message to the server.
   */
  send(message: any): void {
    if (!this.isConnected()) {
      console.warn('Cannot send message: not connected');
      return;
    }

    try {
      this.ws!.send(JSON.stringify(message));
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  }

  /**
   * Send ping to server.
   */
  private sendPing(): void {
    this.send({ type: 'ping' });
  }

  /**
   * Handle WebSocket open event.
   */
  private handleOpen(): void {
    console.log('WebSocket connected');
    this.setState('connected');
    this.reconnectAttempts = 0;
    this.startHeartbeat();
    this.options.onConnect();
  }

  /**
   * Handle WebSocket message event.
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'connected':
          console.log('WebSocket connection confirmed:', message.data);
          break;

        case 'event':
          if (message.data) {
            this.options.onEvent(message.data as TaskUpdateEvent);
          }
          break;

        case 'heartbeat':
          // Server heartbeat received, respond with ping
          this.sendPing();
          break;

        case 'pong':
          // Pong received, connection is alive
          break;

        case 'error':
          console.error('Server error:', message.data);
          this.options.onError(new Error(message.data?.message || 'Server error'));
          break;

        default:
          console.warn('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket error event.
   */
  private handleWebSocketError(event: Event): void {
    console.error('WebSocket error:', event);
    this.setState('error');
    this.options.onError(new Error('WebSocket error'));
  }

  /**
   * Handle WebSocket close event.
   */
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket closed:', event.code, event.reason);
    this.clearHeartbeat();
    this.ws = null;

    if (this.state === 'connected') {
      this.options.onDisconnect();
    }

    if (this.shouldReconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.scheduleReconnect();
    } else {
      this.setState('disconnected');
    }
  }

  /**
   * Handle errors.
   */
  private handleError(error: Error): void {
    console.error('WebSocket client error:', error);
    this.setState('error');
    this.options.onError(error);

    if (this.shouldReconnect) {
      this.scheduleReconnect();
    }
  }

  /**
   * Schedule reconnection with exponential backoff.
   */
  private scheduleReconnect(): void {
    this.setState('reconnecting');
    this.clearReconnectTimeout();

    // Calculate backoff delay with exponential increase
    const delay = Math.min(
      this.options.reconnectInterval * Math.pow(this.options.reconnectDecay, this.reconnectAttempts),
      this.options.maxReconnectInterval
    );

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  /**
   * Clear reconnect timeout.
   */
  private clearReconnectTimeout(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  /**
   * Start heartbeat interval.
   */
  private startHeartbeat(): void {
    this.clearHeartbeat();

    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.sendPing();
      }
    }, this.options.heartbeatInterval);
  }

  /**
   * Clear heartbeat interval.
   */
  private clearHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Set connection state and notify listeners.
   */
  private setState(state: ConnectionState): void {
    if (this.state !== state) {
      this.state = state;
      this.options.onStateChange(state);
    }
  }
}

/**
 * React hook for WebSocket connection.
 */
import { useEffect, useState, useCallback, useRef } from 'react';

export function useWebSocket(options: Omit<WebSocketClientOptions, 'getToken'>) {
  const [state, setState] = useState<ConnectionState>('disconnected');
  const [lastEvent, setLastEvent] = useState<TaskUpdateEvent | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const clientRef = useRef<WebSocketClient | null>(null);

  const getToken = useCallback(() => {
    return localStorage.getItem('auth_token');
  }, []);

  useEffect(() => {
    const client = new WebSocketClient({
      ...options,
      getToken,
      onStateChange: setState,
      onEvent: (event) => {
        setLastEvent(event);
        options.onEvent?.(event);
      },
      onError: (err) => {
        setError(err);
        options.onError?.(err);
      },
    });

    clientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
    };
  }, [options.url]);

  const reconnect = useCallback(() => {
    clientRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
  }, []);

  return {
    state,
    lastEvent,
    error,
    isConnected: state === 'connected',
    reconnect,
    disconnect,
  };
}
