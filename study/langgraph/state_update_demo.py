import json
import dotenv
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, Any, Literal
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, ToolMessage

dotenv.load_dotenv()


class TavilySearchArgsSchema(BaseModel):
    query: str = Field(description="执行实时搜索的查询语句")


# 1. 定义工具
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

tools = [tavily_search]
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)


class GraphState(TypedDict):
    """图结构的状态数据"""

    messages: Annotated[list[BaseMessage], add_messages]


def chatbot(state: GraphState) -> Any:
    """聊天机器人节点"""
    ai_message = llm_with_tools.invoke(state["messages"])
    return {"messages": [ai_message]}


def tool_executor(state: GraphState) -> Any:
    """工具执行节点"""
    tool_calls = state["messages"][-1].tool_calls
    tools_by_name = {tool.name: tool for tool in tools}
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
    return {"messages": messages}


def route(state: GraphState) -> Literal["tool_executor", "__end__"]:
    """路由函数"""
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

# 3. 使用 MemorySaver 和 interrupt_after 后置断点
#    在工具执行后暂停，允许我们修改工具返回的结果
memory = MemorySaver()
graph = graph_builder.compile(
    checkpointer=memory,
    interrupt_after=["tool_executor"],  # 后置断点：在工具执行后中断
)

# 4. 配置 thread_id
config = {"configurable": {"thread_id": "state_update_demo_001"}}

# 5. 第一次调用图，LLM 决策并执行工具，然后在 tool_executor 后暂停
print("=" * 80)
print("启动图执行，LLM 将调用工具搜索马拉松成绩...")
print("=" * 80)

state = graph.invoke(
    {"messages": [("human", "请帮我查询2024年北京半程马拉松的前三名成绩")]},
    config=config,
)

print("\n" + "=" * 80)
print("图已在工具执行后暂停，当前消息列表：")
print("=" * 80)
for i, msg in enumerate(state["messages"]):
    print(f"消息 {i} - 类型: {msg.type}")
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        print(f"  工具调用: {msg.tool_calls}")
    print(f"  内容: {msg.content[:100]}...")
    print()

# 6. 使用 get_state() 获取当前状态
print("=" * 80)
print("使用 get_state() 获取当前状态...")
print("=" * 80)
current_state = graph.get_state(config)
print(f"当前节点: {current_state.next}")
print(f"消息数量: {len(current_state.values['messages'])}")

# 7. 修改工具返回的结果
#    找到最后一条 ToolMessage，修改其内容为我们想要的数据
print("\n" + "=" * 80)
print("修改工具返回的结果...")
print("=" * 80)

# 获取当前状态的消息列表
messages = current_state.values["messages"]

# 找到最后一条 ToolMessage（工具返回的结果）
for i in range(len(messages) - 1, -1, -1):
    if isinstance(messages[i], ToolMessage):
        # 修改工具消息内容为我们自定义的马拉松成绩
        custom_result = {
            "results": [
                {
                    "title": "2024年北京半程马拉松成绩",
                    "content": "第一名：robin1，成绩 01:59:40；第二名：robin2，成绩 02:04:16；第三名：robin3，成绩 02:15:17",
                }
            ]
        }
        messages[i].content = json.dumps(custom_result)
        print(f"已修改消息 {i} 的内容为:")
        print(f"  {messages[i].content}")
        break

# 8. 使用 update_state() 将修改后的状态写回
print("\n" + "=" * 80)
print("使用 update_state() 将修改后的状态写回...")
print("=" * 80)

graph.update_state(
    config,
    {"messages": messages},
)
print("状态已更新")

# 9. 继续执行图，LLM 将基于修改后的工具结果生成回答
print("\n" + "=" * 80)
print("继续执行图，LLM 基于修改后的工具结果生成回答...")
print("=" * 80)

final_state = graph.invoke(None, config)

# 10. 输出最终结果
print("\n" + "=" * 80)
print("最终执行结果：")
print("=" * 80)
for i, msg in enumerate(final_state["messages"]):
    print(f"\n消息 {i} - 类型: {msg.type}")
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        print(f"工具调用: {msg.tool_calls}")
    print(f"内容:\n{msg.content}")
    print("-" * 80)
