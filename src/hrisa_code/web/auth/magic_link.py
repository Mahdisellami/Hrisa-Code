"""Magic link token generation and validation."""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from hrisa_code.web.db.models import User, MagicLinkToken


class MagicLinkService:
    """Service for managing magic link authentication."""

    def __init__(self, token_expiry_minutes: int = 15):
        """Initialize magic link service.

        Args:
            token_expiry_minutes: Token expiration time in minutes (default: 15)
        """
        self.token_expiry_minutes = token_expiry_minutes

    async def create_magic_link(
        self,
        session: AsyncSession,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """Create a magic link token for a user.

        Args:
            session: Database session
            user: User to create link for
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Magic link token string
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)  # 43 chars, URL-safe

        # Create token record
        magic_link = MagicLinkToken(
            token=token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(minutes=self.token_expiry_minutes),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        session.add(magic_link)
        await session.flush()

        return token

    async def verify_magic_link(
        self,
        session: AsyncSession,
        token: str,
        ip_address: Optional[str] = None,
    ) -> Optional[User]:
        """Verify a magic link token and return the user.

        Args:
            session: Database session
            token: Magic link token
            ip_address: Client IP address (for audit)

        Returns:
            User if token is valid, None otherwise
        """
        # Find token
        stmt = select(MagicLinkToken).where(
            and_(
                MagicLinkToken.token == token,
                MagicLinkToken.used == False,
                MagicLinkToken.expires_at > datetime.utcnow(),
            )
        )

        result = await session.execute(stmt)
        magic_link = result.scalar_one_or_none()

        if not magic_link:
            return None

        # Mark token as used
        magic_link.used = True
        magic_link.used_at = datetime.utcnow()

        # Get user
        user_stmt = select(User).where(User.id == magic_link.user_id)
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        # Update last login
        user.last_login = datetime.utcnow()

        await session.flush()

        return user

    async def cleanup_expired_tokens(self, session: AsyncSession) -> int:
        """Delete expired magic link tokens.

        Args:
            session: Database session

        Returns:
            Number of tokens deleted
        """
        stmt = select(MagicLinkToken).where(
            MagicLinkToken.expires_at <= datetime.utcnow()
        )
        result = await session.execute(stmt)
        tokens = result.scalars().all()

        for token in tokens:
            await session.delete(token)

        await session.flush()

        return len(tokens)
