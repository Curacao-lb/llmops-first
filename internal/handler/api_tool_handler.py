from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from flask import request
from flask_login import current_user, login_required
from injector import inject

from internal.model import Account
from internal.schema.api_tool_schema import (
    CreateApiToolReq,
    GetApiToolProviderResp,
    GetApiToolProvidersWithPageReq,
    GetApiToolProvidersWithPageResp,
    GetApiToolResp,
    UpdateApiToolProviderReq,
    ValidateOpenAPISchema,
)
from internal.service import ApiToolService
from pkg.paginator import PageModel
from pkg.response import success_json, success_message, validate_error_json


@inject
@dataclass
class ApiToolHandler:
    """自定义API插件处理器"""

    api_tool_service: ApiToolService

    @login_required
    def create_api_tool_provider(self):
        """创建自定义API工具"""
        # 1.提取请求的数据并且校验
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 2. 调用服务创建API工具
        self.api_tool_service.create_api_tool_provider(
            req, account=cast(Account, current_user)
        )
        return success_message("创建成功")

    @login_required
    def validate_openapi_schema(self):
        """校验传递的openapi_schema字符串是否正确"""
        # 1. 提取前端的数据并校验
        req = ValidateOpenAPISchema()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2. 调用服务并解析传递的数据
        self.api_tool_service.parse_openapi_schema(cast(str, req.openapi_schema.data))
        return success_message("数据校验成功")

    @login_required
    def get_api_tool_provider(self, provider_id: UUID):
        """根据provider_id获取工具提供者"""
        api_tool_provider = self.api_tool_service.get_api_tool_provider(
            provider_id, account=cast(Account, current_user)
        )

        resp = GetApiToolProviderResp()
        return success_json(resp.dump(api_tool_provider))

    @login_required
    def get_api_tool_providers_with_page(self):
        """获取API工具提供者列表信息,该接口支持分页"""
        req = GetApiToolProvidersWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)
        api_tool_providers, paginator = (
            self.api_tool_service.get_api_tool_providers_with_page(
                req, account=cast(Account, current_user)
            )
        )
        resp = GetApiToolProvidersWithPageResp(many=True)
        return success_json(
            PageModel(
                list=cast(list[Any], resp.dump(api_tool_providers)),
                paginator=paginator,
            )
        )

    @login_required
    def get_api_tool(self, provider_id: UUID, tool_name: str):
        """根据传递的provider_id加tool_name获取工具的详情信息"""
        api_tool = self.api_tool_service.get_api_tool(
            provider_id, tool_name, account=cast(Account, current_user)
        )
        resp = GetApiToolResp()
        return success_json(resp.dump(api_tool))

    @login_required
    def delete_api_tool_provider(self, provider_id: UUID):
        """根据传递的provider_id删除对应的工具提供者信息"""
        self.api_tool_service.delete_api_tool_provider(
            provider_id, account=cast(Account, current_user)
        )
        return success_message("删除自定义API成功")

    @login_required
    def update_api_tool_provider(self, provider_id: UUID):
        """更新自定义API工具提供者信息"""

        req = UpdateApiToolProviderReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_tool_service.update_api_tool_provider(
            provider_id, req, account=cast(Account, current_user)
        )
        return success_message("更新成功")
