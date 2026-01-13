from .http_code import HttpCode
from typing import Any


class Response:
    """基础HTTP响应数据格式"""

    code: HttpCode = HttpCode.SUCCESS  # 给他一个默认值Success
    message: str = ""
    data: Any = {}
