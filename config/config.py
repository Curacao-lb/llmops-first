import os
from typing import Any

from .default_config import DEFAULT_CONFIG


def _get_env(key) -> Any:
    """从环境变量中获取配置项，如果找不到则返回默认值。"""
    return os.getenv(key, DEFAULT_CONFIG.get(key))


def _get_bool_env(key) -> bool:
    """
    从环境变量中获取布尔类型的配置项，如果找不到则返回默认值。

    支持的 True 值(不区分大小写): "1", "true", "yes", "on"
    其他任何值(包括 "0", "false", "no", "off" 等)都返回 False
    """
    value = _get_env(key)
    # 如果值为 None 或空字符串，返回 False
    if not value:
        return False
    return str(value).lower() in ("1", "true", "yes", "on")


class Config:
    def __init__(self):
        # 关闭WTF的CSRF保护
        self.WTF_CSRF_ENABLED = _get_bool_env("WTF_CSRF_ENABLED")

        # 配置数据库配置
        self.SQLALCHEMY_DATABASE_URI = _get_env("SQLALCHEMY_DATABASE_URI")
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": int(_get_env("SQLALCHEMY_POOL_SIZE")),
            "pool_recycle": int(_get_env("SQLALCHEMY_POOL_RECYCLE")),
        }
        self.SQLALCHEMY_ECHO = _get_bool_env("SQLALCHEMY_ECHO")

        # weavite 向量数据库配置
        self.WEAVIATE_HTTP_HOST = _get_env("WEAVIATE_HTTP_HOST")
        self.WEAVIATE_HTTP_PORT = _get_env("WEAVIATE_HTTP_PORT")
        self.WEAVIATE_GRPC_HOST = _get_env("WEAVIATE_GRPC_HOST")
        self.WEAVIATE_GRPC_PORT = _get_env("WEAVIATE_GRPC_PORT")
        self.WEAVIATE_API_KEY = _get_env("WEAVIATE_API_KEY") or None

        # Redis配置
        self.REDIS_HOST = _get_env("REDIS_HOST")
        self.REDIS_PORT = _get_env("REDIS_PORT")
        self.REDIS_USERNAME = _get_env("REDIS_USERNAME")
        self.REDIS_PASSWORD = _get_env("REDIS_PASSWORD")
        self.REDIS_DB = _get_env("REDIS_DB")
        self.REDIS_USE_SSL = _get_bool_env("REDIS_USE_SSL")

        # Celery配置
        self.CELERY = {
            "broker_url": f"redis://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{int(_get_env('CELERY_BROKER_DB'))}",
            "result_backend": f"redis://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{int(_get_env('CELERY_RESULT_BACKEND_DB'))}",
            "task_ignore_result": _get_bool_env("CELERY_TASK_IGNORE_RESULT"),
            "result_expires": int(_get_env("CELERY_RESULT_EXPIRES")),
            "broker_connection_retry_on_startup": _get_bool_env(
                "CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP"
            ),
        }

        # # 辅助Agent应用id标识
        # self.ASSISTANT_AGENT_ID = _get_env("ASSISTANT_AGENT_ID")
