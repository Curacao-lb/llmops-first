from .http_code import HttpCode
from typing import Any
from dataclasses import field, dataclass
from flask import jsonify


@dataclass
class Response:
    """基础HTTP响应数据格式"""

    code: HttpCode = HttpCode.SUCCESS  # 给他一个默认值Success
    message: str = ""
    # 通过默认的工厂函数来去创建一个空字典
    data: Any = field(default_factory=dict)


def json(data: Response = None):
    """基础的响应接口"""
    return jsonify(data), 200


def success_json(data: Response = None):
    """成功的数据响应接口"""
    return json(Response(code=HttpCode.SUCCESS, data=data, message=""))


def fail_json(data: Response = None):
    """失败的数据响应接口"""
    return json(Response(code=HttpCode.FAIL, data=data, message=""))


def validate_error_json(errors: Response = None):
    """验证错误的数据响应接口"""
    # 获取 errors 字典的第一个 key（第一个出错的字段名）

    first_key = next(iter(errors))
    # 获取该字段的第一条错误信息
    # errors 结构类似: {"username": ["不能为空", "长度不够"], "email": ["格式错误"]}
    if first_key is not None:
        msg = errors.get(first_key)[0]
    else:
        msg = ""
    # 返回统一格式的 JSON 响应，包含错误码、完整错误数据和第一条错误消息
    return json(Response(code=HttpCode.VALIDATE_ERROR, data=errors, message=msg))


# 有些时候我们只需要返回状态码和消息，并不需要返回数据
def success_json_no_data():
    """成功的数据响应接口"""
    return json(Response(code=HttpCode.SUCCESS, message=""))


# 封装message函数
def message(code: HttpCode, message: str = ""):
    """基础的消息响应，固定返回消息提示，数据固定为空字典"""
    return json(Response(code=code, message=message, data={}))


def success_message(message: str = ""):
    """成功的消息响应"""
    return message(HttpCode.SUCCESS, message=message)


def fail_message(message: str = ""):
    """失败的消息响应"""
    return message(HttpCode.FAIL, message=message)


def not_found_message(message: str = ""):
    """未找到的消息响应"""
    return message(HttpCode.NOT_FOUND, message=message)


def unauthorized_message(message: str = ""):
    """未授权的消息响应"""
    return message(HttpCode.UNAUTHORIZED, message=message)


def forbidden_message(message: str = ""):
    """禁止访问的消息响应"""
    return message(HttpCode.FORBIDDEN, message=message)


def server_error_message(message: str = ""):
    """服务器错误的消息响应"""
    return message(HttpCode.SERVER_ERROR, message=message)
