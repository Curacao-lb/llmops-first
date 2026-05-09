import json
import dotenv
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field
from langchain_community.tools.openai_dalle_image_generation import (
    OpenAIDALLEImageGenerationTool,
)
from typing import TypedDict, Annotated, Any, Literal
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.messages import ToolMessage


dotenv.load_dotenv()


class TavilySearchArgsSchema(BaseModel):
    query: str = Field(description="执行实时搜索的查询语句")


# 1.定义工具与工具列表
tavily_search = TavilySearch(
    name="tavily_search",
    description=(
        "一个用于实时互联网信息搜索的工具。"
        "当你需要查询新闻、实时事件、互联网资料、最新信息或普通网页内容时，可以使用该工具。"
        "该工具的输入是搜索查询语句。"
    ),
    args_schema=TavilySearchArgsSchema,
    max_results=5,
    topic="general",
)


class DallEArgsSchema(BaseModel):
    query: str = Field(description="输入应该是生成图像的文本提示{prompt}")


dalle = OpenAIDALLEImageGenerationTool(
    api_wrapper=DallEAPIWrapper(model="dall-e-3"),
    name="openai_dalle",
    args_schema=DallEArgsSchema,
)

tools = [tavily_search, dalle]
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)


class GraphState(TypedDict):
    """图结构的状态数据"""

    messages: Annotated[list[BaseMessage], add_messages]


def chatbot(state: GraphState, config: RunnableConfig | None = None) -> Any:
    """聊天机器人节点,使用大语言模型根据传递的消息列表生成内容"""
    ai_messages = llm_with_tools.invoke(state["messages"], config=config)
    return {"messages": [ai_messages]}


def tool_executor(state: GraphState, config: RunnableConfig | None = None) -> Any:
    """工具执行节点"""
    # 1.第一步就是提取数据状态中的tool_calls
    tool_calls = state["messages"][-1].tool_calls
    # 2.第二步根据找到的tool_calls去获取需要执行什么工具。
    tools_by_name = {tool.name: tool for tool in tools}  # 转换为字典
    # 3.第三步，执行工具得到对应的结果。
    messages = []
    for call in tool_calls:
        tool = tools_by_name[call["name"]]
        messages.append(
            ToolMessage(
                content=json.dumps(tool.invoke(call["args"])),
                name=call["name"],
                tool_call_id=call["id"],
            )
        )
    # 4.第四步，将工具的执行结果作为工具消息更新到数据状态机中。
    return {"messages": messages}


def route(
    state: GraphState, config: RunnableConfig | None = None
) -> Literal["tool_executor", "llm"]:
    """通过路由来去检测下后续的返回节点是什么。 返回的节点有两个，一个是工具执行，一个是继续对话。"""
    ai_message = state["messages"][-1]
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tool_executor"
    return "llm"


graph_builder = StateGraph(GraphState)

graph_builder.add_node("llm", chatbot)
graph_builder.add_node("tool_executor", tool_executor)

graph_builder.set_entry_point("llm")
graph_builder.add_conditional_edges(
    "llm", route, {"tool_executor": "tool_executor", "llm": END}
)
graph_builder.add_edge("tool_executor", "llm")

graph = graph_builder.compile()

state = graph.invoke(
    {"messages": [("human", "你好，2026年蚌埠半程马拉松的前三名成绩是多少？")]}
)

for message in state["messages"]:
    print("消息类型:", message.type)
    if hasattr(message, "tool_calls") and len(message.tool_calls) > 0:
        print("工具调用参数:", message.tool_calls)
    print("消息内容:", message.content)
    print("===================")
