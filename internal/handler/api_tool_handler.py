from dataclasses import dataclass
from internal.schema.api_tool_schema import ValidateOpenAPISchema
from pkg.response import validate_error_json, success_message
from internal.service import ApiToolService

from injector import inject


@inject
@dataclass
class ApiToolHandler:
    """自定义API插件处理器"""

    api_tool_service = ApiToolService()

    def validate_openapi_schema(self):
        """校验传递的openapi_schema字符串是否正确"""
        # 1. 提取前端的数据并校验
        req = ValidateOpenAPISchema()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2. 调用服务并解析传递的数据
        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)
        return success_message("数据校验成功")
