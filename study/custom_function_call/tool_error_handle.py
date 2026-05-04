from typing import Any

import dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


dotenv.load_dotenv()


@tool
def division(a: int, b: int) -> float:
    """将a除以b，返回计算结果"""

    return a / b


def try_except_tool(tool_args: dict, config: RunnableConfig) -> Any:
    try:
        return division.invoke(tool_args, config)
    except Exception as e:
        return f"调用工具时使用以下参数:\n\n{tool_args}\n\n引发了以下错误:\n\n{type(e)}: {e}"


def get_tool_args(msg) -> dict:
    if not msg.tool_calls:
        raise ValueError(f"模型没有返回工具调用信息，模型输出内容为：{msg.content}")
    return msg.tool_calls[0]["args"]


llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
llm_with_tools = llm.bind_tools(
    [division],
    tool_choice={"type": "function", "function": {"name": "division"}},
)

chain = llm_with_tools | get_tool_args | try_except_tool

print(chain.invoke("请计算 10 除以 0"))
