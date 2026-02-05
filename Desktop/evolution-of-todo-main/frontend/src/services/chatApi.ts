/**
 * Chat API Client for Phase III AI Chatbot
 *
 * Handles communication with the backend chat endpoint.
 * Provides functions for sending messages and managing conversations.
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  tool_calls: Array<{
    tool: string;
    parameters: Record<string, any>;
    result: Record<string, any>;
  }>;
}

export interface Conversation {
  id: string;
  created_at: string;
  updated_at: string;
}

/**
 * Send a chat message to the AI assistant.
 *
 * @param userId - Authenticated user ID
 * @param message - User's message text
 * @param conversationId - Optional conversation ID to continue existing conversation
 * @returns Chat response with AI assistant's reply
 */
export async function sendChatMessage(
  userId: string,
  message: string,
  conversationId?: string
): Promise<ChatResponse> {
  try {
    // Get auth token from localStorage (set by Better Auth)
    const token = localStorage.getItem('auth_token');

    if (!token) {
      throw new Error('Authentication required. Please sign in.');
    }

    const payload: ChatMessage = {
      message,
      ...(conversationId && { conversation_id: conversationId })
    };

    const response = await axios.post<ChatResponse>(
      `${API_BASE_URL}/api/${userId}/chat`,
      payload,
      {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        timeout: 30000 // 30 second timeout for AI responses
      }
    );

    return response.data;
  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        // Server responded with error status
        const status = error.response.status;
        const detail = error.response.data?.detail || 'An error occurred';

        switch (status) {
          case 400:
            throw new Error(`Invalid request: ${detail}`);
          case 401:
            throw new Error('Authentication failed. Please sign in again.');
          case 403:
            throw new Error('You do not have permission to access this conversation.');
          case 404:
            throw new Error('Conversation not found.');
          case 500:
            throw new Error('Server error. Please try again later.');
          default:
            throw new Error(detail);
        }
      } else if (error.request) {
        // Request made but no response received
        throw new Error('Unable to reach the server. Please check your connection.');
      }
    }

    // Generic error
    throw new Error(error.message || 'Failed to send message');
  }
}

/**
 * Get user's recent conversations.
 *
 * @param userId - Authenticated user ID
 * @param limit - Maximum number of conversations to retrieve (default: 20)
 * @returns List of conversation summaries
 */
export async function getUserConversations(
  userId: string,
  limit: number = 20
): Promise<Conversation[]> {
  try {
    const token = localStorage.getItem('auth_token');

    if (!token) {
      throw new Error('Authentication required. Please sign in.');
    }

    const response = await axios.get<Conversation[]>(
      `${API_BASE_URL}/api/${userId}/conversations`,
      {
        params: { limit },
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    return response.data;
  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        const status = error.response.status;
        const detail = error.response.data?.detail || 'An error occurred';

        switch (status) {
          case 401:
            throw new Error('Authentication failed. Please sign in again.');
          case 403:
            throw new Error('You do not have permission to access these conversations.');
          case 500:
            throw new Error('Server error. Please try again later.');
          default:
            throw new Error(detail);
        }
      } else if (error.request) {
        throw new Error('Unable to reach the server. Please check your connection.');
      }
    }

    throw new Error(error.message || 'Failed to fetch conversations');
  }
}

/**
 * Check if user is authenticated.
 *
 * @returns True if auth token exists
 */
export function isAuthenticated(): boolean {
  return !!localStorage.getItem('auth_token');
}

/**
 * Get current user ID from auth token or session.
 * This is a placeholder - actual implementation depends on Better Auth setup.
 *
 * @returns User ID or null if not authenticated
 */
export function getCurrentUserId(): string | null {
  // TODO: Implement proper user ID extraction from Better Auth session
  // For now, return from localStorage if available
  return localStorage.getItem('user_id');
}
