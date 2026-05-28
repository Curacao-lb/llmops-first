from dataclasses import dataclass
from internal.exception import ValidateException, NotFoundException
from internal.core.tools.api_tools.entites import OpenAPISchema

from injector import inject
import json


@inject
@dataclass
class ApiToolService:
    """自定义API插件服务"""

    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str) -> OpenAPISchema:
        """解析传递的openapi_schema字符串,如果出错则抛出错误"""

        try:
            data = json.loads(openapi_schema_str.strip())
            if not isinstance(data, dict):
                raise
        except Exception as e:
            raise ValidateException("格式错误")
        return OpenAPISchema(**data)
