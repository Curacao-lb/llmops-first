import os
from dataclasses import dataclass
from typing import Any

import jwt
from injector import inject

from internal.exception import UnauthorizedException


@inject
@dataclass
class JwtService:
    """JWT服务"""

    @classmethod
    def generate_token(cls, payload: dict[str, Any]) -> str:
        """根据传递的载荷信息生成token信息"""
        secret_key = os.getenv("JWT_SECRET_KEY")
        # 使用jwt转化为access_token
        return jwt.encode(payload, secret_key, algorithm="HS256")

    @classmethod
    def parse_token(cls, token: str) -> dict[str, Any]:
        """解析传入的token信息得到载荷"""
        secret_key = os.getenv("JWT_SECRET_KEY")
        try:
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError as exc:
            raise UnauthorizedException("登陆凭证已过期请重新登录") from exc
        except jwt.InvalidTokenError as exc:
            raise UnauthorizedException("解析token错误，请重新登录") from exc
        except Exception as exc:
            raise UnauthorizedException(str(exc)) from exc
