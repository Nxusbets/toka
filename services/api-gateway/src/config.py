from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    auth_service_url: str = "http://auth-service:8000"
    user_service_url: str = "http://user-service:8000"
    audit_service_url: str = "http://audit-service:8000"
    ai_agent_service_url: str = "http://ai-agent-service:8000"

    model_config = {"env_prefix": "", "case_sensitive": False}
