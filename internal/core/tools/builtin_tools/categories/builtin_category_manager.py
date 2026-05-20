from __future__ import annotations

import os.path
from typing import Any

from pydantic import BaseModel, Field

from internal.core.tools.builtin_tools.entities import CategoryEntity


try:
    from injector import inject, singleton  # type: ignore
except ModuleNotFoundError:  # pragma: no cover

    def inject(obj):  # type: ignore
        return obj

    def singleton(obj):  # type: ignore
        return obj


@inject
@singleton
class BuiltinCategoryManager(BaseModel):
    """内置的工具分类管理器"""

    category_map: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_categories()

    def get_category_map(self) -> dict[str, Any]:
        return self.category_map

    def _init_categories(self):
        if self.category_map:
            return

        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "Missing dependency: PyYAML. Please install `PyYAML` to use builtin categories."
            ) from e

        current_path = os.path.abspath(__file__)
        category_path = os.path.dirname(current_path)
        category_yaml_path = os.path.join(category_path, "categories.yaml")
        with open(category_yaml_path, encoding="utf-8") as f:
            categories = yaml.safe_load(f) or []

        for category in categories:
            category_entity = CategoryEntity(**category)

            icon_path = os.path.join(category_path, "icons", category_entity.icon)
            if not os.path.exists(icon_path):
                raise FileNotFoundError(
                    f"该分类 {category_entity.category} 的 icon 未提供: {icon_path}"
                )

            with open(icon_path, encoding="utf-8") as f:
                icon = f.read()

            self.category_map[category_entity.category] = {
                "entity": category_entity,
                "icon": icon,
            }
