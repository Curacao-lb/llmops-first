"""
Tavily Search Tool Implementation (Builtin Tool Provider Style)

对齐builtin_tools/providers 写法：
- 使用 Pydantic args_schema 描述“工具输入”(query)
- 通过工厂函数返回 LangChain BaseTool
- 使用 add_attribute("args_schema", ...) 在函数对象上挂载元信息，便于 YAML+importlib 动态加载
"""

from __future__ import annotations

from typing import Any, Type
import os

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

try:
    # 新版：官方独立包（避免 LangChainDeprecationWarning）
    from langchain_tavily import TavilySearch  # type: ignore
except Exception:  # pragma: no cover
    TavilySearch = None  # type: ignore

try:
    # 旧版兼容（仍可用，但会有弃用警告）
    from langchain_community.tools.tavily_search import TavilySearchResults  # type: ignore
except Exception:  # pragma: no cover
    TavilySearchResults = None  # type: ignore


def add_attribute(attr_name: str, attr_value: Any):
    """
    简单装饰器：给函数挂载属性。
    lingxi-core 中同名工具用于让加载器能从函数上读到 args_schema 等信息。
    """

    def decorator(func):
        setattr(func, attr_name, attr_value)
        return func

    return decorator


class TavilySearchArgsSchema(BaseModel):
    """Tavily 搜索参数(工具输入)"""

    query: str = Field(description="需要检索查询的语句。")


class TavilySearchTool(BaseTool):
    """
    Tavily 搜索工具(返回格式为可直接给 LLM 使用的文本)。

    说明：
    - api_key 不传则读取环境变量 TAVILY_API_KEY
    - include_answer/include_raw_content/include_images 等为工具配置(实例化参数)，不属于工具输入
    """

    name: str = "tavily_search"
    description: str = (
        "当你需要搜索互联网上的内容时，可以使用该工具。输入为一个查询语句。"
    )
    args_schema: Type[BaseModel] = TavilySearchArgsSchema

    api_key: str | None = None
    max_results: int | None = 5
    search_depth: str | None = "basic"  # basic | advanced
    include_answer: bool | None = True
    include_raw_content: bool | None = False
    include_images: bool | None = False

    def _run(self, *args: Any, **kwargs: Any) -> str:
        query = (kwargs.get("query") or "").strip()
        if query == "":
            return "用户搜索内容为空"

        api_key = self.api_key or os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Tavily API Key 未配置，请设置环境变量 TAVILY_API_KEY 或在工具参数中配置 api_key"

        try:
            max_results = int(self.max_results or 5)
            search_depth = self.search_depth or "basic"
            include_answer = bool(self.include_answer)
            include_raw_content = bool(self.include_raw_content)
            include_images = bool(self.include_images)

            raw = None

            if TavilySearch is not None:
                # langchain-tavily: TavilySearch
                tool = TavilySearch(
                    api_key=api_key,
                    max_results=max_results,
                    search_depth=search_depth,
                    include_answer=include_answer,
                    include_raw_content=include_raw_content,
                    include_images=include_images,
                )
                # 不同版本可能接受 dict 或 str，这里做兼容
                try:
                    raw = tool.invoke({"query": query})
                except Exception:
                    raw = tool.invoke(query)
            elif TavilySearchResults is not None:
                # 兼容旧实现
                tool = TavilySearchResults(
                    api_key=api_key,
                    max_results=max_results,
                    search_depth=search_depth,
                    include_answer=include_answer,
                    include_raw_content=include_raw_content,
                    include_images=include_images,
                )
                raw = tool.invoke({"query": query})
            else:
                return "Tavily 依赖未安装：请安装 `langchain-tavily`（推荐）或 `langchain-community`。"

            return self._format_raw(raw)
        except Exception as e:
            return f"获取 {query} 信息失败: {str(e)}"

    @staticmethod
    def _format_raw(raw: Any) -> str:
        """
        将 Tavily 输出规整为可被 LLM 直接消费的文本。

        兼容两类返回：
        - list[dict]：[{title,url,content,score,...}, ...]
        - dict：{answer: str, results: [...] } 或其他结构
        """
        if raw is None:
            return "未找到相关结果。"

        if isinstance(raw, str):
            return raw.strip() or "未找到相关结果。"

        answer: str | None = None
        results: Any = raw

        if isinstance(raw, dict):
            answer = raw.get("answer") if isinstance(raw.get("answer"), str) else None
            if "results" in raw:
                results = raw.get("results")

        if not isinstance(results, list) or len(results) == 0:
            prefix = (answer.strip() + "\n\n") if answer and answer.strip() else ""
            return prefix + "未找到相关结果。"

        parts: list[str] = []
        if answer and answer.strip():
            parts.append(f"答案摘要: {answer.strip()}")

        for idx, item in enumerate(results, start=1):
            if not isinstance(item, dict):
                continue
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            content = (item.get("content") or item.get("snippet") or "").strip()
            score = item.get("score")

            block = [f"引用: {idx}"]
            if title:
                block.append(f"标题: {title}")
            if url:
                block.append(f"URL: {url}")
            if content:
                block.append(f"摘要: {content}")
            if score is not None:
                block.append(f"相关性: {score}")
            parts.append("\n".join(block))

        return "\n\n".join(parts).strip() or "未找到相关结果。"


@add_attribute("args_schema", TavilySearchArgsSchema)
def tavily_search(**kwargs) -> BaseTool:
    """
    Tavily 搜索(工厂函数)
    加载器会从该函数对象上读取 args_schema 等元信息。
    """

    return TavilySearchTool(**kwargs)


__all__ = ["tavily_search", "TavilySearchTool", "TavilySearchArgsSchema"]
