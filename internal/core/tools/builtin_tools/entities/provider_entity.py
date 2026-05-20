from __future__ import annotations

import os.path
from typing import Any

from pydantic import BaseModel, Field

from internal.core.tools.builtin_tools.helper import dynamic_import
from .tool_entity import ToolEntity


class ProviderEntity(BaseModel):
    """服务提供商实体（来自 providers.yaml）"""

    name: str
    label: str | None = None
    description: str | None = None
    icon: str | None = None
    background: str | None = None
    category: str | None = None
    created_at: int = 0


class Provider(BaseModel):
    """
    Provider 聚合对象

    对齐
    - 构造后自动读取 providers/<name>/positions.yaml
    - 读取每个 tool 的 <tool>.yaml 填充 ToolEntity
    - 动态导入对应 tool 工厂函数填充 tool_func_map

    这里的目录结构为 builtin_tools/providers/<provider_name>/...
    """

    name: str
    position: int
    provider_entity: ProviderEntity

    tool_entity_map: dict[str, ToolEntity] = Field(default_factory=dict)
    tool_func_map: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._provider_init()

    class Config:
        protected_namespace = ()

    def get_tool(self, tool_name: str) -> Any:
        """根据名称获取工具（工厂函数）"""

        return self.tool_func_map.get(tool_name)

    def get_tool_entity(self, tool_name: str) -> Any:
        """根据名称获取工具实体"""

        return self.tool_entity_map.get(tool_name)

    def get_tool_entities(self) -> list[ToolEntity]:
        return list(self.tool_entity_map.values())

    def _provider_init(self):
        # 延迟导入，避免系统 python 未装依赖时 import 阶段直接炸
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "Missing dependency: PyYAML. Please install `PyYAML` to use builtin tools."
            ) from e

        # entities/provider_entity.py -> entities/ -> builtin_tools/ -> providers/
        current_path = os.path.abspath(__file__)
        entities_path = os.path.dirname(current_path)
        builtin_tools_path = os.path.dirname(entities_path)
        providers_path = os.path.join(builtin_tools_path, "providers")
        provider_path = os.path.join(providers_path, self.name)

        positions_yaml_path = os.path.join(provider_path, "positions.yaml")
        if not os.path.exists(positions_yaml_path):
            return

        with open(positions_yaml_path, encoding="utf-8") as f:
            positions_yaml_data = yaml.safe_load(f) or []

        for tool_name in positions_yaml_data:
            if not isinstance(tool_name, str) or tool_name.strip() == "":
                continue
            tool_name = tool_name.strip()

            tool_yaml_path = os.path.join(provider_path, f"{tool_name}.yaml")
            if os.path.exists(tool_yaml_path):
                with open(tool_yaml_path, encoding="utf-8") as f:
                    tool_yaml_data = yaml.safe_load(f) or {}
                try:
                    self.tool_entity_map[tool_name] = ToolEntity(**tool_yaml_data)
                except Exception:
                    # 工具 yaml 不合法不阻断
                    pass

            # 动态导入对应的工具工厂函数（函数名=tool_name）
            try:
                self.tool_func_map[tool_name] = dynamic_import(
                    f"internal.core.tools.builtin_tools.providers.{self.name}",
                    tool_name,
                )
            except Exception:
                # fallback: 直接导入 tool 模块
                try:
                    self.tool_func_map[tool_name] = dynamic_import(
                        f"internal.core.tools.builtin_tools.providers.{self.name}.{tool_name}",
                        tool_name,
                    )
                except Exception:
                    continue
