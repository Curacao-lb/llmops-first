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
        self.WTF_CSRF_ENABLED = False

        # 配置数据库配置
        self.SQLALCHEMY_DATABASE_URI = _get_env("SQLALCHEMY_DATABASE_URI")
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": int(_get_env("SQLALCHEMY_POOL_SIZE")),
            "pool_recycle": int(_get_env("SQLALCHEMY_POOL_RECYCLE")),
        }
        self.SQLALCHEMY_ECHO = _get_bool_env("SQLALCHEMY_ECHO")
