"""
Pydantic schemas for authentication and account management.
"""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """Shared user fields returned to clients."""

    email: str = Field(..., min_length=5, max_length=255)
    full_name: str | None = Field(None, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserSignup(UserBase):
    """Payload used to create a new account."""

    password: str = Field(..., min_length=8, max_length=72)


class UserLogin(BaseModel):
    """Payload used to authenticate an existing account."""

    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(UserBase):
    """Public user representation."""

    id: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthSessionResponse(BaseModel):
    """Response returned after successful authentication actions."""

    user: UserResponse
    message: str


class AuthStatusResponse(BaseModel):
    """Simple message response for auth actions without user payloads."""

    message: str


class CsrfTokenResponse(BaseModel):
    """Response used to bootstrap CSRF protection in the SPA."""

    csrf_token: str