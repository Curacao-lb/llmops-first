from injector import inject
from dataclasses import dataclass, field
from typing import Any, Type

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.core.tools.builtin_tools.categories import BuiltinCategoryManager
from pydantic import BaseModel
from internal.exception import NotFoundException


@inject
@dataclass
class BuiltinToolService:
    """内置工具服务"""

    builtin_provider_manager: BuiltinProviderManager
    # args_schema 解析缓存：同一个 schema 类只解析一次，适合 get_builtin_tools 被频繁调用的场景
    _args_schema_inputs_cache: dict[Type[BaseModel], list[dict[str, Any]]] = field(
        default_factory=dict, init=False, repr=False
    )

    def _args_schema_to_inputs(
        self, schema_cls: Type[BaseModel]
    ) -> list[dict[str, Any]]:
        cached = self._args_schema_inputs_cache.get(schema_cls)
        if cached is not None:
            # 返回拷贝，避免外部误改缓存内容
            return [dict(x) for x in cached]

        inputs: list[dict[str, Any]] = []

        # 优先按 Pydantic v2 处理：BaseModel.model_fields -> dict[str, FieldInfo]
        v2_fields = getattr(schema_cls, "model_fields", None)
        if v2_fields:
            for field_name, field_info in v2_fields.items():
                annotation = getattr(field_info, "annotation", None)
                description = getattr(field_info, "description", None) or ""

                # v2 required 判断：优先 is_required()，否则用 default 是否为 undefined 兜底
                required = False
                if hasattr(field_info, "is_required") and callable(
                    field_info.is_required
                ):
                    required = bool(field_info.is_required())
                else:
                    default_val = getattr(field_info, "default", None)
                    undefined_type = type(
                        getattr(
                            __import__("pydantic_core"), "PydanticUndefined", object()
                        )
                    )
                    required = isinstance(default_val, undefined_type)

                type_name = "str"
                if annotation is not None:
                    type_name = getattr(annotation, "__name__", str(annotation))

                inputs.append(
                    {
                        "name": field_name,
                        "description": description,
                        "required": required,
                        "type": type_name,
                    }
                )
        else:
            # Pydantic v1: BaseModel.__fields__ -> dict[str, ModelField]
            v1_fields = getattr(schema_cls, "__fields__", None) or {}
            for field_name, model_field in v1_fields.items():
                outer_type = getattr(model_field, "outer_type_", None)
                inputs.append(
                    {
                        "name": field_name,
                        "description": (model_field.field_info.description or ""),
                        "required": bool(model_field.required),
                        "type": (
                            getattr(outer_type, "__name__", str(outer_type))
                            if outer_type is not None
                            else "str"
                        ),
                    }
                )

        self._args_schema_inputs_cache[schema_cls] = [dict(x) for x in inputs]
        return inputs

    def get_builtin_tools(self) -> list:
        """获取LLMOps项目中的所有内置提供商+工具对应的信息"""
        # 1.获取所有的提供商
        providers = self.builtin_provider_manager.get_providers()
        # 2.遍历所有的提供商并提取工具信息
        builtin_tools = []
        for provider in providers:
            provider_entity = provider.provider_entity
            builtin_tool = {
                **provider_entity.model_dump(exclude=["icon"]),
                "tools": [],
            }
            # 2.1循环遍历提取提供者的所有工具实体
            for tool_entity in provider.get_tool_entities():
                # 2.2 构建工具实体信息
                tool_dict = {**tool_entity.model_dump(), "inputs": []}
                # 2.3 从提供者中获取工具函数
                tool = provider.get_tool(tool_entity.name)
                # 2.4 检测下工具是否具有 args_schema 这个属性，并且是BaseModel的子类
                if (
                    tool is not None
                    and hasattr(tool, "args_schema")
                    and issubclass(tool.args_schema, BaseModel)
                ):
                    tool_dict["inputs"] = self._args_schema_to_inputs(tool.args_schema)
                builtin_tool["tools"].append(tool_dict)
            builtin_tools.append(builtin_tool)
        return builtin_tools
        # 3.除了工具实体，还需要提取工具的inputs代表大语言模型的输入参数信息
        # 4.组装提取所有信息为list，并返回

    def get_provider_tool(self, provider_name: str, tool_name: str) -> dict:
        """根据传递的提供者名字+工具名字获取指定工具信息"""
        # 1.获取内置的提供商
        provider = self.builtin_provider_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"该提供商{provider_name}不存在")

        # 2.获取该提供商下对应的工具
        tool_entity = provider.get_tool_entity(tool_name)
        if tool_entity is None:
            raise NotFoundException(f"该工具{tool_name}不存在")

        # 3.组装提供商和工具实体信息
        provider_entity = provider.provider_entity
        tool = provider.get_tool(tool_name)

        inputs: list[dict[str, Any]] = []
        if (
            tool is not None
            and hasattr(tool, "args_schema")
            and issubclass(tool.args_schema, BaseModel)
        ):
            inputs = self._args_schema_to_inputs(tool.args_schema)

        builtin_tool = {
            "provider": {**provider_entity.model_dump(exclude=["icon", "created_at"])},
            **tool_entity.model_dump(),
            "created_at": provider_entity.created_at,
            "inputs": inputs,
        }

        return builtin_tool

    def get_provider_icon(self, provider_name: str) -> tuple[bytes, str]:
        """根据提供商名字获取对应的icon文件路径"""
        import os

        # 1.获取内置的提供商
        provider = self.builtin_provider_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"该提供商{provider_name}不存在")

        # 2.获取提供商的icon文件名
        provider_entity = provider.provider_entity
        if not provider_entity.icon:
            raise NotFoundException(f"该提供商{provider_name}未配置icon")

        # 3.拼接icon文件路径
        icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "core",
            "tools",
            "builtin_tools",
            "providers",
            provider_name,
            "_asset",
            provider_entity.icon,
        )
        if not os.path.exists(icon_path):
            raise NotFoundException(f"该提供商{provider_name}的icon文件不存在")

        # 4.读取icon文件内容并推断mimetype
        import mimetypes

        mimetype, _ = mimetypes.guess_type(icon_path)
        if mimetype is None:
            mimetype = "application/octet-stream"

        with open(icon_path, "rb") as f:
            icon_data = f.read()

        return icon_data, mimetype

    def get_categories(self) -> list[dict, Any]:
        """获取所有内置工具的分类列表信息"""
        # 1.从分类管理器获取分类映射
        builtin_category_manager = BuiltinCategoryManager()
        category_map = builtin_category_manager.get_category_map()

        # 2.组装分类列表
        categories = []
        for category_key, category_info in category_map.items():
            category_entity = category_info["entity"]
            categories.append(
                {
                    "category": category_entity.category,
                    "name": category_entity.name,
                    "icon": category_info["icon"],
                }
            )

        return categories
