import os

from redis import Redis


# Redis 客户端在 Injector 中作为单例使用。
# Redis.from_url() 不会立即建立连接，首次执行 Redis 命令时才会连接。
redis_client = Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)
