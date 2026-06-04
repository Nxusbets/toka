import structlog
from pydantic import Field
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic_settings import BaseSettings

logger = structlog.get_logger(__name__)


class MongoSettings(BaseSettings):
    mongo_uri: str = Field(default="mongodb://mongodb:27017", alias="MONGODB_URL")
    mongo_db: str = Field(default="toka_audit", alias="MONGODB_DATABASE")

    model_config = {"populate_by_name": True, "case_sensitive": False}


class MongoDatabase:
    def __init__(self, settings: MongoSettings | None = None):
        self._settings = settings or MongoSettings()
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        self._client = AsyncIOMotorClient(self._settings.mongo_uri)
        self._db = self._client[self._settings.mongo_db]
        await self._db.command("ping")
        await logger.ainfo("connected_to_mongodb", uri=self._settings.mongo_uri, db=self._settings.mongo_db)

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            await logger.ainfo("disconnected_from_mongodb")

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self._db
