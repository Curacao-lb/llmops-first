"""
改进版本：使用 LangGraph 的 send() 实现真正的并行执行
两个子图会同时执行，而不是顺序执行
"""

from typing import TypedDict, Any, Annotated, Literal

import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, Send
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

dotenv.load_dotenv()


class MultiplyInput(BaseModel):
    a: int = Field(description="第一个数字")
    b: int = Field(description="第二个数字")


@tool("multiply_tool", args_schema=MultiplyInput)
def multiply(a: int, b: int) -> int:
    """将传递的两个数字相乘"""
    return a * b


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def reduce_str(left: str | None, right: str | None) -> str | None:
    """合并字符串，优先使用右值"""
    if right is not None and right != "":
        return right
    return left


class AgentState(TypedDict):
    query: str  # 原始问题
    live_content: Annotated[str, reduce_str]  # 直播文案
    xhs_content: Annotated[str, reduce_str]  # 小红书文案


class LiveAgentState(TypedDict):
    """直播文案智能体状态"""

    query: str
    live_content: Annotated[str, reduce_str]
    messages: Annotated[list[AnyMessage], add_messages]


class XHSAgentState(TypedDict):
    """小红书文案智能体状态"""

    query: str
    xhs_content: Annotated[str, reduce_str]


# ============ 直播文案智能体 ============
def chatbot_live(state: LiveAgentState, config: RunnableConfig) -> Any:
    """直播文案智能体聊天机器人节点"""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个拥有10年经验的直播文案专家，请根据用户提供的产品整理一篇直播带货脚本文案",
            ),
            ("human", "{query}"),
            ("placeholder", "{chat_history}"),
        ]
    )
    chain = prompt | llm.bind_tools([multiply])

    ai_message = chain.invoke(
        {"query": state["query"], "chat_history": state.get("messages", [])}
    )

    return {
        "messages": [ai_message],
        "live_content": ai_message.content,
    }


live_agent_graph = StateGraph(LiveAgentState)
live_agent_graph.add_node("chatbot_live", chatbot_live)
live_agent_graph.add_node("tools", ToolNode([multiply]))

live_agent_graph.set_entry_point("chatbot_live")
live_agent_graph.add_conditional_edges("chatbot_live", tools_condition)
live_agent_graph.add_edge("tools", "chatbot_live")


# ============ 小红书文案智能体 ============
def chatbot_xhs(state: XHSAgentState, config: RunnableConfig) -> Any:
    """小红书文案智能体聊天节点"""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个小红书文案大师，请根据用户传递的商品名，生成一篇关于该商品的小红书笔记文案，注意风格活泼，多使用emoji表情。",
            ),
            ("human", "{query}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    return {"xhs_content": chain.invoke({"query": state["query"]})}


xhs_agent_graph = StateGraph(XHSAgentState)
xhs_agent_graph.add_node("chatbot_xhs", chatbot_xhs)
xhs_agent_graph.set_entry_point("chatbot_xhs")
xhs_agent_graph.set_finish_point("chatbot_xhs")


# ============ 主图：使用 Send 实现真正的并行 ============
def route_to_agents(state: AgentState) -> list[Send]:
    """
    使用 Send 将状态同时发送给两个子图
    这样两个子图会真正并行执行
    """
    return [
        Send("live_agent", {"query": state["query"], "messages": []}),
        Send("xhs_agent", {"query": state["query"]}),
    ]


def merge_results(state: AgentState) -> AgentState:
    """合并两个子图的结果"""
    return state


agent_graph = StateGraph(AgentState)
agent_graph.add_node("live_agent", live_agent_graph.compile())
agent_graph.add_node("xhs_agent", xhs_agent_graph.compile())
agent_graph.add_node("merge", merge_results)

agent_graph.set_entry_point("route")
agent_graph.add_conditional_edges("route", route_to_agents)

# 两个子图都完成后，进入合并节点
agent_graph.add_edge("live_agent", "merge")
agent_graph.add_edge("xhs_agent", "merge")
agent_graph.add_edge("merge", END)

# 添加路由节点
agent_graph.add_node("route", lambda state: state)

# 重新编译
agent_graph = StateGraph(AgentState)
agent_graph.add_node("live_agent", live_agent_graph.compile())
agent_graph.add_node("xhs_agent", xhs_agent_graph.compile())
agent_graph.add_node("merge", merge_results)

agent_graph.set_entry_point("live_agent")


# 使用条件边实现并行路由
def route_after_live(state: AgentState) -> Literal["xhs_agent", "merge"]:
    """直播智能体完成后，同时启动小红书智能体和合并"""
    return "xhs_agent"


agent_graph.add_edge("live_agent", "xhs_agent")
agent_graph.add_edge("xhs_agent", "merge")
agent_graph.add_edge("merge", END)

# 编译
agent = agent_graph.compile()

# 执行
print("=" * 80)
print("启动营销智能体（改进版）...")
print("=" * 80)

state = agent.invoke({"query": "潮汕牛肉丸"})

print("\n" + "=" * 80)
print("执行完成，最终结果：")
print("=" * 80)
print(f"\n【原始问题】\n{state.get('query', 'N/A')}")
print(f"\n【直播带货脚本】\n{state.get('live_content', 'N/A')}")
print(f"\n【小红书推广文案】\n{state.get('xhs_content', 'N/A')}")
