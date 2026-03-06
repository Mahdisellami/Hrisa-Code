"""Pydantic schemas for auth API."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# Request schemas

class SendMagicLinkRequest(BaseModel):
    """Request to send magic link to email."""
    email: EmailStr = Field(..., description="User email address")


class VerifyMagicLinkRequest(BaseModel):
    """Request to verify magic link token."""
    token: str = Field(..., min_length=1, description="Magic link token")


class UpdateUserRoleRequest(BaseModel):
    """Request to update user role."""
    role: str = Field(..., description="New role (admin, user, viewer)")


# Response schemas

class UserResponse(BaseModel):
    """User information response."""
    id: UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class SendMagicLinkResponse(BaseModel):
    """Response after sending magic link."""
    message: str = Field(..., description="Success message")
    is_new_user: bool = Field(..., description="Whether this is a new user")


class VerifyMagicLinkResponse(BaseModel):
    """Response after verifying magic link."""
    token: str = Field(..., description="Session token")
    user: UserResponse = Field(..., description="User information")


class LogoutResponse(BaseModel):
    """Response after logout."""
    message: str = Field(default="Logged out successfully")


class UserListResponse(BaseModel):
    """Response with list of users."""
    users: list[UserResponse]
    total: int


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str = Field(..., description="Error message")
