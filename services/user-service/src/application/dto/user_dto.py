from __future__ import annotations
import re
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class CreateUserRequest(BaseModel):
    email: str = Field(..., max_length=255)
    username: str = Field(..., min_length=3, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format")
        return v


class UpdateUserRequest(BaseModel):
    email: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    is_active: Optional[bool] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if v is not None and not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format")
        return v


class AssignRoleRequest(BaseModel):
    role_id: UUID


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    roles: list["RoleResponse"] = []


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str
    is_system: bool
    created_at: datetime
    updated_at: datetime
    permissions: list["PermissionResponse"] = []


class PermissionResponse(BaseModel):
    id: UUID
    name: str
    resource: str
    action: str
    description: str
    created_at: datetime


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class CreateRoleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str = ""


class UpdateRoleRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
