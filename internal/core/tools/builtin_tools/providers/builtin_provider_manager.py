from __future__ import annotations

import os
from typing import Any, Optional

from pydantic import BaseModel, Field

from internal.core.tools.builtin_tools.entities import (
    ProviderEntity,
    Provider,
    ToolEntity,
)


try:
    from injector import inject, singleton  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    # 让模块在缺少 injector 依赖时也能被 import（例如系统 python 未装依赖）。
    def inject(obj):  # type: ignore
        return obj

    def singleton(obj):  # type: ignore
        return obj


@inject
@singleton
class BuiltinProviderManager(BaseModel):
    """
    工厂类

    目录约定：
    internal/core/tools/builtin_tools/
      entities/
      providers/
        providers.yaml
        <provider_name>/
          positions.yaml
          <tool_name>.yaml
          <tool_name>.py
    """

    provider_map: dict[str, Provider] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_provider_tool_map()

    def get_provider(self, provider_name: str) -> Optional[Provider]:
        return self.provider_map.get(provider_name)

    def get_providers(self) -> list[Provider]:
        return list(self.provider_map.values())

    def get_provider_entities(self) -> list[ProviderEntity]:
        return [p.provider_entity for p in self.provider_map.values()]

    def get_tool(self, provider_name: str, tool_name: str, **kwargs) -> Any:
        provider = self.get_provider(provider_name)
        if provider is None:
            return None
        # 返回 tool 工厂函数本身，由上层决定是否实例化/传参
        return provider.get_tool(tool_name)

    def get_tool_entity(
        self, provider_name: str, tool_name: str
    ) -> Optional[ToolEntity]:
        provider = self.get_provider(provider_name)
        if provider is None:
            return None
        return provider.get_tool_entity(tool_name)

    def _load_provider_tool_map(self) -> None:
        if self.provider_map:
            return
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "Missing dependency: PyYAML. Please install `PyYAML` to use BuiltinProviderManager."
            ) from e

        root_dir = os.path.dirname(os.path.abspath(__file__))
        providers_yaml_path = os.path.join(root_dir, "providers.yaml")
        if not os.path.exists(providers_yaml_path):
            return

        with open(providers_yaml_path, encoding="utf-8") as f:
            providers_yaml_data = yaml.safe_load(f) or []

        for idx, provider_data in enumerate(providers_yaml_data):
            provider_entity = ProviderEntity(**(provider_data or {}))
            provider = Provider(
                name=provider_entity.name,
                position=idx + 1,
                provider_entity=provider_entity,
            )
            self.provider_map[provider_entity.name] = provider
