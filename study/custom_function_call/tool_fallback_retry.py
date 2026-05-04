from typing import Any

import dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


dotenv.load_dotenv()


@tool
def complex_tool(int_arg: int, float_arg: float, dict_arg: dict) -> int:
    """使用复杂工具进行复杂计算操作"""

    return int(int_arg * float_arg)


def get_first_tool_args(msg) -> dict:
    return msg.tool_calls[0]["args"]


def try_except_tool(tool_args: dict, config: RunnableConfig) -> Any:
    try:
        return complex_tool.invoke(tool_args, config)
    except Exception as e:
        return {
            "tool_args": tool_args,
            "error": f"{type(e).__name__}: {e}",
        }


def retry_with_error(inputs: dict) -> Any:
    """携带错误信息，让LLM重新生成工具调用参数并再次执行工具。"""

    first_result = inputs["first_result"]
    if not isinstance(first_result, dict) or "error" not in first_result:
        return first_result

    retry_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(
        [complex_tool],
        tool_choice="complex_tool",
    )

    msg = retry_llm.invoke(
        [
            SystemMessage(
                content=(
                    "你需要根据用户问题生成complex_tool的正确调用参数。"
                    "上一次工具调用失败了，请根据错误信息修正参数。"
                )
            ),
            HumanMessage(
                content=(
                    f"用户原始问题：{inputs['query']}\n"
                    f"上一次调用参数：{first_result['tool_args']}\n"
                    f"上一次错误信息：{first_result['error']}\n"
                    "请重新生成工具调用。"
                )
            ),
        ]
    )
    return complex_tool.invoke(get_first_tool_args(msg))


# 1.创建大语言模型并绑定工具
llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0).bind_tools([complex_tool])
better_llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(
    [complex_tool],
    tool_choice="complex_tool",
)


# 2.创建链并执行工具，出错时回退到更好的模型
better_chain = better_llm | get_first_tool_args | complex_tool
chain = (llm | get_first_tool_args | complex_tool).with_fallbacks([better_chain])


# 3.创建携带错误信息的重试链
retry_chain = {
    "query": RunnableLambda(lambda query: query),
    "first_result": llm | get_first_tool_args | RunnableLambda(try_except_tool),
} | RunnableLambda(retry_with_error)


print("回退调用结果：", chain.invoke("使用复杂工具，对应参数为5和2.1"))
print("重试调用结果：", retry_chain.invoke("使用复杂工具，对应参数为5和2.1"))
