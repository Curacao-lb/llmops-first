from datetime import datetime
from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel

from internal.lib.helper import add_attribute


class CurrentTimeSchema(BaseModel):
    pass


class CurrentTimeTool(BaseTool):
    # 一个用于获取当前时间的工具

    name: str = "current_time"
    description: str = "一个用于获取当前时间的工具"
    args_schema: Type[BaseModel] = CurrentTimeSchema

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """获取当前系统的时间并直接格式化后返回"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")


@add_attribute("args_schema", CurrentTimeSchema)
def current_time(**kwargs) -> BaseTool:
    return CurrentTimeTool()
