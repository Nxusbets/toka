from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "user-service"
    database_url: str = "postgresql+asyncpg://toka_user:toka_pass_2024@localhost:5432/toka_auth"
    rabbitmq_url: str = "amqp://toka_user:toka_pass_2024@localhost:5672/"
    jwt_secret_key: str = "super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    auth_service_url: str = "http://auth-service:8000"
    internal_api_key: str = "toka-internal-key-2024"

    model_config = {"env_file": ".env", "extra": "ignore"}
