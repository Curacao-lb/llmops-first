import os
from typing import Any
from urllib.parse import quote

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

        # 邮件配置：465 默认使用 SMTPS，其他端口默认使用 STARTTLS。
        self.SMTP_SERVER = _get_env("SMTP_SERVER") or None
        smtp_port = _get_env("SMTP_PORT")
        self.SMTP_PORT = int(smtp_port) if smtp_port else None
        self.SENDER_EMAIL = _get_env("SENDER_EMAIL") or None
        self.SMTP_USERNAME = _get_env("SMTP_USERNAME") or self.SENDER_EMAIL
        self.SMTP_PASSWORD = _get_env("SMTP_PASSWORD") or None
        self.SMTP_AUTH_METHOD = (
            _get_env("SMTP_AUTH_METHOD") or "password"
        ).strip().lower()
        self.SMTP_CLIENT_ID = _get_env("SMTP_CLIENT_ID") or None
        self.SMTP_REFRESH_TOKEN = _get_env("SMTP_REFRESH_TOKEN") or None
        self.SMTP_TENANT = _get_env("SMTP_TENANT") or "consumers"
        smtp_use_ssl = _get_env("SMTP_USE_SSL")
        self.SMTP_USE_SSL = (
            _get_bool_env("SMTP_USE_SSL")
            if smtp_use_ssl not in (None, "")
            else self.SMTP_PORT == 465
        )
        smtp_use_tls = _get_env("SMTP_USE_TLS")
        self.SMTP_USE_TLS = (
            _get_bool_env("SMTP_USE_TLS")
            if smtp_use_tls not in (None, "")
            else not self.SMTP_USE_SSL
        )

        # Redis配置
        self.REDIS_HOST = _get_env("REDIS_HOST")
        self.REDIS_PORT = _get_env("REDIS_PORT")
        self.REDIS_USERNAME = _get_env("REDIS_USERNAME")
        self.REDIS_PASSWORD = _get_env("REDIS_PASSWORD")
        self.REDIS_DB = _get_env("REDIS_DB")
        self.REDIS_USE_SSL = _get_bool_env("REDIS_USE_SSL")

        # Celery配置
        redis_scheme = "rediss" if self.REDIS_USE_SSL else "redis"
        redis_username = _get_env("REDIS_USERNAME") or ""
        redis_password = _get_env("REDIS_PASSWORD") or ""
        if redis_username or redis_password:
            encoded_username = quote(str(redis_username), safe="")
            encoded_password = quote(str(redis_password), safe="")
            redis_auth = f"{encoded_username}:{encoded_password}@"
        else:
            redis_auth = ""
        redis_host = _get_env("REDIS_HOST")
        redis_port = _get_env("REDIS_PORT")

        self.CELERY = {
            "broker_url": (
                f"{redis_scheme}://{redis_auth}{redis_host}:{redis_port}/"
                f"{int(_get_env('CELERY_BROKER_DB'))}"
            ),
            "result_backend": (
                f"{redis_scheme}://{redis_auth}{redis_host}:{redis_port}/"
                f"{int(_get_env('CELERY_RESULT_BACKEND_DB'))}"
            ),
            "task_ignore_result": _get_bool_env("CELERY_TASK_IGNORE_RESULT"),
            "result_expires": int(_get_env("CELERY_RESULT_EXPIRES")),
            "broker_connection_retry_on_startup": _get_bool_env(
                "CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP"
            ),
        }

        # # 辅助Agent应用id标识
        # self.ASSISTANT_AGENT_ID = _get_env("ASSISTANT_AGENT_ID")
