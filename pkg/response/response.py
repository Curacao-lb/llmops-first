from .http_code import HttpCode
from typing import Any
from dataclasses import field, dataclass


@dataclass
class Response:
    """基础HTTP响应数据格式"""

    code: HttpCode = HttpCode.SUCCESS  # 给他一个默认值Success
    message: str = ""
    # 通过默认的工厂函数来去创建一个空字典
    data: Any = field(default_factory=dict)
