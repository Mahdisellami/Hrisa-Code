"""FastAPI routes for authentication and user management."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from hrisa_code.web.db.database import get_database
from hrisa_code.web.auth.magic_link import MagicLinkService
from hrisa_code.web.auth.email import create_email_service_from_env
from hrisa_code.web.auth.session import SessionManager
from hrisa_code.web.auth.user_service import UserService
from hrisa_code.web.auth.audit import AuditLogger
from hrisa_code.web.auth.schemas import (
    SendMagicLinkRequest,
    SendMagicLinkResponse,
    VerifyMagicLinkResponse,
    LogoutResponse,
    UserResponse,
    UserListResponse,
    UpdateUserRoleRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Service instances
magic_link_service = MagicLinkService(token_expiry_minutes=15)
session_manager = SessionManager(session_expiry_days=30)
user_service = UserService()
audit_logger = AuditLogger()


# Dependency to get database session
async def get_session() -> AsyncSession:
    """Get database session dependency."""
    db = get_database()
    async with db.get_session() as session:
        yield session


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")


# Authentication endpoints

@router.post("/send-magic-link", response_model=SendMagicLinkResponse)
async def send_magic_link(
    request_data: SendMagicLinkRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Send magic link to user's email.

    If user doesn't exist, creates a new account. First user becomes admin.
    """
    email = request_data.email
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Get or create user
    user, is_new_user = await user_service.get_or_create_user(session, email)

    # Create magic link token
    token = await magic_link_service.create_magic_link(
        session=session,
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Send email
    email_service = create_email_service_from_env()
    if not email_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email service not configured",
        )

    success = await email_service.send_magic_link(
        to_email=email,
        token=token,
        is_new_user=is_new_user,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email",
        )

    # Log event
    await audit_logger.log_magic_link_sent(
        session=session,
        email=email,
        is_new_user=is_new_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await session.commit()

    return SendMagicLinkResponse(
        message="Magic link sent to your email",
        is_new_user=is_new_user,
    )


@router.get("/verify")
async def verify_magic_link(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Verify magic link and create session.

    Returns session token in response. Frontend should redirect to app.
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Verify magic link
    user = await magic_link_service.verify_magic_link(
        session=session,
        token=token,
        ip_address=ip_address,
    )

    if not user:
        # Redirect to login page with error
        return RedirectResponse(
            url="/?error=invalid_token",
            status_code=status.HTTP_302_FOUND,
        )

    # Create session
    session_token = await session_manager.create_session(
        db_session=session,
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Log login
    await audit_logger.log_login(
        session=session,
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await session.commit()

    # Redirect to app with token in URL fragment (frontend will extract and store)
    return RedirectResponse(
        url=f"/#token={session_token}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Logout user by revoking session token."""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = auth_header.replace("Bearer ", "")
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Get user before revoking session
    user = await session_manager.get_user_from_token(session, token)

    # Revoke session
    revoked = await session_manager.revoke_session(session, token)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Log logout if we found the user
    if user:
        await audit_logger.log_logout(
            session=session,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    await session.commit()

    return LogoutResponse()


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Get current authenticated user information."""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = auth_header.replace("Bearer ", "")

    # Get user from token
    user = await session_manager.get_user_from_token(session, token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    await session.commit()

    return UserResponse.from_orm(user)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    request: Request,
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
):
    """List all users (admin only)."""
    # Get current user
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = auth_header.replace("Bearer ", "")
    current_user = await session_manager.get_user_from_token(session, token)

    if not current_user or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # List users
    users = await user_service.list_users(
        session=session,
        skip=skip,
        limit=limit,
        include_inactive=True,
    )

    total = await user_service.count_users(session)

    await session.commit()

    return UserListResponse(
        users=[UserResponse.from_orm(u) for u in users],
        total=total,
    )


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    request_data: UpdateUserRoleRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Update user role (admin only)."""
    # Get current user
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = auth_header.replace("Bearer ", "")
    current_user = await session_manager.get_user_from_token(session, token)

    if not current_user or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Get target user
    target_user = await user_service.get_user_by_id(session, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    old_role = target_user.role

    # Update role
    try:
        updated_user = await user_service.update_user_role(
            session=session,
            user_id=user_id,
            new_role=request_data.role,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Log event
    await audit_logger.log_user_role_update(
        session=session,
        actor=current_user,
        target_user_id=user_id,
        old_role=old_role,
        new_role=request_data.role,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    await session.commit()

    return UserResponse.from_orm(updated_user)


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Deactivate user account (admin only)."""
    # Get current user
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = auth_header.replace("Bearer ", "")
    current_user = await session_manager.get_user_from_token(session, token)

    if not current_user or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Deactivate user
    updated_user = await user_service.deactivate_user(session, user_id)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Log event
    await audit_logger.log_user_deactivated(
        session=session,
        actor=current_user,
        target_user_id=user_id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    await session.commit()

    return UserResponse.from_orm(updated_user)


@router.post("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Activate user account (admin only)."""
    # Get current user
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = auth_header.replace("Bearer ", "")
    current_user = await session_manager.get_user_from_token(session, token)

    if not current_user or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Activate user
    updated_user = await user_service.activate_user(session, user_id)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await session.commit()

    return UserResponse.from_orm(updated_user)
