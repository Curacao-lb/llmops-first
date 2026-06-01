from dataclasses import dataclass
from internal.schema.api_tool_schema import (
    ValidateOpenAPISchema,
    CreateApiToolReq,
    GetApiToolProviderResp,
    GetApiToolResp,
    GetApiToolProvidersWithPageReq,
    GetApiToolProvidersWithPageResp,
)
from pkg.response import validate_error_json, success_message
from internal.service import ApiToolService
from uuid import UUID
from pkg.response import success_json
from flask import request
from pkg.paginator import PageModel


from injector import inject


@inject
@dataclass
class ApiToolHandler:
    """自定义API插件处理器"""

    api_tool_service: ApiToolService

    def create_api_tool(self):
        """创建自定义API工具"""
        # 1.提取请求的数据并且校验
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 2. 调用服务创建API工具
        self.api_tool_service.create_api_tool(req)
        return success_message("创建成功")

    def validate_openapi_schema(self):
        """校验传递的openapi_schema字符串是否正确"""
        # 1. 提取前端的数据并校验
        req = ValidateOpenAPISchema()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2. 调用服务并解析传递的数据
        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)
        return success_message("数据校验成功")

    def get_api_tool_provider(self, provider_id: UUID):
        """根据provider_id获取工具提供者"""
        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id)

        resp = GetApiToolProviderResp()
        return success_json(resp.dump(api_tool_provider))

    def get_api_tool_providers_with_page(self):
        """获取API工具提供者列表信息,该接口支持分页"""
        req = GetApiToolProvidersWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)
        api_tool_providers, paginator = (
            self.api_tool_service.get_api_tool_providers_with_page(req)
        )
        resp = GetApiToolProvidersWithPageResp(many=True)
        return success_json(
            PageModel(list=resp.dump(api_tool_providers), paginator=paginator)
        )

    def get_api_tool(self, provider_id: UUID, tool_name: str):
        """根据传递的provider_id加tool_name获取工具的详情信息"""
        api_tool = self.api_tool_service.get_api_tool(provider_id, tool_name)
        resp = GetApiToolResp()
        return success_json(resp.dump(api_tool))

    def delete_api_tool_provider(self, provider_id: UUID):
        """根据传递的provider_id删除对应的工具提供者信息"""
        self.api_tool_service.delete_api_tool_provider(provider_id)
        return success_message("删除自定义API成功")
