"""Audit logging for security and compliance."""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from hrisa_code.web.db.models import AuditLog, User


class AuditLogger:
    """Service for logging user actions."""

    async def log(
        self,
        session: AsyncSession,
        action: str,
        user: Optional[User] = None,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log an action to the audit log.

        Args:
            session: Database session
            action: Action performed (e.g., "login", "logout", "agent.create")
            user: User who performed the action (optional)
            user_id: User ID if user object not available (optional)
            resource_type: Type of resource affected (e.g., "agent", "team")
            resource_id: ID of resource affected
            details: Additional details as JSON
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog instance
        """
        # Get user_id from user object if provided
        if user:
            user_id = user.id

        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        session.add(audit_entry)
        await session.flush()

        return audit_entry

    # Convenience methods for common actions

    async def log_login(
        self,
        session: AsyncSession,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a user login event.

        Args:
            session: Database session
            user: User who logged in
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog instance
        """
        return await self.log(
            session=session,
            action="auth.login",
            user=user,
            details={"method": "magic_link"},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_logout(
        self,
        session: AsyncSession,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a user logout event.

        Args:
            session: Database session
            user: User who logged out
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog instance
        """
        return await self.log(
            session=session,
            action="auth.logout",
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_magic_link_sent(
        self,
        session: AsyncSession,
        email: str,
        is_new_user: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a magic link send event.

        Args:
            session: Database session
            email: Email address magic link was sent to
            is_new_user: Whether this is a new user
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog instance
        """
        return await self.log(
            session=session,
            action="auth.magic_link_sent",
            details={"email": email, "is_new_user": is_new_user},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_user_role_update(
        self,
        session: AsyncSession,
        actor: User,
        target_user_id: UUID,
        old_role: str,
        new_role: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a user role update event.

        Args:
            session: Database session
            actor: User who performed the update (admin)
            target_user_id: User whose role was updated
            old_role: Previous role
            new_role: New role
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog instance
        """
        return await self.log(
            session=session,
            action="user.role_update",
            user=actor,
            resource_type="user",
            resource_id=str(target_user_id),
            details={"old_role": old_role, "new_role": new_role},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_user_deactivated(
        self,
        session: AsyncSession,
        actor: User,
        target_user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a user deactivation event.

        Args:
            session: Database session
            actor: User who performed the deactivation (admin)
            target_user_id: User who was deactivated
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog instance
        """
        return await self.log(
            session=session,
            action="user.deactivated",
            user=actor,
            resource_type="user",
            resource_id=str(target_user_id),
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_agent_created(
        self,
        session: AsyncSession,
        user: User,
        agent_id: UUID,
        agent_task: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log an agent creation event.

        Args:
            session: Database session
            user: User who created the agent
            agent_id: Created agent ID
            agent_task: Agent task description
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog instance
        """
        return await self.log(
            session=session,
            action="agent.created",
            user=user,
            resource_type="agent",
            resource_id=str(agent_id),
            details={"task": agent_task},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_agent_deleted(
        self,
        session: AsyncSession,
        user: User,
        agent_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log an agent deletion event.

        Args:
            session: Database session
            user: User who deleted the agent
            agent_id: Deleted agent ID
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog instance
        """
        return await self.log(
            session=session,
            action="agent.deleted",
            user=user,
            resource_type="agent",
            resource_id=str(agent_id),
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_team_created(
        self,
        session: AsyncSession,
        user: User,
        team_id: UUID,
        team_name: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a team creation event.

        Args:
            session: Database session
            user: User who created the team
            team_id: Created team ID
            team_name: Team name
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog instance
        """
        return await self.log(
            session=session,
            action="team.created",
            user=user,
            resource_type="team",
            resource_id=str(team_id),
            details={"name": team_name},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_team_deleted(
        self,
        session: AsyncSession,
        user: User,
        team_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a team deletion event.

        Args:
            session: Database session
            user: User who deleted the team
            team_id: Deleted team ID
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog instance
        """
        return await self.log(
            session=session,
            action="team.deleted",
            user=user,
            resource_type="team",
            resource_id=str(team_id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
