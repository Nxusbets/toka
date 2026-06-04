import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException

from src.domain.entities.user import User
from src.domain.entities.role import Role
from src.application.dto.user_dto import (
    CreateUserRequest, UpdateUserRequest, AssignRoleRequest,
    CreateRoleRequest, UpdateRoleRequest,
)
from src.application.use_cases.user_use_cases import (
    CreateUserUseCase, GetUserUseCase, ListUsersUseCase,
    UpdateUserUseCase, DeleteUserUseCase, AssignRoleUseCase,
    RemoveRoleUseCase, CreateRoleUseCase, ListRolesUseCase,
    GetRoleUseCase, UpdateRoleUseCase, DeleteRoleUseCase,
    ListPermissionsUseCase, GetRolePermissionsUseCase, SyncUserUseCase,
    _user_to_response, _role_to_response, _permission_to_response,
)


pytestmark = pytest.mark.asyncio


class TestCreateUserUseCase:
    async def test_create_success(self, mock_user_repo, mock_event_publisher, sample_user):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.create.return_value = sample_user

        use_case = CreateUserUseCase(mock_user_repo, mock_event_publisher)
        request = CreateUserRequest(email="test@example.com", username="testuser")
        result = await use_case.execute(request)

        assert result.email == "test@example.com"
        assert result.username == "testuser"
        mock_user_repo.create.assert_called_once()
        mock_event_publisher.publish.assert_called_once()

    async def test_create_duplicate_email(self, mock_user_repo, mock_event_publisher, sample_user):
        mock_user_repo.get_by_email.return_value = sample_user

        use_case = CreateUserUseCase(mock_user_repo, mock_event_publisher)
        request = CreateUserRequest(email="test@example.com", username="testuser")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(request)
        assert exc.value.status_code == 409
        assert "Email already exists" in exc.value.detail

    async def test_create_duplicate_username(self, mock_user_repo, mock_event_publisher, sample_user):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.get_by_username.return_value = sample_user

        use_case = CreateUserUseCase(mock_user_repo, mock_event_publisher)
        request = CreateUserRequest(email="other@example.com", username="existing")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(request)
        assert exc.value.status_code == 409
        assert "Username already exists" in exc.value.detail


class TestGetUserUseCase:
    async def test_get_success(self, mock_user_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.get_roles.return_value = []

        use_case = GetUserUseCase(mock_user_repo)
        result = await use_case.execute(sample_user.id)

        assert result.id == sample_user.id
        assert result.email == sample_user.email

    async def test_get_not_found(self, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None

        use_case = GetUserUseCase(mock_user_repo)
        with pytest.raises(HTTPException) as exc:
            await use_case.execute(uuid4())
        assert exc.value.status_code == 404


class TestListUsersUseCase:
    async def test_list_empty(self, mock_user_repo):
        mock_user_repo.list.return_value = []
        mock_user_repo.count.return_value = 0

        use_case = ListUsersUseCase(mock_user_repo)
        result = await use_case.execute()

        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.page_size == 20

    async def test_list_with_results(self, mock_user_repo, sample_user):
        mock_user_repo.list.return_value = [sample_user]
        mock_user_repo.count.return_value = 1
        mock_user_repo.get_roles.return_value = []

        use_case = ListUsersUseCase(mock_user_repo)
        result = await use_case.execute(page=1, page_size=20)

        assert len(result.items) == 1
        assert result.total == 1

    async def test_list_with_filters(self, mock_user_repo):
        use_case = ListUsersUseCase(mock_user_repo)
        role_id = uuid4()
        await use_case.execute(page=1, page_size=20, role_id=role_id, is_active=True)

        mock_user_repo.list.assert_called_once_with(skip=0, limit=20, role_id=role_id, is_active=True)


class TestUpdateUserUseCase:
    async def test_update_success(self, mock_user_repo, mock_event_publisher, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.update.return_value = sample_user
        mock_user_repo.get_roles.return_value = []

        use_case = UpdateUserUseCase(mock_user_repo, mock_event_publisher)
        request = UpdateUserRequest(email="new@example.com", username="newname")
        result = await use_case.execute(sample_user.id, request)

        assert result is not None
        mock_user_repo.update.assert_called_once()
        mock_event_publisher.publish.assert_called_once()

    async def test_update_not_found(self, mock_user_repo, mock_event_publisher):
        mock_user_repo.get_by_id.return_value = None

        use_case = UpdateUserUseCase(mock_user_repo, mock_event_publisher)
        request = UpdateUserRequest(email="new@example.com")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(uuid4(), request)
        assert exc.value.status_code == 404

    async def test_update_no_changes(self, mock_user_repo, mock_event_publisher, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.get_roles.return_value = []

        use_case = UpdateUserUseCase(mock_user_repo, mock_event_publisher)
        request = UpdateUserRequest()
        result = await use_case.execute(sample_user.id, request)

        assert result is not None
        mock_user_repo.update.assert_not_called()


class TestDeleteUserUseCase:
    async def test_delete_success(self, mock_user_repo, mock_event_publisher, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user

        use_case = DeleteUserUseCase(mock_user_repo, mock_event_publisher)
        await use_case.execute(sample_user.id)

        mock_user_repo.delete.assert_called_once_with(sample_user.id)
        mock_event_publisher.publish.assert_called_once()

    async def test_delete_not_found(self, mock_user_repo, mock_event_publisher):
        mock_user_repo.get_by_id.return_value = None

        use_case = DeleteUserUseCase(mock_user_repo, mock_event_publisher)
        with pytest.raises(HTTPException) as exc:
            await use_case.execute(uuid4())
        assert exc.value.status_code == 404


class TestAssignRoleUseCase:
    async def test_assign_success(self, mock_user_repo, mock_role_repo, mock_event_publisher, sample_user, sample_role):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_role_repo.get_by_id.return_value = sample_role
        mock_user_repo.get_roles.return_value = [sample_role]

        use_case = AssignRoleUseCase(mock_user_repo, mock_role_repo, mock_event_publisher)
        request = AssignRoleRequest(role_id=sample_role.id)
        result = await use_case.execute(sample_user.id, request)

        assert result is not None
        mock_user_repo.assign_role.assert_called_once()
        mock_event_publisher.publish.assert_called_once()

    async def test_assign_user_not_found(self, mock_user_repo, mock_role_repo, mock_event_publisher):
        mock_user_repo.get_by_id.return_value = None

        use_case = AssignRoleUseCase(mock_user_repo, mock_role_repo, mock_event_publisher)
        request = AssignRoleRequest(role_id=uuid4())

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(uuid4(), request)
        assert exc.value.status_code == 404

    async def test_assign_role_not_found(self, mock_user_repo, mock_role_repo, mock_event_publisher, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_role_repo.get_by_id.return_value = None

        use_case = AssignRoleUseCase(mock_user_repo, mock_role_repo, mock_event_publisher)
        request = AssignRoleRequest(role_id=uuid4())

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(sample_user.id, request)
        assert exc.value.status_code == 404


class TestRemoveRoleUseCase:
    async def test_remove_success(self, mock_user_repo, sample_user, sample_role):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.get_roles.return_value = []

        use_case = RemoveRoleUseCase(mock_user_repo)
        result = await use_case.execute(sample_user.id, sample_role.id)

        assert result is not None
        mock_user_repo.remove_role.assert_called_once_with(sample_user.id, sample_role.id)

    async def test_remove_user_not_found(self, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None

        use_case = RemoveRoleUseCase(mock_user_repo)
        with pytest.raises(HTTPException) as exc:
            await use_case.execute(uuid4(), uuid4())
        assert exc.value.status_code == 404


class TestCreateRoleUseCase:
    async def test_create_success(self, mock_role_repo, sample_role):
        mock_role_repo.get_by_name.return_value = None
        mock_role_repo.create.return_value = sample_role

        use_case = CreateRoleUseCase(mock_role_repo)
        request = CreateRoleRequest(name="admin", description="Admin role")
        result = await use_case.execute(request)

        assert result.name == "admin"
        mock_role_repo.create.assert_called_once()

    async def test_create_duplicate(self, mock_role_repo, sample_role):
        mock_role_repo.get_by_name.return_value = sample_role

        use_case = CreateRoleUseCase(mock_role_repo)
        request = CreateRoleRequest(name="admin")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(request)
        assert exc.value.status_code == 409


class TestListRolesUseCase:
    async def test_list_empty(self, mock_role_repo, mock_permission_repo):
        mock_role_repo.list.return_value = []
        mock_role_repo.count.return_value = 0

        use_case = ListRolesUseCase(mock_role_repo, mock_permission_repo)
        result = await use_case.execute()

        assert result.items == []
        assert result.total == 0

    async def test_list_with_results(self, mock_role_repo, mock_permission_repo, sample_role):
        mock_role_repo.list.return_value = [sample_role]
        mock_role_repo.count.return_value = 1
        mock_role_repo.get_permissions.return_value = []

        use_case = ListRolesUseCase(mock_role_repo, mock_permission_repo)
        result = await use_case.execute(page=1, page_size=20)

        assert len(result.items) == 1
        assert result.total == 1


class TestGetRoleUseCase:
    async def test_get_success(self, mock_role_repo, sample_role):
        mock_role_repo.get_by_id.return_value = sample_role
        mock_role_repo.get_permissions.return_value = []

        use_case = GetRoleUseCase(mock_role_repo)
        result = await use_case.execute(sample_role.id)

        assert result.id == sample_role.id
        assert result.name == "admin"

    async def test_get_not_found(self, mock_role_repo):
        mock_role_repo.get_by_id.return_value = None

        use_case = GetRoleUseCase(mock_role_repo)
        with pytest.raises(HTTPException) as exc:
            await use_case.execute(uuid4())
        assert exc.value.status_code == 404


class TestUpdateRoleUseCase:
    async def test_update_success(self, mock_role_repo, sample_role):
        mock_role_repo.get_by_id.return_value = sample_role
        mock_role_repo.get_by_name.return_value = None
        mock_role_repo.update.return_value = sample_role
        mock_role_repo.get_permissions.return_value = []

        use_case = UpdateRoleUseCase(mock_role_repo)
        request = UpdateRoleRequest(name="moderator", description="Updated")
        result = await use_case.execute(sample_role.id, request)

        assert result.name == "moderator"

    async def test_update_system_role(self, mock_role_repo):
        system_role = Role(id=uuid4(), name="system", is_system=True)
        mock_role_repo.get_by_id.return_value = system_role

        use_case = UpdateRoleUseCase(mock_role_repo)
        request = UpdateRoleRequest(name="newname")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(system_role.id, request)
        assert exc.value.status_code == 403

    async def test_update_not_found(self, mock_role_repo):
        mock_role_repo.get_by_id.return_value = None

        use_case = UpdateRoleUseCase(mock_role_repo)
        request = UpdateRoleRequest(name="newname")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(uuid4(), request)
        assert exc.value.status_code == 404


class TestDeleteRoleUseCase:
    async def test_delete_success(self, mock_role_repo, sample_role):
        mock_role_repo.get_by_id.return_value = sample_role

        use_case = DeleteRoleUseCase(mock_role_repo)
        await use_case.execute(sample_role.id)

        mock_role_repo.delete.assert_called_once_with(sample_role.id)

    async def test_delete_not_found(self, mock_role_repo):
        mock_role_repo.get_by_id.return_value = None

        use_case = DeleteRoleUseCase(mock_role_repo)
        with pytest.raises(HTTPException) as exc:
            await use_case.execute(uuid4())
        assert exc.value.status_code == 404

    async def test_delete_system_role(self, mock_role_repo):
        system_role = Role(id=uuid4(), name="system", is_system=True)
        mock_role_repo.get_by_id.return_value = system_role

        use_case = DeleteRoleUseCase(mock_role_repo)
        with pytest.raises(HTTPException) as exc:
            await use_case.execute(system_role.id)
        assert exc.value.status_code == 403


class TestListPermissionsUseCase:
    async def test_list_empty(self, mock_permission_repo):
        mock_permission_repo.list.return_value = []
        mock_permission_repo.count.return_value = 0

        use_case = ListPermissionsUseCase(mock_permission_repo)
        result = await use_case.execute()

        assert result.items == []
        assert result.total == 0

    async def test_list_with_results(self, mock_permission_repo, sample_permission):
        mock_permission_repo.list.return_value = [sample_permission]
        mock_permission_repo.count.return_value = 1

        use_case = ListPermissionsUseCase(mock_permission_repo)
        result = await use_case.execute()

        assert len(result.items) == 1


class TestGetRolePermissionsUseCase:
    async def test_get_success(self, mock_role_repo, sample_role, sample_permission):
        mock_role_repo.get_by_id.return_value = sample_role
        mock_role_repo.get_permissions.return_value = [sample_permission]

        use_case = GetRolePermissionsUseCase(mock_role_repo)
        result = await use_case.execute(sample_role.id)

        assert len(result) == 1
        assert result[0].name == "user:read"

    async def test_get_role_not_found(self, mock_role_repo):
        mock_role_repo.get_by_id.return_value = None

        use_case = GetRolePermissionsUseCase(mock_role_repo)
        with pytest.raises(HTTPException) as exc:
            await use_case.execute(uuid4())
        assert exc.value.status_code == 404


class TestSyncUserUseCase:
    async def test_sync_existing_user(self, mock_user_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.update.return_value = sample_user

        use_case = SyncUserUseCase(mock_user_repo)
        await use_case.execute(sample_user.id, "updated@example.com", "updateduser")

        assert sample_user.email == "updated@example.com"
        assert sample_user.username == "updateduser"
        mock_user_repo.update.assert_called_once()

    async def test_sync_new_user(self, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None
        mock_user_repo.create.return_value = User(
            id=uuid4(), email="new@example.com", username="newuser",
        )

        use_case = SyncUserUseCase(mock_user_repo)
        user_id = uuid4()
        await use_case.execute(user_id, "new@example.com", "newuser")

        mock_user_repo.create.assert_called_once()


class TestResponseHelpers:
    def test_user_to_response(self, sample_user):
        result = _user_to_response(sample_user)
        assert result.id == sample_user.id
        assert result.email == sample_user.email
        assert result.roles == []

    def test_user_to_response_with_roles(self, sample_user, sample_role):
        result = _user_to_response(sample_user, [sample_role])
        assert len(result.roles) == 1
        assert result.roles[0].name == "admin"

    def test_role_to_response(self, sample_role):
        result = _role_to_response(sample_role)
        assert result.name == "admin"
        assert result.permissions == []

    def test_permission_to_response(self, sample_permission):
        result = _permission_to_response(sample_permission)
        assert result.name == "user:read"
