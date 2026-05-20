from __future__ import annotations

from pydantic import BaseModel, field_validator


class CategoryEntity(BaseModel):
    """分类实体"""

    category: str
    name: str
    icon: str

    @field_validator("icon")
    def check_icon_extension(cls, value: str):
        if not value.endswith(".svg"):
            raise ValueError("该分类的icon图标并不是.svg格式")
        return value
