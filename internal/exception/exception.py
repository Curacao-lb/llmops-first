from pkg.response import HttpCode
from typing import Any


class CustomException(Exception):
    """基础自定义异常信息"""

    def __init__(self, message: str = "", data: Any = None):
        super().__init__()
        self.code: HttpCode = HttpCode.FAIL
        self.message: str = message if message else ""
        self.data: Any = data if data is not None else {}


class FailException(CustomException):
    """通用失败异常"""

    def __init__(self, message: str = "", data: Any = None):
        super().__init__(message, data)
        self.code = HttpCode.FAIL


class NotFoundException(CustomException):
    """资源未找到异常"""

    def __init__(self, message: str = "", data: Any = None):
        super().__init__(message, data)
        self.code = HttpCode.NOT_FOUND


class UnauthorizedException(CustomException):
    """未授权异常"""

    def __init__(self, message: str = "", data: Any = None):
        super().__init__(message, data)
        self.code = HttpCode.UNAUTHORIZED


class ForbiddenException(CustomException):
    """无权限异常"""

    def __init__(self, message: str = "", data: Any = None):
        super().__init__(message, data)
        self.code = HttpCode.FORBIDDEN


class ValidateException(CustomException):
    """参数验证异常"""

    def __init__(self, message: str = "", data: Any = None):
        super().__init__(message, data)
        self.code = HttpCode.VALIDATE_ERROR
