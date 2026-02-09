"""
Audit Log Service for tracking all task changes.

This service:
1. Subscribes to task-events topic via Dapr Pub/Sub (T075)
2. Persists audit records via Dapr State Management (T076)
3. Provides API endpoint for querying audit trail (T077)

Architecture:
- FastAPI microservice
- Dapr Pub/Sub for event consumption
- Dapr State Store for audit record persistence
- Query API for retrieving audit history
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel
import httpx
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Audit Log Service",
    description="Task change audit trail and history tracking",
    version="1.0.0"
)

# Dapr configuration
DAPR_HTTP_PORT = int(os.getenv("DAPR_HTTP_PORT", "3500"))
DAPR_STATE_STORE = "statestore"


# Models
class TaskEvent(BaseModel):
    """Task event model from task-events topic."""
    schema_version: str
    event_id: str
    event_type: str
    timestamp: str
    user_id: int
    task: Dict[str, Any]
    changes: Optional[Dict[str, Dict[str, Any]]] = None
    metadata: Dict[str, Any]


class AuditRecord(BaseModel):
    """Audit record model for persistence."""
    audit_id: str
    event_id: str
    event_type: str
    timestamp: str
    user_id: int
    task_id: int
    task_title: str
    changes: Optional[Dict[str, Dict[str, Any]]] = None
    task_snapshot: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str


class AuditRecordResponse(BaseModel):
    """Audit record response model."""
    audit_id: str
    event_type: str
    timestamp: str
    task_id: int
    task_title: str
    changes: Optional[Dict[str, Dict[str, Any]]] = None
    source: str
    correlation_id: str


# Dapr State Management
class DaprStateManager:
    """Manager for Dapr State Store operations."""

    def __init__(self, dapr_port: int = DAPR_HTTP_PORT, state_store: str = DAPR_STATE_STORE):
        self.dapr_url = f"http://localhost:{dapr_port}"
        self.state_store = state_store

    async def save_audit_record(self, audit_record: AuditRecord) -> bool:
        """
        Save audit record to Dapr State Store.

        Args:
            audit_record: Audit record to save

        Returns:
            True if saved successfully, False otherwise
        """
        url = f"{self.dapr_url}/v1.0/state/{self.state_store}"

        # Prepare state entry
        state_entry = [
            {
                "key": f"audit:{audit_record.user_id}:{audit_record.audit_id}",
                "value": audit_record.dict()
            }
        ]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=state_entry, timeout=5.0)
                response.raise_for_status()

            logger.info(f"Saved audit record: {audit_record.audit_id}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to save audit record: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving audit record: {str(e)}", exc_info=True)
            return False

    async def get_audit_records(
        self,
        user_id: int,
        task_id: Optional[int] = None,
        limit: int = 100
    ) -> List[AuditRecord]:
        """
        Get audit records for a user.

        Note: This is a simplified implementation. In production, you would use
        a proper database with indexing for efficient querying.

        Args:
            user_id: User ID
            task_id: Optional task ID filter
            limit: Maximum number of records to return

        Returns:
            List of audit records
        """
        # In production, use a database query instead of scanning state store
        # This is a placeholder implementation
        logger.warning("get_audit_records: Using simplified implementation. Use database in production.")
        return []


# Initialize state manager
state_manager = DaprStateManager()


# T075: Dapr Pub/Sub subscription endpoint
@app.post("/dapr/subscribe")
async def dapr_subscribe():
    """
    Dapr subscription endpoint.

    Returns list of topics to subscribe to.
    """
    return [
        {
            "pubsubname": "pubsub",
            "topic": "task-events",
            "route": "/events/task-events"
        }
    ]


# T076: Event handler with audit record persistence
@app.post("/events/task-events")
async def handle_task_event(event: TaskEvent):
    """
    Handle task events from Dapr Pub/Sub.

    Creates audit records for all task changes.

    Args:
        event: Task event from task-events topic
    """
    try:
        logger.info(f"Received event: {event.event_type} for task {event.task['id']}, user {event.user_id}")

        # Create audit record
        audit_record = AuditRecord(
            audit_id=event.event_id,
            event_id=event.event_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            user_id=event.user_id,
            task_id=event.task["id"],
            task_title=event.task["title"],
            changes=event.changes,
            task_snapshot=event.task,
            metadata=event.metadata,
            created_at=datetime.utcnow().isoformat() + "Z"
        )

        # Persist audit record
        success = await state_manager.save_audit_record(audit_record)

        if success:
            logger.info(f"Audit record created: {audit_record.audit_id}")
            return {"status": "success", "audit_id": audit_record.audit_id}
        else:
            logger.error(f"Failed to create audit record for event {event.event_id}")
            return {"status": "error", "message": "Failed to persist audit record"}

    except Exception as e:
        logger.error(f"Error handling task event: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# T077: Audit trail API endpoint
@app.get("/audit/users/{user_id}/tasks", response_model=List[AuditRecordResponse])
async def get_user_audit_trail(
    user_id: int,
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get audit trail for a user's tasks.

    Args:
        user_id: User ID
        task_id: Optional task ID filter
        event_type: Optional event type filter
        limit: Maximum number of records
        offset: Number of records to skip

    Returns:
        List of audit records
    """
    try:
        # Get audit records from state store
        records = await state_manager.get_audit_records(user_id, task_id, limit)

        # Filter by event type if specified
        if event_type:
            records = [r for r in records if r.event_type == event_type]

        # Apply pagination
        records = records[offset:offset + limit]

        # Convert to response model
        response = [
            AuditRecordResponse(
                audit_id=r.audit_id,
                event_type=r.event_type,
                timestamp=r.timestamp,
                task_id=r.task_id,
                task_title=r.task_title,
                changes=r.changes,
                source=r.metadata.get("source", "unknown"),
                correlation_id=r.metadata.get("correlation_id", "")
            )
            for r in records
        ]

        return response

    except Exception as e:
        logger.error(f"Error fetching audit trail: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch audit trail"
        )


@app.get("/audit/users/{user_id}/tasks/{task_id}", response_model=List[AuditRecordResponse])
async def get_task_audit_trail(
    user_id: int,
    task_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records")
):
    """
    Get audit trail for a specific task.

    Args:
        user_id: User ID (for authorization)
        task_id: Task ID
        limit: Maximum number of records

    Returns:
        List of audit records for the task
    """
    return await get_user_audit_trail(user_id=user_id, task_id=task_id, limit=limit)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "audit-log-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Metrics endpoint for monitoring."""
    # In production, use Prometheus client library
    return {
        "service": "audit-log-service",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
