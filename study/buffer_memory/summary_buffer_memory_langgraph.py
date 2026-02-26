import sys
import dotenv
from typing import Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    RemoveMessage,
)
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver

dotenv.load_dotenv()


# 1. 定义状态（扩展 MessagesState 添加摘要字段）
class SummaryBufferState(MessagesState):
    """扩展的状态，包含摘要和消息"""

    summary: str = ""  # 历史对话摘要


# 2. 定义摘要生成节点
def should_generate_summary(state: SummaryBufferState) -> bool:
    """判断是否需要生成摘要（消息数超过6条）"""
    messages = state["messages"]
    # 过滤掉系统消息和摘要消息
    chat_messages = [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]
    return len(chat_messages) > 6


def generate_summary_node(state: SummaryBufferState) -> dict:
    """生成摘要节点"""
    messages = state["messages"]
    old_summary = state.get("summary", "")

    # 获取需要摘要的消息（最早的2条）
    chat_messages = [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]
    messages_to_summarize = chat_messages[:2]

    # 构建摘要提示
    messages_text = "\n".join(
        [f"{msg.__class__.__name__}: {msg.content}" for msg in messages_to_summarize]
    )

    summary_prompt = f"""你是一个强大的聊天机器人，请根据用户提供的谈话内容，总结摘要，并将其添加到先前提供的摘要中，返回一个新的摘要。
除了新摘要其他任何数据都不要生成。
如果用户的对话信息里有一些关键的信息，比方说姓名、爱好、性别、重要事件等等，这些全部都要包括在生成的摘要中。
摘要尽可能要还原用户的对话记录。

当前摘要：{old_summary if old_summary else "无"}

新的对话：
{messages_text}

请生成新摘要："""

    # 调用 LLM 生成摘要
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    response = llm.invoke([SystemMessage(content=summary_prompt)])
    new_summary = response.content

    print(f"\n[摘要生成中...]")
    print(f"[新摘要生成成功]: {new_summary}\n")

    # 标记要删除的消息
    messages_to_delete = [RemoveMessage(id=m.id) for m in messages_to_summarize]

    return {"summary": new_summary, "messages": messages_to_delete}


# 3. 定义聊天节点
def chatbot_node(state: SummaryBufferState) -> dict:
    """聊天机器人节点"""
    messages = state["messages"]
    summary = state.get("summary", "")

    # 构建完整的消息列表
    full_messages = []

    # 添加系统提示
    system_prompt = "你是OpenAI开发的聊天机器人，请根据对应的上下文回复用户问题。"
    if summary:
        system_prompt += f"\n\n历史对话摘要：{summary}"

    full_messages.append(SystemMessage(content=system_prompt))

    # 添加最近的对话历史
    chat_messages = [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]
    full_messages.extend(chat_messages)

    # 调用 LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", streaming=True)

    print("AI: ", end="", flush=True)
    sys.stdout.flush()

    ai_content = ""
    for chunk in llm.stream(full_messages):
        content = chunk.content
        if content:
            print(content, end="", flush=True)
            sys.stdout.flush()
            ai_content += content
    print("")

    return {"messages": [AIMessage(content=ai_content)]}


# 4. 定义路由逻辑
def should_continue(state: SummaryBufferState) -> str:
    """决定是否需要生成摘要"""
    if should_generate_summary(state):
        return "summarize"
    return "end"


# 5. 构建图
def create_summary_buffer_graph():
    """创建摘要缓冲混合记忆图"""
    # 创建图
    graph = StateGraph(SummaryBufferState)

    # 添加节点
    graph.add_node("chatbot", chatbot_node)
    graph.add_node("summarize", generate_summary_node)

    # 添加边
    graph.add_edge(START, "chatbot")
    graph.add_conditional_edges(
        "chatbot", should_continue, {"summarize": "summarize", "end": END}
    )
    graph.add_edge("summarize", END)

    # 添加持久化（内存存储）
    memory = MemorySaver()

    return graph.compile(checkpointer=memory)


# ==================== 主程序 ====================

print("=" * 60)
print("LangGraph 版本：摘要缓冲混合记忆演示")
print("当历史消息超过6条时，会自动生成摘要")
print("输入 'q' 退出")
print("=" * 60)

# 创建应用
app = create_summary_buffer_graph()

# 配置（使用线程ID来区分不同会话）
config = {"configurable": {"thread_id": "user_session_001"}}

while True:
    query = input("\nHuman: ")

    if query == "q":
        break

    # 调用图
    result = app.invoke({"messages": [HumanMessage(content=query)]}, config=config)

    # 打印调试信息
    state = app.get_state(config)
    messages = state.values.get("messages", [])
    summary = state.values.get("summary", "")

    # 只统计对话消息
    chat_messages = [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]

    print(f"\n[DEBUG] 当前历史消息数: {len(chat_messages)}")
    print(f"[DEBUG] 当前摘要: {summary if summary else '(无)'}")
    print(f"[DEBUG] 缓冲区阈值: 6条消息")
