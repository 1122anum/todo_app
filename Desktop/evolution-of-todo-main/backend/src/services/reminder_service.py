"""
ReminderService for managing task reminders.

Handles creation, updates, and querying of reminders for tasks.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import Session, select
from ..models.reminder import Reminder, ReminderStatus, NotificationChannel


class ReminderService:
    """Service for managing reminders."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session

    def create_reminder(
        self,
        task_id: int,
        user_id: int,
        scheduled_time: datetime,
        notification_channel: NotificationChannel = NotificationChannel.IN_APP,
    ) -> Reminder:
        """
        Create a new reminder for a task.

        Args:
            task_id: Task ID
            user_id: Owner of the reminder
            scheduled_time: When to send the reminder
            notification_channel: Notification channel (default: in_app)

        Returns:
            Created Reminder

        Raises:
            ValueError: If validation fails
        """
        # Validate scheduled time is in the future
        if scheduled_time <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")

        reminder = Reminder(
            task_id=task_id,
            user_id=user_id,
            scheduled_time=scheduled_time,
            notification_channel=notification_channel,
            status=ReminderStatus.PENDING,
        )

        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)

        return reminder

    def create_reminder_for_due_date(
        self,
        task_id: int,
        user_id: int,
        due_date: datetime,
        advance_minutes: int = 60,
    ) -> Optional[Reminder]:
        """
        Create a reminder for a task's due date.

        Reminder is scheduled N minutes before the due date.

        Args:
            task_id: Task ID
            user_id: Owner of the reminder
            due_date: Task due date
            advance_minutes: Minutes before due date to remind (default: 60)

        Returns:
            Created Reminder or None if due date is too soon
        """
        scheduled_time = due_date - timedelta(minutes=advance_minutes)

        # Don't create reminder if scheduled time is in the past
        if scheduled_time <= datetime.utcnow():
            return None

        return self.create_reminder(task_id, user_id, scheduled_time)

    def get_reminder(self, reminder_id: int, user_id: int) -> Optional[Reminder]:
        """Get a reminder by ID."""
        statement = select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id
        )
        return self.session.exec(statement).first()

    def list_reminders(
        self,
        user_id: int,
        task_id: Optional[int] = None,
        status: Optional[ReminderStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Reminder]:
        """
        List reminders for a user with optional filters.

        Args:
            user_id: Owner ID
            task_id: Filter by task ID (optional)
            status: Filter by status (optional)
            limit: Maximum number of reminders to return
            offset: Number of reminders to skip

        Returns:
            List of reminders
        """
        statement = select(Reminder).where(Reminder.user_id == user_id)

        if task_id is not None:
            statement = statement.where(Reminder.task_id == task_id)

        if status is not None:
            statement = statement.where(Reminder.status == status)

        statement = statement.order_by(Reminder.scheduled_time.asc()).limit(limit).offset(offset)

        return list(self.session.exec(statement).all())

    def get_due_reminders(self, current_time: Optional[datetime] = None) -> List[Reminder]:
        """
        Get reminders that are due for notification.

        A reminder is due if:
        - status is 'pending' or 'snoozed'
        - scheduled_time <= current_time (for pending)
        - snoozed_until <= current_time (for snoozed)

        Args:
            current_time: Current time (defaults to now)

        Returns:
            List of due reminders
        """
        if current_time is None:
            current_time = datetime.utcnow()

        # Get pending reminders that are due
        pending_statement = select(Reminder).where(
            Reminder.status == ReminderStatus.PENDING,
            Reminder.scheduled_time <= current_time
        )
        pending_reminders = list(self.session.exec(pending_statement).all())

        # Get snoozed reminders that are due
        snoozed_statement = select(Reminder).where(
            Reminder.status == ReminderStatus.SNOOZED,
            Reminder.snoozed_until <= current_time
        )
        snoozed_reminders = list(self.session.exec(snoozed_statement).all())

        return pending_reminders + snoozed_reminders

    def update_reminder(
        self,
        reminder_id: int,
        user_id: int,
        **updates
    ) -> Optional[Reminder]:
        """
        Update a reminder.

        Args:
            reminder_id: Reminder ID
            user_id: Owner ID (for authorization)
            **updates: Fields to update

        Returns:
            Updated reminder or None if not found
        """
        reminder = self.get_reminder(reminder_id, user_id)
        if not reminder:
            return None

        for key, value in updates.items():
            if hasattr(reminder, key) and key not in ['id', 'user_id', 'created_at']:
                setattr(reminder, key, value)

        reminder.updated_at = datetime.utcnow()
        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)

        return reminder

    def snooze_reminder(
        self,
        reminder_id: int,
        user_id: int,
        snooze_minutes: int = 10
    ) -> Optional[Reminder]:
        """
        Snooze a reminder for a specified duration.

        Args:
            reminder_id: Reminder ID
            user_id: Owner ID (for authorization)
            snooze_minutes: Minutes to snooze (default: 10)

        Returns:
            Updated reminder or None if not found
        """
        reminder = self.get_reminder(reminder_id, user_id)
        if not reminder:
            return None

        snoozed_until = datetime.utcnow() + timedelta(minutes=snooze_minutes)

        reminder.status = ReminderStatus.SNOOZED
        reminder.snoozed_until = snoozed_until
        reminder.updated_at = datetime.utcnow()

        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)

        return reminder

    def mark_sent(self, reminder_id: int) -> Optional[Reminder]:
        """
        Mark a reminder as sent.

        Args:
            reminder_id: Reminder ID

        Returns:
            Updated reminder or None if not found
        """
        statement = select(Reminder).where(Reminder.id == reminder_id)
        reminder = self.session.exec(statement).first()

        if not reminder:
            return None

        reminder.status = ReminderStatus.SENT
        reminder.sent_at = datetime.utcnow()
        reminder.updated_at = datetime.utcnow()

        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)

        return reminder

    def cancel_reminder(self, reminder_id: int, user_id: int) -> Optional[Reminder]:
        """
        Cancel a reminder.

        Args:
            reminder_id: Reminder ID
            user_id: Owner ID (for authorization)

        Returns:
            Updated reminder or None if not found
        """
        return self.update_reminder(
            reminder_id,
            user_id,
            status=ReminderStatus.CANCELLED
        )

    def delete_reminder(self, reminder_id: int, user_id: int) -> bool:
        """
        Delete a reminder.

        Args:
            reminder_id: Reminder ID
            user_id: Owner ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        reminder = self.get_reminder(reminder_id, user_id)
        if not reminder:
            return False

        self.session.delete(reminder)
        self.session.commit()
        return True

    def cancel_reminders_for_task(self, task_id: int, user_id: int) -> int:
        """
        Cancel all pending reminders for a task.

        Useful when a task is completed or deleted.

        Args:
            task_id: Task ID
            user_id: Owner ID (for authorization)

        Returns:
            Number of reminders cancelled
        """
        statement = select(Reminder).where(
            Reminder.task_id == task_id,
            Reminder.user_id == user_id,
            Reminder.status.in_([ReminderStatus.PENDING, ReminderStatus.SNOOZED])
        )
        reminders = self.session.exec(statement).all()

        count = 0
        for reminder in reminders:
            reminder.status = ReminderStatus.CANCELLED
            reminder.updated_at = datetime.utcnow()
            self.session.add(reminder)
            count += 1

        self.session.commit()
        return count
