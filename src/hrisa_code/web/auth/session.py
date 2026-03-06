"""Session management for maintaining authentication state."""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from hrisa_code.web.db.models import User, Session


class SessionManager:
    """Service for managing user sessions."""

    def __init__(self, session_expiry_days: int = 30):
        """Initialize session manager.

        Args:
            session_expiry_days: Session expiration time in days (default: 30)
        """
        self.session_expiry_days = session_expiry_days

    async def create_session(
        self,
        db_session: AsyncSession,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """Create a new session for a user.

        Args:
            db_session: Database session
            user: User to create session for
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Session token string
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)  # 43 chars, URL-safe

        # Create session record
        session = Session(
            token=token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=self.session_expiry_days),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db_session.add(session)
        await db_session.flush()

        return token

    async def get_user_from_token(
        self,
        db_session: AsyncSession,
        token: str,
    ) -> Optional[User]:
        """Validate session token and return the user.

        Updates last_accessed timestamp on successful validation.

        Args:
            db_session: Database session
            token: Session token

        Returns:
            User if token is valid, None otherwise
        """
        # Find non-expired session
        stmt = select(Session).where(
            and_(
                Session.token == token,
                Session.expires_at > datetime.utcnow(),
            )
        )

        result = await db_session.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return None

        # Update last accessed time
        session.last_accessed = datetime.utcnow()

        # Get user
        user_stmt = select(User).where(User.id == session.user_id)
        user_result = await db_session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        await db_session.flush()

        return user

    async def revoke_session(
        self,
        db_session: AsyncSession,
        token: str,
    ) -> bool:
        """Revoke a session (logout).

        Args:
            db_session: Database session
            token: Session token to revoke

        Returns:
            True if session was revoked, False if not found
        """
        stmt = select(Session).where(Session.token == token)
        result = await db_session.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return False

        await db_session.delete(session)
        await db_session.flush()

        return True

    async def revoke_all_user_sessions(
        self,
        db_session: AsyncSession,
        user_id: str,
    ) -> int:
        """Revoke all sessions for a user.

        Useful for security actions like password change or account compromise.

        Args:
            db_session: Database session
            user_id: User ID

        Returns:
            Number of sessions revoked
        """
        stmt = select(Session).where(Session.user_id == user_id)
        result = await db_session.execute(stmt)
        sessions = result.scalars().all()

        for session in sessions:
            await db_session.delete(session)

        await db_session.flush()

        return len(sessions)

    async def cleanup_expired_sessions(self, db_session: AsyncSession) -> int:
        """Delete expired sessions.

        Should be called periodically via cron job or scheduled task.

        Args:
            db_session: Database session

        Returns:
            Number of sessions deleted
        """
        stmt = select(Session).where(
            Session.expires_at <= datetime.utcnow()
        )
        result = await db_session.execute(stmt)
        sessions = result.scalars().all()

        for session in sessions:
            await db_session.delete(session)

        await db_session.flush()

        return len(sessions)

    async def get_user_sessions(
        self,
        db_session: AsyncSession,
        user_id: str,
    ) -> list[Session]:
        """Get all active sessions for a user.

        Useful for displaying active sessions in user profile.

        Args:
            db_session: Database session
            user_id: User ID

        Returns:
            List of active sessions
        """
        stmt = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.expires_at > datetime.utcnow(),
            )
        ).order_by(Session.last_accessed.desc())

        result = await db_session.execute(stmt)
        sessions = result.scalars().all()

        return list(sessions)
