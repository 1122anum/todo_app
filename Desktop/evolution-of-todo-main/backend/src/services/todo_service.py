"""
TodoService for managing tasks with event-driven architecture support.

Handles task CRUD operations, recurring tasks, and event publishing.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from backend.src.models.todo import Task, TaskPriority
from backend.src.models.recurrence_pattern import RecurrencePattern, RecurrenceFrequency
from backend.src.services.recurrence_pattern_service import RecurrencePatternService
import uuid


class TodoService:
    """Service for managing tasks."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.recurrence_service = RecurrencePatternService(session)

    def create_task(
        self,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        recurrence_pattern: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        Create a new task, optionally with recurrence pattern.

        Args:
            user_id: Owner of the task
            title: Task title
            description: Task description (optional)
            priority: Task priority (default: medium)
            due_date: When task is due (optional)
            tags: List of tag names (optional)
            recurrence_pattern: Recurrence pattern config (optional)
                {
                    "frequency": "daily|weekly|monthly",
                    "interval": 1,
                    "days_of_week": [0, 1, 2],  # For weekly
                    "day_of_month": 15,  # For monthly
                    "start_date": "2026-02-09T09:00:00Z",
                    "end_date": "2026-12-31T23:59:59Z"  # Optional
                }

        Returns:
            Created Task

        Raises:
            ValueError: If validation fails
        """
        # Create recurrence pattern if specified
        pattern_id = None
        if recurrence_pattern:
            pattern = self._create_recurrence_pattern(user_id, recurrence_pattern)
            pattern_id = pattern.id

        # Create task
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags or [],
            recurrence_pattern_id=pattern_id,
            is_recurring_instance=False,
            parent_task_id=None,
        )

        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)

        return task

    def create_recurring_instance(
        self,
        parent_task: Task,
        due_date: datetime,
    ) -> Task:
        """
        Create a recurring task instance from a parent task.

        Args:
            parent_task: Parent recurring task
            due_date: Due date for this instance

        Returns:
            Created task instance
        """
        instance = Task(
            user_id=parent_task.user_id,
            title=parent_task.title,
            description=parent_task.description,
            priority=parent_task.priority,
            due_date=due_date,
            tags=parent_task.tags,
            recurrence_pattern_id=None,
            is_recurring_instance=True,
            parent_task_id=parent_task.id,
        )

        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)

        return instance

    def get_task(self, task_id: int, user_id: int) -> Optional[Task]:
        """Get a task by ID."""
        statement = select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id
        )
        return self.session.exec(statement).first()

    def list_tasks(
        self,
        user_id: int,
        completed: Optional[bool] = None,
        priority: Optional[TaskPriority] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Task]:
        """
        List tasks for a user with optional filters.

        Args:
            user_id: Owner ID
            completed: Filter by completion status (optional)
            priority: Filter by priority (optional)
            tags: Filter by tags (optional)
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip

        Returns:
            List of tasks
        """
        statement = select(Task).where(Task.user_id == user_id)

        if completed is not None:
            statement = statement.where(Task.completed == completed)

        if priority is not None:
            statement = statement.where(Task.priority == priority)

        if tags:
            # Filter tasks that have all specified tags
            for tag in tags:
                statement = statement.where(Task.tags.contains([tag]))

        statement = statement.order_by(Task.created_at.desc()).limit(limit).offset(offset)

        return list(self.session.exec(statement).all())

    def update_task(
        self,
        task_id: int,
        user_id: int,
        **updates
    ) -> Optional[Task]:
        """
        Update a task.

        Args:
            task_id: Task ID
            user_id: Owner ID (for authorization)
            **updates: Fields to update

        Returns:
            Updated task or None if not found
        """
        task = self.get_task(task_id, user_id)
        if not task:
            return None

        for key, value in updates.items():
            if hasattr(task, key) and key not in ['id', 'user_id', 'created_at']:
                setattr(task, key, value)

        task.updated_at = datetime.utcnow()
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)

        return task

    def complete_task(self, task_id: int, user_id: int) -> Optional[Task]:
        """Mark a task as completed."""
        return self.update_task(task_id, user_id, completed=True)

    def uncomplete_task(self, task_id: int, user_id: int) -> Optional[Task]:
        """Mark a task as not completed."""
        return self.update_task(task_id, user_id, completed=False)

    def delete_task(self, task_id: int, user_id: int) -> bool:
        """
        Delete a task.

        If task is a recurring parent, deletes all future instances.

        Args:
            task_id: Task ID
            user_id: Owner ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        task = self.get_task(task_id, user_id)
        if not task:
            return False

        # If task has recurrence pattern, delete all future instances
        if task.recurrence_pattern_id:
            self._delete_future_instances(task_id)

            # Delete the recurrence pattern
            if task.recurrence_pattern_id:
                self.recurrence_service.delete_pattern(task.recurrence_pattern_id, user_id)

        self.session.delete(task)
        self.session.commit()
        return True

    def get_recurring_parent(self, task_id: int, user_id: int) -> Optional[Task]:
        """Get the parent task for a recurring instance."""
        task = self.get_task(task_id, user_id)
        if not task or not task.is_recurring_instance or not task.parent_task_id:
            return None

        return self.get_task(task.parent_task_id, user_id)

    def _create_recurrence_pattern(
        self,
        user_id: int,
        pattern_config: Dict[str, Any]
    ) -> RecurrencePattern:
        """Create a recurrence pattern from configuration."""
        frequency = RecurrenceFrequency(pattern_config["frequency"])
        interval = pattern_config.get("interval", 1)
        start_date = pattern_config.get("start_date")

        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        end_date = pattern_config.get("end_date")
        if end_date and isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        days_of_week = pattern_config.get("days_of_week")
        day_of_month = pattern_config.get("day_of_month")

        return self.recurrence_service.create_pattern(
            user_id=user_id,
            frequency=frequency,
            interval=interval,
            start_date=start_date,
            days_of_week=days_of_week,
            day_of_month=day_of_month,
            end_date=end_date,
        )

    def _delete_future_instances(self, parent_task_id: int) -> None:
        """Delete all future instances of a recurring task."""
        statement = select(Task).where(
            Task.parent_task_id == parent_task_id,
            Task.completed == False
        )
        instances = self.session.exec(statement).all()

        for instance in instances:
            self.session.delete(instance)

        self.session.commit()
