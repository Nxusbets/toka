import structlog
from pydantic_settings import BaseSettings
from qdrant_client import AsyncQdrantClient

logger = structlog.get_logger(__name__)


class QdrantSettings(BaseSettings):
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    qdrant_https: bool = False

    model_config = {"env_prefix": "", "case_sensitive": False}


class QdrantDatabase:
    def __init__(self, settings: QdrantSettings | None = None):
        self._settings = settings or QdrantSettings()
        self._client: AsyncQdrantClient | None = None

    async def connect(self) -> None:
        self._client = AsyncQdrantClient(
            host=self._settings.qdrant_host,
            port=self._settings.qdrant_port,
            api_key=self._settings.qdrant_api_key,
            https=self._settings.qdrant_https,
        )
        await self._client.get_collections()
        await logger.ainfo("connected_to_qdrant", host=self._settings.qdrant_host, port=self._settings.qdrant_port)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            await logger.ainfo("disconnected_from_qdrant")

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            raise RuntimeError("Qdrant not connected. Call connect() first.")
        return self._client
