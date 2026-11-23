"""Authentication & Identity Pydantic DTO Schemas.

Defines strict request/response data contracts for authentication,
forced password change, session profile inspection, and logout.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequestDTO(BaseModel):
    """Credentials payload for login."""
    username_or_email: str = Field(..., min_length=3, max_length=255, description="Username or email address")
    password: str = Field(..., min_length=1, max_length=255, description="Plaintext password")

    model_config = ConfigDict(str_strip_whitespace=True)


class UserDTO(BaseModel):
    """Safe authenticated user profile DTO."""
    id: str
    username: str
    email: str
    full_name: str
    roles: List[str]
    account_status: str
    password_status: str
    must_change_password: bool
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LoginResponseDTO(BaseModel):
    """Successful authentication response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserDTO


class ChangePasswordRequestDTO(BaseModel):
    """Payload for forced or self-initiated password updates."""
    current_password: str = Field(..., min_length=1, description="Current temporary or existing password")
    new_password: str = Field(..., min_length=10, max_length=128, description="New permanent password")
    confirm_new_password: str = Field(..., min_length=10, max_length=128, description="Confirmation of new password")

    model_config = ConfigDict(str_strip_whitespace=True)


class ChangePasswordResponseDTO(BaseModel):
    """Successful password change response."""
    message: str
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserDTO


class MessageResponseDTO(BaseModel):
    """Standard message acknowledgment DTO."""
    message: str
