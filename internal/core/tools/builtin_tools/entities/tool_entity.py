from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolParamType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"
    PASSWORD = "password"


class ToolParam(BaseModel):
    """工具参数类型"""

    name: str
    label: str
    type: ToolParamType
    required: bool = False
    default: Optional[Any] = None
    min: Optional[float] = None
    max: Optional[float] = None
    options: list[dict[str, Any]] = Field(default_factory=list)


class ToolEntity(BaseModel):
    """工具实体类（来自 <tool_name>.yaml）"""

    name: str
    label: str
    description: str
    params: list[ToolParam] = Field(default_factory=list)

