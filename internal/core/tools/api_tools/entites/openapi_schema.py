from enum import Enum

from pydantic import BaseModel, Field, field_validator

from internal.exception import ValidateException


class ParameterType(str, Enum):
    """API参数的数据类型枚举"""

    STR: str = "str"
    INT: str = "int"
    FLOAT: str = "float"
    BOOL: str = "bool"


# 参数类型到Python原生类型的映射字典，用于运行时类型转换
ParameterTypeMap = {
    ParameterType.STR: str,
    ParameterType.INT: int,
    ParameterType.FLOAT: float,
    ParameterType.BOOL: bool,
}


class ParameterIn(str, Enum):
    """API参数的传递位置枚举，标识参数在HTTP请求中的位置"""

    PATH: str = "path"  # 路径参数，如 /users/{id}
    QUERY: str = "query"  # 查询参数，如 ?page=1
    HEADER: str = "header"  # 请求头参数
    COOKIE: str = "cookie"  # Cookie参数
    REQUEST_BODY: str = "request_body"  # 请求体参数


class OpenAPISchema(BaseModel):
    """OpenAPI规范的数据结构，用于解析和校验自定义API工具的schema配置"""

    server: str = Field(
        default="", validate_default=True, description="工具提供者的服务基础地址"
    )
    description: str = Field(
        default="", validate_default=True, description="工具提供者的描述信息"
    )
    paths: dict[str, dict] = Field(
        default_factory=dict,
        validate_default=True,
        description="工具提供者的路径参数字典",
    )

    @field_validator("server", mode="before")
    def validate_server(cls, server: str) -> str:
        """校验server字段，确保服务基础地址不为空"""
        if server is None or server == "":
            raise ValidateException("server不能为空")
        return server

    @field_validator("description", mode="before")
    def validate_description(cls, description: str) -> str:
        """校验description字段，确保描述信息不为空"""
        if description is None or description == "":
            raise ValidateException("description不能为空")
        return description

    @field_validator("paths", mode="before")
    def validate_paths(cls, paths: dict[str, dict]) -> dict[str, dict]:
        """校验并规范化paths字段。
        遍历所有路径和方法，提取接口信息，校验每个接口的operationId、description、
        parameters等字段的合法性，最终返回规范化后的路径字典。
        """
        # 1. 校验paths不能为空且类型必须为字典
        if not paths or not isinstance(paths, dict):
            raise ValidateException("paths不能为空，且类型必须为字典")

        # 2. 遍历所有路径，提取支持的HTTP方法(get/post)对应的接口信息
        methods = ["get", "post"]
        interfaces = []
        extra_paths = {}
        for path, path_item in paths.items():
            for method in methods:
                if method in path_item:
                    interfaces.append(
                        {
                            "path": path,
                            "method": method,
                            "operation": path_item[method],
                        }
                    )

        # 3. 逐个校验每个接口的字段合法性
        operation_ids = []
        for interface in interfaces:
            # 校验接口描述信息
            if not isinstance(interface["operation"].get("description"), str):
                raise ValidateException("description不能为空且需为字符串")
            # 校验接口唯一标识
            if not isinstance(interface["operation"].get("operationId"), str):
                raise ValidateException("operationId不能为空且需为字符串")
            # 校验参数列表格式
            if not isinstance(interface["operation"].get("parameters", []), list):
                raise ValidateException("parameters必须是列表或者为空")

            # 校验operationId在所有接口中必须唯一
            if interface["operation"]["operationId"] in operation_ids:
                raise ValidateException(
                    f"operationId: {interface["operation"]["operationId"]} 必须唯一"
                )

            operation_ids.append(interface["operation"]["operationId"])

            # 4. 逐个校验接口中每个参数的字段合法性:name/description/required/in/type
            for parameter in interface["operation"].get("parameters", []):
                if not isinstance(parameter.get("name"), str):
                    raise ValidateException("parameter.name参数必须为字符串且不为空")
                if not isinstance(parameter.get("description"), str):
                    raise ValidateException(
                        "parameter.description参数必须为字符串且不为空"
                    )
                if not isinstance(parameter.get("required"), bool):
                    raise ValidateException(
                        "parameter.required参数必须为布尔值且不为空"
                    )
                # 校验参数位置必须为ParameterIn枚举中的合法值
                if (
                    not isinstance(parameter.get("in"), str)
                    or parameter.get("in") not in ParameterIn.__members__.values()
                ):
                    raise ValidateException(
                        f"parameter.in参数必须为{'/'.join([item.value for item in ParameterIn])}"
                    )
                # 校验参数类型必须为ParameterType枚举中的合法值
                if (
                    not isinstance(parameter.get("type"), str)
                    or parameter.get("type") not in ParameterType.__members__.values()
                ):
                    raise ValidateException(
                        f"parameter.type参数必须为{'/'.join([item.value for item in ParameterType])}"
                    )

            # 5. 构建规范化后的路径字典，只保留必要字段
            extra_paths[interface["path"]] = {
                interface["method"]: {
                    "description": interface["operation"]["description"],
                    "operationId": interface["operation"]["operationId"],
                    "parameters": [
                        {
                            "name": parameter.get("name"),
                            "in": parameter.get("in"),
                            "description": parameter.get("description"),
                            "required": parameter.get("required"),
                            "type": parameter.get("type"),
                        }
                        for parameter in interface["operation"].get("parameters", [])
                    ],
                }
            }

        return extra_paths
