import redis.asyncio as redis
from app.core.config import get_settings

settings = get_settings()

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def cache_get(key: str) -> str | None:
    return await redis_client.get(key)


async def cache_set(key: str, value: str, ttl: int = 300):
    await redis_client.set(key, value, ex=ttl)


async def cache_delete(key: str):
    await redis_client.delete(key)


async def cache_delete_pattern(pattern: str):
    keys = []
    async for key in redis_client.scan_iter(match=pattern):
        keys.append(key)
    if keys:
        await redis_client.delete(*keys)


async def rate_limit(key: str, limit: int = 60, window: int = 60) -> bool:
    """Returns True if allowed, False if rate limited."""
    try:
        current = await redis_client.incr(f"rl:{key}")
        if current == 1:
            await redis_client.expire(f"rl:{key}", window)
        return current <= limit
    except Exception:
        return True
