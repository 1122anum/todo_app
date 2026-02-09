"""
TagService for managing task tags.

Handles tag creation, autocomplete, and usage tracking.
"""
from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select, func
from ..models.tag import Tag


class TagService:
    """Service for managing tags."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session

    def get_or_create_tag(
        self,
        user_id: int,
        name: str,
        color: Optional[str] = None
    ) -> Tag:
        """
        Get existing tag or create new one.

        Tags are automatically created when first used on a task.

        Args:
            user_id: Owner of the tag
            name: Tag name (will be normalized)
            color: Hex color code (optional)

        Returns:
            Tag (existing or newly created)

        Raises:
            ValueError: If tag name is invalid
        """
        # Normalize tag name (lowercase, strip whitespace)
        normalized_name = name.strip().lower()

        if not normalized_name:
            raise ValueError("Tag name cannot be empty")

        if len(normalized_name) > 50:
            raise ValueError("Tag name cannot exceed 50 characters")

        # Check if tag already exists
        statement = select(Tag).where(
            Tag.user_id == user_id,
            Tag.name == normalized_name
        )
        existing_tag = self.session.exec(statement).first()

        if existing_tag:
            return existing_tag

        # Create new tag
        tag = Tag(
            user_id=user_id,
            name=normalized_name,
            color=color,
            usage_count=0
        )

        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)

        return tag

    def get_tag(self, tag_id: int, user_id: int) -> Optional[Tag]:
        """Get a tag by ID."""
        statement = select(Tag).where(
            Tag.id == tag_id,
            Tag.user_id == user_id
        )
        return self.session.exec(statement).first()

    def get_tag_by_name(self, user_id: int, name: str) -> Optional[Tag]:
        """Get a tag by name."""
        normalized_name = name.strip().lower()
        statement = select(Tag).where(
            Tag.user_id == user_id,
            Tag.name == normalized_name
        )
        return self.session.exec(statement).first()

    def list_tags(
        self,
        user_id: int,
        min_usage: int = 0,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tag]:
        """
        List tags for a user.

        Args:
            user_id: Owner ID
            min_usage: Minimum usage count (default: 0)
            limit: Maximum number of tags to return
            offset: Number of tags to skip

        Returns:
            List of tags ordered by usage count (descending)
        """
        statement = select(Tag).where(
            Tag.user_id == user_id,
            Tag.usage_count >= min_usage
        ).order_by(Tag.usage_count.desc()).limit(limit).offset(offset)

        return list(self.session.exec(statement).all())

    def search_tags(
        self,
        user_id: int,
        query: str,
        limit: int = 10
    ) -> List[Tag]:
        """
        Search tags by name (for autocomplete).

        Args:
            user_id: Owner ID
            query: Search query (partial tag name)
            limit: Maximum number of results

        Returns:
            List of matching tags ordered by usage count
        """
        normalized_query = query.strip().lower()

        if not normalized_query:
            # Return most used tags if no query
            return self.list_tags(user_id, limit=limit)

        # Search for tags that start with or contain the query
        statement = select(Tag).where(
            Tag.user_id == user_id,
            Tag.name.like(f"%{normalized_query}%")
        ).order_by(Tag.usage_count.desc()).limit(limit)

        return list(self.session.exec(statement).all())

    def update_tag(
        self,
        tag_id: int,
        user_id: int,
        **updates
    ) -> Optional[Tag]:
        """
        Update a tag.

        Args:
            tag_id: Tag ID
            user_id: Owner ID (for authorization)
            **updates: Fields to update (name, color)

        Returns:
            Updated tag or None if not found
        """
        tag = self.get_tag(tag_id, user_id)
        if not tag:
            return None

        # Don't allow updating usage_count manually
        if 'usage_count' in updates:
            del updates['usage_count']

        for key, value in updates.items():
            if hasattr(tag, key) and key not in ['id', 'user_id', 'created_at']:
                if key == 'name':
                    # Normalize name
                    value = value.strip().lower()
                setattr(tag, key, value)

        tag.updated_at = datetime.utcnow()
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)

        return tag

    def delete_tag(self, tag_id: int, user_id: int) -> bool:
        """
        Delete a tag.

        Only tags with usage_count=0 can be deleted.

        Args:
            tag_id: Tag ID
            user_id: Owner ID (for authorization)

        Returns:
            True if deleted, False if not found or still in use

        Raises:
            ValueError: If tag is still in use
        """
        tag = self.get_tag(tag_id, user_id)
        if not tag:
            return False

        if tag.usage_count > 0:
            raise ValueError(f"Cannot delete tag '{tag.name}' - still used by {tag.usage_count} task(s)")

        self.session.delete(tag)
        self.session.commit()
        return True

    def increment_usage(self, user_id: int, tag_name: str) -> None:
        """
        Increment usage count for a tag.

        Called when a tag is added to a task.

        Args:
            user_id: Owner ID
            tag_name: Tag name
        """
        tag = self.get_tag_by_name(user_id, tag_name)
        if tag:
            tag.usage_count += 1
            tag.updated_at = datetime.utcnow()
            self.session.add(tag)
            self.session.commit()

    def decrement_usage(self, user_id: int, tag_name: str) -> None:
        """
        Decrement usage count for a tag.

        Called when a tag is removed from a task.

        Args:
            user_id: Owner ID
            tag_name: Tag name
        """
        tag = self.get_tag_by_name(user_id, tag_name)
        if tag and tag.usage_count > 0:
            tag.usage_count -= 1
            tag.updated_at = datetime.utcnow()
            self.session.add(tag)
            self.session.commit()

    def get_popular_tags(self, user_id: int, limit: int = 10) -> List[Tag]:
        """
        Get most popular tags for a user.

        Args:
            user_id: Owner ID
            limit: Maximum number of tags

        Returns:
            List of tags ordered by usage count
        """
        return self.list_tags(user_id, min_usage=1, limit=limit)

    def get_unused_tags(self, user_id: int) -> List[Tag]:
        """
        Get tags with zero usage count.

        These tags can be safely deleted.

        Args:
            user_id: Owner ID

        Returns:
            List of unused tags
        """
        statement = select(Tag).where(
            Tag.user_id == user_id,
            Tag.usage_count == 0
        ).order_by(Tag.created_at.desc())

        return list(self.session.exec(statement).all())

    def cleanup_unused_tags(self, user_id: int) -> int:
        """
        Delete all unused tags for a user.

        Args:
            user_id: Owner ID

        Returns:
            Number of tags deleted
        """
        unused_tags = self.get_unused_tags(user_id)
        count = 0

        for tag in unused_tags:
            self.session.delete(tag)
            count += 1

        self.session.commit()
        return count
