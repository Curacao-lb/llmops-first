from dataclasses import dataclass
from internal.schema.api_tool_schema import ValidateOpenAPISchema, CreateApiToolReq
from pkg.response import validate_error_json, success_message
from internal.service import ApiToolService

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
