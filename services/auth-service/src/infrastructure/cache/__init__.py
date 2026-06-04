from typing import Optional

from redis.asyncio import Redis

from src.config import Settings

redis_client: Optional[Redis] = None


async def init_redis(settings: Settings):
    global redis_client
    redis_client = await Redis.from_url(
        settings.redis_url, decode_responses=True, max_connections=20
    )


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


def get_redis() -> Redis:
    return redis_client


async def blacklist_token(jti: str, expires_in: int):
    if redis_client:
        await redis_client.setex(f"token:blacklist:{jti}", expires_in, "true")


async def is_token_blacklisted(jti: str) -> bool:
    if redis_client:
        result = await redis_client.get(f"token:blacklist:{jti}")
        return result is not None
    return False
