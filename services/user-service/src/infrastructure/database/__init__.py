from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from src.config import Settings


class Base(DeclarativeBase):
    pass


engine = None
async_session_factory = None


async def init_db(settings: Settings):
    global engine, async_session_factory
    engine = create_async_engine(settings.database_url, echo=False, pool_size=10, max_overflow=20)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def close_db():
    global engine
    if engine:
        await engine.dispose()


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
