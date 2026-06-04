from src.domain.repositories import UserRepository, RefreshTokenRepository
from src.domain.entities.user import User
from src.domain.entities.refresh_token import RefreshToken


class TestDomainRepositories:
    def test_user_repository_is_abstract(self):
        try:
            UserRepository()
            assert False, "Should not be instantiable"
        except TypeError as e:
            assert "Can't instantiate abstract class" in str(e)

    def test_refresh_token_repository_is_abstract(self):
        try:
            RefreshTokenRepository()
            assert False, "Should not be instantiable"
        except TypeError as e:
            assert "Can't instantiate abstract class" in str(e)

    def test_user_repository_methods_exist(self):
        methods = ["create", "get_by_id", "get_by_email", "get_by_username", "update"]
        for method in methods:
            assert hasattr(UserRepository, method)

    def test_refresh_token_repository_methods_exist(self):
        methods = ["create", "get_by_token_hash", "revoke", "revoke_all_for_user"]
        for method in methods:
            assert hasattr(RefreshTokenRepository, method)
