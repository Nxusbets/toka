from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "auth-service"
    database_url: str = "postgresql+asyncpg://toka_user:toka_pass_2024@localhost:5432/toka_auth"
    redis_url: str = "redis://:toka_pass_2024@localhost:6379/0"
    rabbitmq_url: str = "amqp://toka_user:toka_pass_2024@localhost:5672/"
    jwt_secret_key: str = "super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    user_service_url: str = "http://user-service:8000"

    model_config = {"env_file": ".env", "extra": "ignore"}
