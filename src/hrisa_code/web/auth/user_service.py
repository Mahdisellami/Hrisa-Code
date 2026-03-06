"""User service for user management operations."""

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from hrisa_code.web.db.models import User


class UserService:
    """Service for managing users."""

    async def count_users(self, session: AsyncSession) -> int:
        """Count total number of users.

        Args:
            session: Database session

        Returns:
            Total user count
        """
        stmt = select(func.count()).select_from(User)
        result = await session.execute(stmt)
        count = result.scalar()
        return count or 0

    async def create_user(
        self,
        session: AsyncSession,
        email: str,
        role: Optional[str] = None,
    ) -> User:
        """Create a new user.

        If this is the first user in the system, they automatically become an admin.

        Args:
            session: Database session
            email: User email address
            role: User role (admin, user, viewer). If None, auto-assigned.

        Returns:
            Created User instance
        """
        # Check if this is the first user
        user_count = await self.count_users(session)
        is_first_user = user_count == 0

        # Auto-assign role
        if role is None:
            if is_first_user:
                role = "admin"
            else:
                role = "user"

        # Create user
        user = User(
            email=email.lower(),
            role=role,
            is_active=True,
        )

        session.add(user)
        await session.flush()

        return user

    async def get_user_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """Get user by email address.

        Args:
            session: Database session
            email: User email address

        Returns:
            User if found, None otherwise
        """
        stmt = select(User).where(User.email == email.lower())
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user

    async def get_user_by_id(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> Optional[User]:
        """Get user by ID.

        Args:
            session: Database session
            user_id: User UUID

        Returns:
            User if found, None otherwise
        """
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user

    async def list_users(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[User]:
        """List users with pagination.

        Args:
            session: Database session
            skip: Number of users to skip
            limit: Maximum number of users to return
            include_inactive: Whether to include inactive users

        Returns:
            List of users
        """
        stmt = select(User)

        if not include_inactive:
            stmt = stmt.where(User.is_active == True)

        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)

        result = await session.execute(stmt)
        users = result.scalars().all()

        return list(users)

    async def update_user_role(
        self,
        session: AsyncSession,
        user_id: UUID,
        new_role: str,
    ) -> Optional[User]:
        """Update a user's role.

        Args:
            session: Database session
            user_id: User UUID
            new_role: New role (admin, user, viewer)

        Returns:
            Updated User if found, None otherwise
        """
        if new_role not in ["admin", "user", "viewer"]:
            raise ValueError(f"Invalid role: {new_role}")

        user = await self.get_user_by_id(session, user_id)

        if not user:
            return None

        user.role = new_role
        await session.flush()

        return user

    async def deactivate_user(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> Optional[User]:
        """Deactivate a user account.

        Args:
            session: Database session
            user_id: User UUID

        Returns:
            Updated User if found, None otherwise
        """
        user = await self.get_user_by_id(session, user_id)

        if not user:
            return None

        user.is_active = False
        await session.flush()

        return user

    async def activate_user(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> Optional[User]:
        """Activate a user account.

        Args:
            session: Database session
            user_id: User UUID

        Returns:
            Updated User if found, None otherwise
        """
        user = await self.get_user_by_id(session, user_id)

        if not user:
            return None

        user.is_active = True
        await session.flush()

        return user

    async def get_or_create_user(
        self,
        session: AsyncSession,
        email: str,
    ) -> tuple[User, bool]:
        """Get existing user or create new one.

        Args:
            session: Database session
            email: User email address

        Returns:
            Tuple of (User, is_new) where is_new indicates if user was created
        """
        user = await self.get_user_by_email(session, email)

        if user:
            return user, False

        user = await self.create_user(session, email)
        return user, True
