import pytest
from uuid import UUID
from datetime import datetime
from pydantic import ValidationError

from src.application.dto.user_dto import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    RoleResponse,
    PermissionResponse,
    AssignRoleRequest,
    CreateRoleRequest,
    UpdateRoleRequest,
    PaginatedResponse,
)


class TestCreateUserRequest:
    def test_valid_request(self):
        dto = CreateUserRequest(email="test@example.com", username="testuser")
        assert dto.email == "test@example.com"
        assert dto.username == "testuser"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            CreateUserRequest(email="invalid", username="testuser")

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            CreateUserRequest(email="test@example.com", username="ab")

    def test_username_too_long(self):
        with pytest.raises(ValidationError):
            CreateUserRequest(email="test@example.com", username="a" * 101)

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            CreateUserRequest()


class TestUpdateUserRequest:
    def test_valid_update_all_fields(self):
        dto = UpdateUserRequest(email="new@example.com", username="newname", is_active=False)
        assert dto.email == "new@example.com"
        assert dto.username == "newname"
        assert dto.is_active is False

    def test_valid_update_partial(self):
        dto = UpdateUserRequest(email="new@example.com")
        assert dto.email == "new@example.com"
        assert dto.username is None
        assert dto.is_active is None

    def test_all_optional(self):
        dto = UpdateUserRequest()
        assert dto.email is None
        assert dto.username is None
        assert dto.is_active is None


class TestAssignRoleRequest:
    def test_valid(self):
        role_id = UUID("12345678-1234-5678-1234-567812345678")
        dto = AssignRoleRequest(role_id=role_id)
        assert dto.role_id == role_id

    def test_missing_role_id(self):
        with pytest.raises(ValidationError):
            AssignRoleRequest()


class TestCreateRoleRequest:
    def test_valid(self):
        dto = CreateRoleRequest(name="admin", description="Admin role")
        assert dto.name == "admin"
        assert dto.description == "Admin role"

    def test_name_too_short(self):
        with pytest.raises(ValidationError):
            CreateRoleRequest(name="", description="test")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            CreateRoleRequest(name="a" * 51, description="test")

    def test_default_description(self):
        dto = CreateRoleRequest(name="admin")
        assert dto.description == ""


class TestUpdateRoleRequest:
    def test_valid(self):
        dto = UpdateRoleRequest(name="admin", description="Updated")
        assert dto.name == "admin"
        assert dto.description == "Updated"

    def test_partial(self):
        dto = UpdateRoleRequest(name="moderator")
        assert dto.name == "moderator"
        assert dto.description is None


class TestResponses:
    def test_user_response(self):
        now = datetime.utcnow()
        dto = UserResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            username="testuser",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert dto.roles == []

    def test_role_response(self):
        now = datetime.utcnow()
        dto = RoleResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            name="admin",
            description="Admin",
            is_system=False,
            created_at=now,
            updated_at=now,
        )
        assert dto.permissions == []

    def test_permission_response(self):
        now = datetime.utcnow()
        dto = PermissionResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            name="user:read",
            resource="user",
            action="read",
            description="Read users",
            created_at=now,
        )
        assert dto.name == "user:read"

    def test_paginated_response(self):
        dto = PaginatedResponse(items=[1, 2, 3], total=3, page=1, page_size=10, total_pages=1)
        assert dto.total_pages == 1
        assert len(dto.items) == 3

    def test_paginated_response_rounds_up(self):
        dto = PaginatedResponse(items=[1], total=11, page=1, page_size=10, total_pages=2)
        assert dto.total_pages == 2
