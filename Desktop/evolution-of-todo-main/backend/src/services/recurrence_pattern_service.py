"""
RecurrencePatternService for managing recurring task patterns.

Handles creation, updates, and calculation of next occurrence dates.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import Session, select
from backend.src.models.recurrence_pattern import RecurrencePattern, RecurrenceFrequency


class RecurrencePatternService:
    """Service for managing recurrence patterns."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session

    def create_pattern(
        self,
        user_id: int,
        frequency: RecurrenceFrequency,
        interval: int,
        start_date: datetime,
        days_of_week: Optional[List[int]] = None,
        day_of_month: Optional[int] = None,
        end_date: Optional[datetime] = None,
    ) -> RecurrencePattern:
        """
        Create a new recurrence pattern.

        Args:
            user_id: Owner of the pattern
            frequency: Recurrence frequency (daily, weekly, monthly, custom)
            interval: Repeat every N units
            start_date: When to start generating instances
            days_of_week: Days of week for weekly patterns (0=Sunday, 6=Saturday)
            day_of_month: Day of month for monthly patterns (1-31)
            end_date: When to stop generating instances (optional)

        Returns:
            Created RecurrencePattern

        Raises:
            ValueError: If validation fails
        """
        # Validate pattern
        self._validate_pattern(frequency, interval, days_of_week, day_of_month, start_date, end_date)

        pattern = RecurrencePattern(
            user_id=user_id,
            frequency=frequency,
            interval=interval,
            days_of_week=days_of_week,
            day_of_month=day_of_month,
            start_date=start_date,
            end_date=end_date,
            last_generated_at=None,
        )

        self.session.add(pattern)
        self.session.commit()
        self.session.refresh(pattern)

        return pattern

    def get_pattern(self, pattern_id: int, user_id: int) -> Optional[RecurrencePattern]:
        """Get a recurrence pattern by ID."""
        statement = select(RecurrencePattern).where(
            RecurrencePattern.id == pattern_id,
            RecurrencePattern.user_id == user_id
        )
        return self.session.exec(statement).first()

    def update_pattern(
        self,
        pattern_id: int,
        user_id: int,
        **updates
    ) -> Optional[RecurrencePattern]:
        """
        Update a recurrence pattern.

        Args:
            pattern_id: Pattern ID
            user_id: Owner ID (for authorization)
            **updates: Fields to update

        Returns:
            Updated pattern or None if not found
        """
        pattern = self.get_pattern(pattern_id, user_id)
        if not pattern:
            return None

        for key, value in updates.items():
            if hasattr(pattern, key):
                setattr(pattern, key, value)

        pattern.updated_at = datetime.utcnow()
        self.session.add(pattern)
        self.session.commit()
        self.session.refresh(pattern)

        return pattern

    def delete_pattern(self, pattern_id: int, user_id: int) -> bool:
        """
        Delete a recurrence pattern.

        Args:
            pattern_id: Pattern ID
            user_id: Owner ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        pattern = self.get_pattern(pattern_id, user_id)
        if not pattern:
            return False

        self.session.delete(pattern)
        self.session.commit()
        return True

    def get_due_patterns(self, current_time: Optional[datetime] = None) -> List[RecurrencePattern]:
        """
        Get patterns that are due for instance generation.

        A pattern is due if:
        - start_date <= current_time
        - end_date is None or end_date > current_time
        - last_generated_at is None or next occurrence is due

        Args:
            current_time: Current time (defaults to now)

        Returns:
            List of patterns due for generation
        """
        if current_time is None:
            current_time = datetime.utcnow()

        statement = select(RecurrencePattern).where(
            RecurrencePattern.start_date <= current_time,
            (RecurrencePattern.end_date.is_(None)) | (RecurrencePattern.end_date > current_time)
        )

        patterns = self.session.exec(statement).all()

        # Filter patterns where next occurrence is due
        due_patterns = []
        for pattern in patterns:
            next_occurrence = self.calculate_next_occurrence(pattern, current_time)
            if next_occurrence and next_occurrence <= current_time:
                due_patterns.append(pattern)

        return due_patterns

    def calculate_next_occurrence(
        self,
        pattern: RecurrencePattern,
        from_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        Calculate the next occurrence date for a pattern.

        Args:
            pattern: Recurrence pattern
            from_time: Calculate from this time (defaults to last_generated_at or start_date)

        Returns:
            Next occurrence datetime or None if pattern has ended
        """
        if from_time is None:
            from_time = pattern.last_generated_at or pattern.start_date

        # Check if pattern has ended
        if pattern.end_date and from_time >= pattern.end_date:
            return None

        if pattern.frequency == RecurrenceFrequency.DAILY:
            next_date = from_time + timedelta(days=pattern.interval)

        elif pattern.frequency == RecurrenceFrequency.WEEKLY:
            # Find next occurrence on specified days of week
            next_date = self._calculate_next_weekly(from_time, pattern.interval, pattern.days_of_week)

        elif pattern.frequency == RecurrenceFrequency.MONTHLY:
            # Add months to the date
            next_date = self._calculate_next_monthly(from_time, pattern.interval, pattern.day_of_month)

        else:  # CUSTOM
            # Custom patterns not implemented in Phase V
            return None

        # Ensure next_date doesn't exceed end_date
        if pattern.end_date and next_date > pattern.end_date:
            return None

        return next_date

    def mark_generated(self, pattern_id: int, generated_at: Optional[datetime] = None) -> None:
        """
        Mark a pattern as having generated an instance.

        Args:
            pattern_id: Pattern ID
            generated_at: Generation timestamp (defaults to now)
        """
        if generated_at is None:
            generated_at = datetime.utcnow()

        statement = select(RecurrencePattern).where(RecurrencePattern.id == pattern_id)
        pattern = self.session.exec(statement).first()

        if pattern:
            pattern.last_generated_at = generated_at
            pattern.updated_at = datetime.utcnow()
            self.session.add(pattern)
            self.session.commit()

    def _validate_pattern(
        self,
        frequency: RecurrenceFrequency,
        interval: int,
        days_of_week: Optional[List[int]],
        day_of_month: Optional[int],
        start_date: datetime,
        end_date: Optional[datetime],
    ) -> None:
        """Validate recurrence pattern parameters."""
        if interval < 1:
            raise ValueError("Interval must be >= 1")

        if frequency == RecurrenceFrequency.WEEKLY:
            if not days_of_week or len(days_of_week) == 0:
                raise ValueError("Weekly patterns must specify days_of_week")
            if not all(0 <= day <= 6 for day in days_of_week):
                raise ValueError("days_of_week must be 0-6 (Sunday-Saturday)")

        if frequency == RecurrenceFrequency.MONTHLY:
            if not day_of_month:
                raise ValueError("Monthly patterns must specify day_of_month")
            if not 1 <= day_of_month <= 31:
                raise ValueError("day_of_month must be 1-31")

        if end_date and end_date <= start_date:
            raise ValueError("end_date must be after start_date")

    def _calculate_next_weekly(
        self,
        from_time: datetime,
        interval: int,
        days_of_week: List[int]
    ) -> datetime:
        """Calculate next weekly occurrence."""
        current_weekday = from_time.weekday()
        # Convert Monday=0 to Sunday=0 format
        current_weekday = (current_weekday + 1) % 7

        # Sort days of week
        sorted_days = sorted(days_of_week)

        # Find next day in current week
        next_day = None
        for day in sorted_days:
            if day > current_weekday:
                next_day = day
                break

        if next_day is not None:
            # Next occurrence is in current week
            days_ahead = next_day - current_weekday
            return from_time + timedelta(days=days_ahead)
        else:
            # Next occurrence is in next interval week
            days_ahead = (7 * interval) - current_weekday + sorted_days[0]
            return from_time + timedelta(days=days_ahead)

    def _calculate_next_monthly(
        self,
        from_time: datetime,
        interval: int,
        day_of_month: int
    ) -> datetime:
        """Calculate next monthly occurrence."""
        # Add interval months
        month = from_time.month + interval
        year = from_time.year

        while month > 12:
            month -= 12
            year += 1

        # Handle day overflow (e.g., Feb 31 -> Feb 28/29)
        try:
            next_date = from_time.replace(year=year, month=month, day=day_of_month)
        except ValueError:
            # Day doesn't exist in target month, use last day of month
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year

            # Get last day of target month
            last_day = (datetime(next_year, next_month, 1) - timedelta(days=1)).day
            next_date = from_time.replace(year=year, month=month, day=min(day_of_month, last_day))

        return next_date
