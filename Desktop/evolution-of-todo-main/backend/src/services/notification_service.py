"""
Notification Service - Microservice for checking and triggering reminders.

This service runs as a separate FastAPI application with Dapr sidecar.
It listens to Dapr Cron Binding (every minute) and triggers reminders
that are due.
"""
from fastapi import FastAPI, Request, HTTPException
from sqlmodel import Session, create_engine, select
from datetime import datetime
from typing import List
import logging
import os

from ..models.reminder import Reminder, ReminderStatus
from ..models.todo import Task
from .reminder_service import ReminderService
from .dapr_event_publisher import DaprEventPublisher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Notification Service",
    description="Microservice for checking and triggering reminders",
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
        "service": "notification-service",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/cron")
async def handle_cron_trigger(request: Request):
    """
    Handle Dapr Cron Binding trigger.

    This endpoint is called every minute by Dapr Cron Binding.
    It checks for due reminders and triggers notifications.

    Dapr Cron Binding configuration:
    - Component: reminders-cron (k8s/dapr-components/cron-binding.yaml)
    - Schedule: */1 * * * * (every minute)
    - Direction: input
    """
    try:
        logger.info("Cron trigger received - checking for due reminders")

        # Get current time
        current_time = datetime.utcnow()

        # Check and trigger reminders
        triggered_count = await check_and_trigger_reminders(current_time)

        logger.info(f"Reminder check complete: {triggered_count} reminders triggered")

        return {
            "status": "success",
            "triggered_count": triggered_count,
            "timestamp": current_time.isoformat()
        }

    except Exception as e:
        logger.error(f"Error in cron handler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def check_and_trigger_reminders(current_time: datetime) -> int:
    """
    Check for due reminders and trigger notifications.

    Args:
        current_time: Current timestamp

    Returns:
        Number of reminders triggered
    """
    triggered_count = 0

    with Session(engine) as session:
        # Get reminder service
        reminder_service = ReminderService(session)

        # Get all due reminders
        due_reminders = reminder_service.get_due_reminders(current_time)

        logger.info(f"Found {len(due_reminders)} due reminders")

        for reminder in due_reminders:
            try:
                # Get associated task
                task = get_task(session, reminder.task_id)

                if not task:
                    logger.warning(f"Task {reminder.task_id} not found for reminder {reminder.id}")
                    # Cancel reminder if task doesn't exist
                    reminder_service.cancel_reminder(reminder.id, reminder.user_id)
                    continue

                # Skip if task is already completed
                if task.completed:
                    logger.info(f"Task {task.id} already completed, cancelling reminder {reminder.id}")
                    reminder_service.cancel_reminder(reminder.id, reminder.user_id)
                    continue

                # Build reminder message
                message = build_reminder_message(task, reminder)

                # Publish reminder.triggered event
                await publish_reminder_triggered(reminder, task, message)

                # Publish to task-updates for real-time sync
                await publish_reminder_sync(reminder, task, message)

                # Mark reminder as sent
                reminder_service.mark_sent(reminder.id)

                logger.info(f"Triggered reminder {reminder.id} for task {task.id}")
                triggered_count += 1

            except Exception as e:
                logger.error(f"Error triggering reminder {reminder.id}: {str(e)}", exc_info=True)
                # Continue with next reminder
                continue

    return triggered_count


def get_task(session: Session, task_id: int) -> Task:
    """
    Get a task by ID.

    Args:
        session: Database session
        task_id: Task ID

    Returns:
        Task or None
    """
    statement = select(Task).where(Task.id == task_id)
    return session.exec(statement).first()


def build_reminder_message(task: Task, reminder: Reminder) -> str:
    """
    Build reminder notification message.

    Args:
        task: Task
        reminder: Reminder

    Returns:
        Reminder message
    """
    if task.due_date:
        time_until_due = task.due_date - datetime.utcnow()
        hours = int(time_until_due.total_seconds() / 3600)
        minutes = int((time_until_due.total_seconds() % 3600) / 60)

        if hours > 0:
            time_str = f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"

        return f"Reminder: {task.title} is due in {time_str}"
    else:
        return f"Reminder: {task.title}"


async def publish_reminder_triggered(reminder: Reminder, task: Task, message: str) -> bool:
    """
    Publish reminder.triggered event to reminders topic.

    Args:
        reminder: Reminder
        task: Task
        message: Reminder message

    Returns:
        True if published successfully
    """
    import uuid

    event = {
        "schema_version": "1.0",
        "event_id": str(uuid.uuid4()),
        "event_type": "reminder.triggered",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_id": reminder.user_id,
        "reminder": {
            "id": reminder.id,
            "task_id": reminder.task_id,
            "task_title": task.title,
            "scheduled_time": reminder.scheduled_time.isoformat() + "Z",
            "notification_channel": reminder.notification_channel.value,
            "message": message,
            "snoozed_until": None
        },
        "task": {
            "id": task.id,
            "title": task.title,
            "due_date": task.due_date.isoformat() + "Z" if task.due_date else None,
            "priority": task.priority.value,
            "completed": task.completed
        },
        "metadata": {
            "source": "notification_service",
            "correlation_id": str(uuid.uuid4()),
            "trigger_reason": "scheduled"
        }
    }

    url = f"http://localhost:3500/v1.0/publish/pubsub/reminders"

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=event, timeout=5.0)
            response.raise_for_status()

        logger.info(f"Published reminder.triggered event: {event['event_id']}")
        return True

    except Exception as e:
        logger.error(f"Failed to publish reminder event: {str(e)}", exc_info=True)
        return False


async def publish_reminder_sync(reminder: Reminder, task: Task, message: str) -> bool:
    """
    Publish reminder to task-updates topic for real-time sync.

    Args:
        reminder: Reminder
        task: Task
        message: Reminder message

    Returns:
        True if published successfully
    """
    import uuid

    event = {
        "schema_version": "1.0",
        "event_id": str(uuid.uuid4()),
        "event_type": "reminder.triggered",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_id": reminder.user_id,
        "task": {
            "id": task.id,
            "title": task.title,
            "due_date": task.due_date.isoformat() + "Z" if task.due_date else None
        },
        "changes": None,
        "reminder": {
            "id": reminder.id,
            "task_id": reminder.task_id,
            "message": message,
            "scheduled_time": reminder.scheduled_time.isoformat() + "Z"
        },
        "metadata": {
            "source": "notification_service",
            "correlation_id": str(uuid.uuid4()),
            "device_id": None,
            "sync_priority": "high"
        }
    }

    url = f"http://localhost:3500/v1.0/publish/pubsub/task-updates"

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=event, timeout=5.0)
            response.raise_for_status()

        logger.info(f"Published reminder sync event: {event['event_id']}")
        return True

    except Exception as e:
        logger.error(f"Failed to publish reminder sync: {str(e)}", exc_info=True)
        return False


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Notification Service starting up")
    logger.info(f"Database URL: {DATABASE_URL}")
    logger.info("Waiting for Dapr Cron Binding triggers...")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Notification Service shutting down")


if __name__ == "__main__":
    import uvicorn

    # Run the service
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
