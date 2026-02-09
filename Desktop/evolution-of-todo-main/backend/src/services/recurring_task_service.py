"""
Recurring Task Service - Microservice for generating recurring task instances.

This service runs as a separate FastAPI application with Dapr sidecar.
It listens to Dapr Cron Binding (every minute) and generates task instances
for due recurrence patterns.
"""
from fastapi import FastAPI, Request, HTTPException
from sqlmodel import Session, create_engine, select
from datetime import datetime
from typing import List
import logging
import os

from backend.src.models.recurrence_pattern import RecurrencePattern
from backend.src.models.todo import Task
from backend.src.services.recurrence_pattern_service import RecurrencePatternService
from backend.src.services.todo_service import TodoService
from backend.src.services.dapr_event_publisher import DaprEventPublisher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Recurring Task Service",
    description="Microservice for generating recurring task instances",
    version="1.0.0"
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/todo_db")
engine = create_engine(DATABASE_URL, echo=False)

# Dapr event publisher
event_publisher = DaprEventPublisher()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "recurring-task-service",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/cron")
async def handle_cron_trigger(request: Request):
    """
    Handle Dapr Cron Binding trigger.

    This endpoint is called every minute by Dapr Cron Binding.
    It generates task instances for all due recurrence patterns.

    Dapr Cron Binding configuration:
    - Component: cron-binding (k8s/dapr-components/cron-binding.yaml)
    - Schedule: */1 * * * * (every minute)
    - Direction: input
    """
    try:
        logger.info("Cron trigger received - starting instance generation")

        # Get current time
        current_time = datetime.utcnow()

        # Generate instances
        generated_count = await generate_recurring_instances(current_time)

        logger.info(f"Instance generation complete: {generated_count} instances created")

        return {
            "status": "success",
            "generated_count": generated_count,
            "timestamp": current_time.isoformat()
        }

    except Exception as e:
        logger.error(f"Error in cron handler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def generate_recurring_instances(current_time: datetime) -> int:
    """
    Generate task instances for all due recurrence patterns.

    Args:
        current_time: Current timestamp

    Returns:
        Number of instances generated
    """
    generated_count = 0

    with Session(engine) as session:
        # Get services
        recurrence_service = RecurrencePatternService(session)
        todo_service = TodoService(session)

        # Get all due patterns
        due_patterns = recurrence_service.get_due_patterns(current_time)

        logger.info(f"Found {len(due_patterns)} due patterns")

        for pattern in due_patterns:
            try:
                # Get parent task for this pattern
                parent_task = get_parent_task(session, pattern.id)

                if not parent_task:
                    logger.warning(f"No parent task found for pattern {pattern.id}")
                    continue

                # Calculate next occurrence
                next_occurrence = recurrence_service.calculate_next_occurrence(
                    pattern,
                    current_time
                )

                if not next_occurrence:
                    logger.info(f"Pattern {pattern.id} has ended")
                    continue

                # Check if instance already exists for this occurrence
                if instance_exists(session, parent_task.id, next_occurrence):
                    logger.debug(f"Instance already exists for pattern {pattern.id} at {next_occurrence}")
                    continue

                # Create recurring instance
                instance = todo_service.create_recurring_instance(
                    parent_task=parent_task,
                    due_date=next_occurrence
                )

                logger.info(f"Created instance {instance.id} for pattern {pattern.id}")

                # Publish task.created event
                await event_publisher.publish_task_created(
                    task=instance,
                    source="recurring_task_service",
                    correlation_id=None
                )

                # Publish to task-updates for real-time sync
                await event_publisher.publish_task_update_sync(
                    task=instance,
                    event_type="task.created",
                    changes=None,
                    source="recurring_task_service",
                    correlation_id=None
                )

                # Mark pattern as generated
                recurrence_service.mark_generated(pattern.id, current_time)

                generated_count += 1

            except Exception as e:
                logger.error(f"Error generating instance for pattern {pattern.id}: {str(e)}", exc_info=True)
                # Continue with next pattern
                continue

    return generated_count


def get_parent_task(session: Session, pattern_id: int) -> Task:
    """
    Get the parent task for a recurrence pattern.

    Args:
        session: Database session
        pattern_id: Recurrence pattern ID

    Returns:
        Parent task or None
    """
    statement = select(Task).where(
        Task.recurrence_pattern_id == pattern_id,
        Task.is_recurring_instance == False
    )
    return session.exec(statement).first()


def instance_exists(session: Session, parent_task_id: int, due_date: datetime) -> bool:
    """
    Check if a recurring instance already exists for a given due date.

    Args:
        session: Database session
        parent_task_id: Parent task ID
        due_date: Due date to check

    Returns:
        True if instance exists, False otherwise
    """
    # Check for instances with same due date (within 1 minute tolerance)
    statement = select(Task).where(
        Task.parent_task_id == parent_task_id,
        Task.is_recurring_instance == True,
        Task.due_date >= due_date.replace(second=0, microsecond=0),
        Task.due_date < due_date.replace(second=59, microsecond=999999)
    )
    return session.exec(statement).first() is not None


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Recurring Task Service starting up")
    logger.info(f"Database URL: {DATABASE_URL}")
    logger.info("Waiting for Dapr Cron Binding triggers...")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Recurring Task Service shutting down")


if __name__ == "__main__":
    import uvicorn

    # Run the service
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
