"""
Todo routes for CRUD operations with Phase V features.

Supports recurring tasks, priorities, tags, reminders, and event-driven architecture.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlmodel import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..database import get_session
from ..models.todo import Task, TaskPriority
from ..models.reminder import Reminder, ReminderStatus
from ..models.user import User
from ..middleware.auth import get_current_user
from ..services.todo_service import TodoService
from ..services.reminder_service import ReminderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/todos", tags=["todos"])


# Request/Response Models

class RecurrencePatternCreate(BaseModel):
    """Recurrence pattern configuration."""
    frequency: str  # daily, weekly, monthly
    interval: int = 1
    days_of_week: Optional[List[int]] = None  # For weekly: 0=Sunday, 6=Saturday
    day_of_month: Optional[int] = None  # For monthly: 1-31
    start_date: datetime
    end_date: Optional[datetime] = None


class TaskCreate(BaseModel):
    """Task creation request."""
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    recurrence_pattern: Optional[Dict[str, Any]] = None


class TaskUpdate(BaseModel):
    """Task update request."""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None


class TaskResponse(BaseModel):
    """Task response."""
    id: int
    user_id: int
    title: str
    description: Optional[str]
    completed: bool
    priority: str
    due_date: Optional[datetime]
    tags: List[str]
    recurrence_pattern_id: Optional[int]
    is_recurring_instance: bool
    parent_task_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Endpoints

@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    completed: Optional[bool] = None,
    priority: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get all tasks for the current user with optional filters.

    Args:
        completed: Filter by completion status
        priority: Filter by priority (high, medium, low)
        tags: Comma-separated list of tags to filter by
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        session: Database session
        current_user: Authenticated user

    Returns:
        List of tasks
    """
    try:
        service = TodoService(session)

        # Parse filters
        priority_enum = TaskPriority(priority) if priority else None
        tag_list = tags.split(',') if tags else None

        tasks = service.list_tasks(
            user_id=current_user.user_id,
            completed=completed,
            priority=priority_enum,
            tags=tag_list,
            limit=limit,
            offset=offset
        )

        return tasks

    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tasks"
        )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new task for the current user.

    Supports recurring tasks with recurrence patterns.

    Args:
        task: Task creation data
        session: Database session
        current_user: Authenticated user

    Returns:
        Created task
    """
    try:
        service = TodoService(session)

        # Parse priority
        priority = TaskPriority(task.priority) if task.priority else TaskPriority.MEDIUM

        new_task = service.create_task(
            user_id=current_user.user_id,
            title=task.title,
            description=task.description,
            priority=priority,
            due_date=task.due_date,
            tags=task.tags,
            recurrence_pattern=task.recurrence_pattern
        )

        logger.info(f"Task created: {new_task.id} for user {current_user.user_id}")
        return new_task

    except ValueError as e:
        logger.warning(f"Validation error creating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific task by ID.

    Args:
        task_id: Task ID
        session: Database session
        current_user: Authenticated user

    Returns:
        Task

    Raises:
        HTTPException: 404 if task not found or doesn't belong to user
    """
    try:
        service = TodoService(session)
        task = service.get_task(task_id, current_user.user_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch task"
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update a task.

    Args:
        task_id: Task ID
        task_update: Task update data
        session: Database session
        current_user: Authenticated user

    Returns:
        Updated task

    Raises:
        HTTPException: 404 if task not found or doesn't belong to user
    """
    try:
        service = TodoService(session)

        # Build updates dict
        updates = {}
        if task_update.title is not None:
            updates['title'] = task_update.title
        if task_update.description is not None:
            updates['description'] = task_update.description
        if task_update.completed is not None:
            updates['completed'] = task_update.completed
        if task_update.priority is not None:
            updates['priority'] = TaskPriority(task_update.priority)
        if task_update.due_date is not None:
            updates['due_date'] = task_update.due_date
        if task_update.tags is not None:
            updates['tags'] = task_update.tags

        task = service.update_task(task_id, current_user.user_id, **updates)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        logger.info(f"Task updated: {task.id}")
        return task

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error updating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task"
        )


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a task as completed.

    Args:
        task_id: Task ID
        session: Database session
        current_user: Authenticated user

    Returns:
        Updated task
    """
    try:
        service = TodoService(session)
        task = service.complete_task(task_id, current_user.user_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        logger.info(f"Task completed: {task.id}")
        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete task"
        )


@router.post("/{task_id}/uncomplete", response_model=TaskResponse)
async def uncomplete_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a task as not completed.

    Args:
        task_id: Task ID
        session: Database session
        current_user: Authenticated user

    Returns:
        Updated task
    """
    try:
        service = TodoService(session)
        task = service.uncomplete_task(task_id, current_user.user_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        logger.info(f"Task uncompleted: {task.id}")
        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uncompleting task: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to uncomplete task"
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a task.

    If task is a recurring parent, deletes all future instances.

    Args:
        task_id: Task ID
        session: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: 404 if task not found or doesn't belong to user
    """
    try:
        service = TodoService(session)
        deleted = service.delete_task(task_id, current_user.user_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        logger.info(f"Task deleted: {task_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task"
        )


# Reminder Endpoints

class ReminderCreate(BaseModel):
    """Reminder creation request."""
    scheduled_time: datetime
    notification_channel: str = "in_app"


class ReminderResponse(BaseModel):
    """Reminder response."""
    id: int
    task_id: int
    user_id: int
    scheduled_time: datetime
    notification_channel: str
    status: str
    snoozed_until: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/{task_id}/reminders", response_model=List[ReminderResponse])
async def get_task_reminders(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get all reminders for a task.

    Args:
        task_id: Task ID
        session: Database session
        current_user: Authenticated user

    Returns:
        List of reminders
    """
    try:
        reminder_service = ReminderService(session)
        reminders = reminder_service.list_reminders(
            user_id=current_user.user_id,
            task_id=task_id
        )
        return reminders

    except Exception as e:
        logger.error(f"Error fetching reminders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reminders"
        )


@router.post("/{task_id}/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_task_reminder(
    task_id: int,
    reminder: ReminderCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a reminder for a task.

    Args:
        task_id: Task ID
        reminder: Reminder creation data
        session: Database session
        current_user: Authenticated user

    Returns:
        Created reminder
    """
    try:
        # Verify task exists and belongs to user
        todo_service = TodoService(session)
        task = todo_service.get_task(task_id, current_user.user_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        # Create reminder
        reminder_service = ReminderService(session)
        new_reminder = reminder_service.create_reminder(
            task_id=task_id,
            user_id=current_user.user_id,
            scheduled_time=reminder.scheduled_time
        )

        logger.info(f"Reminder created: {new_reminder.id} for task {task_id}")
        return new_reminder

    except ValueError as e:
        logger.warning(f"Validation error creating reminder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating reminder: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reminder"
        )


@router.post("/{task_id}/reminders/{reminder_id}/snooze", response_model=ReminderResponse)
async def snooze_reminder(
    task_id: int,
    reminder_id: int,
    snooze_minutes: int = 10,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Snooze a reminder.

    Args:
        task_id: Task ID
        reminder_id: Reminder ID
        snooze_minutes: Minutes to snooze (default: 10)
        session: Database session
        current_user: Authenticated user

    Returns:
        Updated reminder
    """
    try:
        reminder_service = ReminderService(session)
        reminder = reminder_service.snooze_reminder(
            reminder_id,
            current_user.user_id,
            snooze_minutes
        )

        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )

        logger.info(f"Reminder snoozed: {reminder_id} for {snooze_minutes} minutes")
        return reminder

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error snoozing reminder: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to snooze reminder"
        )


@router.delete("/{task_id}/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    task_id: int,
    reminder_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a reminder.

    Args:
        task_id: Task ID
        reminder_id: Reminder ID
        session: Database session
        current_user: Authenticated user
    """
    try:
        reminder_service = ReminderService(session)
        deleted = reminder_service.delete_reminder(reminder_id, current_user.user_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )

        logger.info(f"Reminder deleted: {reminder_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reminder: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete reminder"
        )


# Backward compatibility aliases
TodoCreate = TaskCreate
TodoUpdate = TaskUpdate
TodoResponse = TaskResponse

