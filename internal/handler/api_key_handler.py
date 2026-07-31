from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from flask import request
from flask_login import current_user, login_required
from injector import inject

from internal.model.account import Account
from internal.schema.api_key_schema import (
    CreateApiKeyReq,
    GetApiKeysWithPageResp,
    UpdateApiKeyIsActiveReq,
    UpdateApiKeyReq,
)
from internal.service import ApiKeyService
from pkg.paginator import PageModel, PaginatorReq
from pkg.response import success_json, success_message, validate_error_json


@inject
@dataclass
class ApiKeyHandler:
    """API 密钥处理器"""

    api_key_service: ApiKeyService

    @login_required
    def create_api_key(self):
        """创建API密钥"""
        req = CreateApiKeyReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_key_service.create_api_key(req, cast(Account, current_user))

        return success_message("创建API密钥成功")

    @login_required
    def delete_api_key(self, api_key_id: UUID):
        """根据传递的id删除API密钥"""
        self.api_key_service.delete_api_key(api_key_id, cast(Account, current_user))
        return success_message("删除API密钥成功")

    @login_required
    def update_api_key(self, api_key_id: UUID):
        """根据传递的信息更新API密钥"""
        req = UpdateApiKeyReq()
        # print(req.data)
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_key_service.update_api_key(
            api_key_id, cast(Account, current_user), **req.data
        )

        return success_message("更新API密钥成功")

    @login_required
    def update_api_key_is_active(self, api_key_id: UUID):
        """根据传递的信息更新API密钥激活状态"""
        req = UpdateApiKeyIsActiveReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_key_service.update_api_key(
            api_key_id, cast(Account, current_user), **req.data
        )

        return success_message("更新API密钥激活状态成功")

    @login_required
    def get_api_keys_with_page(self):
        """获取当前登录账号的API密钥分页列表信息"""
        req = PaginatorReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        api_keys, paginator = self.api_key_service.get_api_keys_with_page(
            req, cast(Account, current_user)
        )

        resp = GetApiKeysWithPageResp(many=True)

        return success_json(
            PageModel(list=cast(list[Any], resp.dump(api_keys)), paginator=paginator)
        )
