"""Administrative User Management Pydantic DTO Schemas.

Defines request/response contracts for administrative user creation,
updates, pagination, role governance, and temporary credential disclosure.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserAdminMetricsDTO(BaseModel):
    """Aggregate platform user metrics."""
    total_users: int
    active_users: int
    administrators: int
    password_pending: int


class UserRoleDTO(BaseModel):
    """Domain role summary representation."""
    role_id: str
    role_name: str
    description: Optional[str] = None


class UserAdminResponseDTO(BaseModel):
    """Safe administrative user profile response."""
    id: str
    username: str
    email: str
    full_name: str
    roles: List[str]
    account_status: str
    password_status: str
    must_change_password: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)


class UserAdminCreateRequestDTO(BaseModel):
    """Request payload for creating a new user."""
    username: str = Field(..., min_length=3, max_length=64, description="Unique username")
    email: str = Field(..., min_length=5, max_length=255, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="Unique email address")
    full_name: str = Field(..., min_length=2, max_length=128, description="User full name")
    roles: List[str] = Field(..., min_length=1, description="Assigned role machine identifiers")

    model_config = ConfigDict(str_strip_whitespace=True)


class UserAdminCreateResponseDTO(BaseModel):
    """Immediate one-time credential response for user creation."""
    user: UserAdminResponseDTO
    temporary_password: str = Field(..., description="One-time plaintext temporary credential")
    expires_at: datetime
    message: str = "User created successfully. Transfer temporary password securely to the user."


class UserAdminUpdateRequestDTO(BaseModel):
    """Request payload for updating permitted user fields."""
    email: Optional[str] = Field(None, min_length=5, max_length=255, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    full_name: Optional[str] = Field(None, min_length=2, max_length=128)
    roles: Optional[List[str]] = Field(None, min_length=1)
    version: Optional[int] = Field(None, description="Current optimistic locking version")

    model_config = ConfigDict(str_strip_whitespace=True)


class UserAdminListResponseDTO(BaseModel):
    """Paginated user listing with metrics."""
    items: List[UserAdminResponseDTO]
    total: int
    page: int
    page_size: int
    metrics: UserAdminMetricsDTO


class PasswordResetResponseDTO(BaseModel):
    """One-time credential disclosure for admin-initiated password resets."""
    user_id: str
    username: str
    temporary_password: str
    expires_at: datetime
    message: str = "Password has been reset. All previous sessions revoked."
