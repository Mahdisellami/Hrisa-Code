"""RBAC middleware and authentication dependencies for FastAPI."""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from hrisa_code.web.db.database import get_database
from hrisa_code.web.db.models import User
from hrisa_code.web.auth.session import SessionManager

# Global session manager instance
session_manager = SessionManager(session_expiry_days=30)


# Dependency to get database session
async def get_db_session():
    """Get database session dependency."""
    db = get_database()
    async with db.get_session() as session:
        yield session


def extract_token_from_header(request: Request) -> Optional[str]:
    """Extract bearer token from Authorization header.

    Args:
        request: FastAPI request object

    Returns:
        Token string if found, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    if not auth_header.startswith("Bearer "):
        return None

    return auth_header.replace("Bearer ", "").strip()


async def get_current_user_optional(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise.

    This dependency does NOT raise exceptions, allowing endpoints
    to handle unauthenticated users gracefully.

    Args:
        request: FastAPI request object
        session: Database session

    Returns:
        User if authenticated, None otherwise
    """
    token = extract_token_from_header(request)
    if not token:
        return None

    user = await session_manager.get_user_from_token(session, token)
    return user


async def get_current_user_required(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Get current user, raise 401 if not authenticated.

    This dependency enforces authentication on endpoints.

    Args:
        request: FastAPI request object
        session: Database session

    Returns:
        User instance

    Raises:
        HTTPException: 401 if not authenticated or token invalid
    """
    token = extract_token_from_header(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await session_manager.get_user_from_token(session, token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


class RoleChecker:
    """Dependency class to check if user has required role.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(RoleChecker(["admin"]))])
        async def admin_endpoint():
            ...

        # Or get the user:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(RoleChecker(["admin"]))):
            ...
    """

    def __init__(self, allowed_roles: List[str]):
        """Initialize role checker.

        Args:
            allowed_roles: List of roles that are allowed access
        """
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        user: User = Depends(get_current_user_required),
    ) -> User:
        """Check if user has required role.

        Args:
            user: Current authenticated user

        Returns:
            User instance

        Raises:
            HTTPException: 403 if user doesn't have required role
        """
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}",
            )

        return user


# Convenience role dependencies for common cases

def get_admin_user(
    user: User = Depends(get_current_user_required),
) -> User:
    """Require admin role.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(get_admin_user)):
            ...
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def get_user_or_admin(
    user: User = Depends(get_current_user_required),
) -> User:
    """Require user or admin role (not viewer).

    Usage:
        @router.post("/create-agent")
        async def create_agent(user: User = Depends(get_user_or_admin)):
            ...
    """
    if user.role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User or admin access required",
        )
    return user


def check_resource_ownership(
    current_user: User,
    resource_user_id: str,
) -> bool:
    """Check if user owns a resource or is admin.

    Args:
        current_user: Current authenticated user
        resource_user_id: User ID that owns the resource

    Returns:
        True if user owns resource or is admin, False otherwise
    """
    if current_user.role == "admin":
        return True

    return str(current_user.id) == str(resource_user_id)


def require_resource_ownership(
    current_user: User,
    resource_user_id: str,
) -> None:
    """Require user to own a resource or be admin.

    Args:
        current_user: Current authenticated user
        resource_user_id: User ID that owns the resource

    Raises:
        HTTPException: 403 if user doesn't own resource and is not admin
    """
    if not check_resource_ownership(current_user, resource_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource",
        )


# Summary of available dependencies:
#
# For optional auth (allows unauthenticated):
#   user: Optional[User] = Depends(get_current_user_optional)
#
# For required auth (raises 401):
#   user: User = Depends(get_current_user_required)
#
# For admin-only endpoints:
#   user: User = Depends(get_admin_user)
#
# For user/admin endpoints (not viewer):
#   user: User = Depends(get_user_or_admin)
#
# For custom role checking:
#   user: User = Depends(RoleChecker(["admin", "user"]))
#
# For resource ownership checking (in endpoint body):
#   require_resource_ownership(current_user, resource.user_id)
