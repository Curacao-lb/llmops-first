from dataclasses import dataclass
from typing import cast
from uuid import UUID

from flask import Request
from injector import inject

from internal.exception import UnauthorizedException
from internal.model import Account
from internal.service import AccountService, JwtService
from internal.service.api_key_service import ApiKeyService


@inject
@dataclass
class Middleware:
    """应用中间件, 可以重写request_loader与unauthorized_hanlder"""

    jwt_service: JwtService
    account_service: AccountService
    api_key_service: ApiKeyService

    def request_loader(self, request: Request) -> Account | None:
        """登录管理器的请求加载器"""
        # 1. 单独为llmops路由蓝图创建请求加载器
        if request.blueprint == "llmops":
            # 2.提取请求头headers中的信息
            access_token = self._validate_credential(request)

            # 5.解析token信息得到用户信息并返回
            payload = self.jwt_service.parse_token(access_token)
            account_id = payload.get("sub")
            if not account_id:
                raise UnauthorizedException("授权失败，请重新登录")
            return self.account_service.get_account(UUID(account_id))
        elif request.blueprint == "openapi":
            # 校验获取 api_key
            api_key = self._validate_credential(request)
            # 解析得到API密钥记录
            api_key_record = self.api_key_service.get_api_by_credential(api_key)

            # 判断API密钥记录是否存在，如果不存在则抛出错误
            if not api_key_record or not cast(bool, api_key_record.is_active):
                raise UnauthorizedException("该密钥不存在或未激活")
            # 获取密钥信息并返回
            return api_key_record.account
        else:
            return None

    @classmethod
    def _validate_credential(cls, request: Request) -> str:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise UnauthorizedException("未授权，请登录后尝试")

        # 3.请求信息中没有空格分隔符，则验证失败，Authorization: Bearer access_token
        if " " not in auth_header:
            raise UnauthorizedException("授权失败并且验证格式失败")

        # 4.分割授权信息，必须符合Bearer access_token
        auth_schema, credential = auth_header.split(None, 1)
        if auth_schema.lower() != "bearer":
            raise UnauthorizedException("授权失败，认证格式错误，请重试")

        return credential
