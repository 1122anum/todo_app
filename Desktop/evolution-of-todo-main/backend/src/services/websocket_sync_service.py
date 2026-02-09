"""
WebSocket Sync Service for real-time task synchronization.

This service:
1. Maintains WebSocket connections with authenticated clients (T065)
2. Subscribes to task-updates topic via Dapr Pub/Sub (T066)
3. Pushes events to connected clients based on user_id (T067)
4. Implements heartbeat/ping-pong for connection health (T068)

Architecture:
- FastAPI with WebSocket support
- Dapr Pub/Sub for event consumption
- In-memory connection registry (user_id -> WebSocket connections)
- JWT authentication for WebSocket connections
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="WebSocket Sync Service",
    description="Real-time task synchronization via WebSocket",
    version="1.0.0"
)

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# Connection registry: user_id -> Set of WebSocket connections
connections: Dict[int, Set[WebSocket]] = {}

# Heartbeat configuration
HEARTBEAT_INTERVAL = 30  # seconds
HEARTBEAT_TIMEOUT = 60  # seconds


# Models
class TaskUpdateEvent(BaseModel):
    """Event model for task updates."""
    event_id: str
    event_type: str  # task.created, task.updated, task.completed, task.deleted
    task_id: int
    user_id: int
    timestamp: str
    changes: Optional[Dict] = None
    task_data: Optional[Dict] = None


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str  # event, ping, pong, error
    data: Optional[Dict] = None
    timestamp: str


# Authentication
security = HTTPBearer()


def verify_token(token: str) -> Dict:
    """
    Verify JWT token and extract user information.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload with user_id

    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# Connection Management
class ConnectionManager:
    """Manages WebSocket connections per user."""

    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Register a new WebSocket connection for a user.

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat()
        }

        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.connection_metadata:
            user_id = self.connection_metadata[websocket]["user_id"]

            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)

                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            del self.connection_metadata[websocket]
            logger.info(f"User {user_id} disconnected")

    async def send_to_user(self, user_id: int, message: Dict):
        """
        Send a message to all connections for a specific user.

        Args:
            user_id: Target user ID
            message: Message to send
        """
        if user_id not in self.active_connections:
            return

        disconnected = set()

        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                disconnected.add(websocket)

        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast(self, message: Dict):
        """
        Broadcast a message to all connected users.

        Args:
            message: Message to broadcast
        """
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)

    def get_connection_count(self, user_id: Optional[int] = None) -> int:
        """Get connection count for a user or total."""
        if user_id:
            return len(self.active_connections.get(user_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())


# Initialize connection manager
manager = ConnectionManager()


# WebSocket Endpoint (T065: Authentication)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket endpoint for real-time task synchronization.

    Query parameter:
        token: JWT authentication token

    Message format:
        Client -> Server: {"type": "ping"}
        Server -> Client: {"type": "pong", "timestamp": "..."}
        Server -> Client: {"type": "event", "data": {...}, "timestamp": "..."}
    """
    # Authenticate
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    try:
        payload = verify_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    # Connect
    await manager.connect(websocket, user_id)

    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "data": {"user_id": user_id},
        "timestamp": datetime.utcnow().isoformat()
    })

    # Start heartbeat task
    heartbeat_task = asyncio.create_task(heartbeat_loop(websocket, user_id))

    try:
        # Listen for client messages
        while True:
            data = await websocket.receive_json()

            # Handle ping
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Update last heartbeat
                if websocket in manager.connection_metadata:
                    manager.connection_metadata[websocket]["last_heartbeat"] = datetime.utcnow().isoformat()

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        heartbeat_task.cancel()
        manager.disconnect(websocket)


# T068: Heartbeat implementation
async def heartbeat_loop(websocket: WebSocket, user_id: int):
    """
    Send periodic heartbeat pings to keep connection alive.

    Args:
        websocket: WebSocket connection
        user_id: User ID
    """
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)

            try:
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Heartbeat failed for user {user_id}: {e}")
                break
    except asyncio.CancelledError:
        pass


# T066: Dapr Pub/Sub subscription endpoint
@app.post("/dapr/subscribe")
async def dapr_subscribe():
    """
    Dapr subscription endpoint.

    Returns list of topics to subscribe to.
    """
    return [
        {
            "pubsubname": "pubsub",
            "topic": "task-updates",
            "route": "/events/task-updates"
        }
    ]


# T067: Event-to-WebSocket push logic
@app.post("/events/task-updates")
async def handle_task_update(event: TaskUpdateEvent):
    """
    Handle task update events from Dapr Pub/Sub.

    Pushes events to connected WebSocket clients for the affected user.

    Args:
        event: Task update event
    """
    try:
        logger.info(f"Received event: {event.event_type} for task {event.task_id}, user {event.user_id}")

        # Prepare message for WebSocket clients
        message = {
            "type": "event",
            "data": {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "task_id": event.task_id,
                "changes": event.changes,
                "task_data": event.task_data
            },
            "timestamp": event.timestamp
        }

        # Send to user's connections
        await manager.send_to_user(event.user_id, message)

        logger.info(f"Event pushed to {manager.get_connection_count(event.user_id)} connections for user {event.user_id}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error handling task update: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "websocket-sync-service",
        "connections": manager.get_connection_count(),
        "timestamp": datetime.utcnow().isoformat()
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Metrics endpoint for monitoring."""
    return {
        "total_connections": manager.get_connection_count(),
        "users_connected": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
