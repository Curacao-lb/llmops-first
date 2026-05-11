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
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper

dotenv.load_dotenv()


class TavilySearchArgsSchema(BaseModel):
    query: str = Field(description="执行实时搜索的查询语句")


# 1. 定义工具与工具列表
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
    """聊天机器人节点，使用大语言模型根据传递的消息列表生成内容"""
    ai_message = llm_with_tools.invoke(state["messages"], config=config)
    return {"messages": [ai_message]}


def tool_executor(state: GraphState, config: RunnableConfig | None = None) -> Any:
    """工具执行节点"""
    # 1. 提取数据状态中的 tool_calls
    tool_calls = state["messages"][-1].tool_calls
    # 2. 根据 tool_calls 找到对应工具
    tools_by_name = {tool.name: tool for tool in tools}
    # 3. 执行工具并收集结果
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
    # 4. 将工具执行结果更新到状态中
    return {"messages": messages}


def route(
    state: GraphState, config: RunnableConfig | None = None
) -> Literal["tool_executor", "__end__"]:
    """路由函数：检测是否需要调用工具"""
    ai_message = state["messages"][-1]
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tool_executor"
    return "__end__"


# 2. 构建图结构
graph_builder = StateGraph(GraphState)

graph_builder.add_node("llm", chatbot)
graph_builder.add_node("tool_executor", tool_executor)

graph_builder.set_entry_point("llm")
graph_builder.add_conditional_edges(
    "llm", route, {"tool_executor": "tool_executor", "__end__": END}
)
graph_builder.add_edge("tool_executor", "llm")

# 3. 使用 MemorySaver 作为 checkpointer，并设置 interrupt_before 前置断点
#    在执行 tool_executor 节点之前暂停，等待人类确认
memory = MemorySaver()
graph = graph_builder.compile(
    checkpointer=memory,
    interrupt_before=["tool_executor"],  # 前置断点：在工具执行前中断
)

# 4. 配置 thread_id，MemorySaver 需要通过 thread_id 来持久化状态
config = {"configurable": {"thread_id": "human_in_loop_001"}}

# 5. 第一次调用图，LLM 决定调用工具后会在 tool_executor 前暂停
print("=" * 60)
print("启动图执行，等待 LLM 决策...")
print("=" * 60)

state = graph.invoke(
    {"messages": [("human", "你好，2026年蚌埠半程马拉松的前三名成绩是多少？")]},
    config=config,
)

# 6. 获取人类的提示：检查是否存在待执行的工具调用
if (
    hasattr(state["messages"][-1], "tool_calls")
    and len(state["messages"][-1].tool_calls) > 0
):
    tool_calls = state["messages"][-1].tool_calls
    print("准备调用工具：", tool_calls)
    human_input = input("如需调用工具请回复yes，否则回复no: ")
    if human_input.lower() == "yes":
        # 7. 人类确认后，传入 None 继续执行（从断点处恢复）
        final_state = graph.invoke(None, config)
        print("\n" + "=" * 60)
        print("执行完成，输出所有消息：")
        print("=" * 60)
        for message in final_state["messages"]:
            print("消息类型:", message.type)
            if hasattr(message, "tool_calls") and len(message.tool_calls) > 0:
                print("工具调用参数:", message.tool_calls)
            print("消息内容:", message.content)
            print("-------------------")
    else:
        print("程序执行结束")
else:
    # LLM 直接回答，无需工具调用
    print("\n" + "=" * 60)
    print("LLM 直接回答（无需工具调用）：")
    print("=" * 60)
    for message in state["messages"]:
        print("消息类型:", message.type)
        print("消息内容:", message.content)
        print("-------------------")
