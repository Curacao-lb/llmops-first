import os

from redis import Redis


def _create_redis_client() -> Redis:
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return Redis.from_url(redis_url)

    use_ssl = os.getenv("REDIS_USE_SSL", "false").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    return Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        username=os.getenv("REDIS_USERNAME") or None,
        password=os.getenv("REDIS_PASSWORD") or None,
        ssl=use_ssl,
    )


# Redis 客户端在 Injector 中作为单例使用。
# Redis 客户端不会立即建立连接，首次执行 Redis 命令时才会连接。
redis_client = _create_redis_client()
