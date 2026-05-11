from typing import Any
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph.message import RemoveMessage
import json

import dotenv

dotenv.load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")


def chatbot(state: MessagesState, config: RunnableConfig | None = None) -> Any:
    """聊天机器人节点"""
    return {"messages": [llm.invoke(state["messages"])]}


def format_output(result: dict) -> None:
    """格式化输出结果"""
    print("\n" + "=" * 80)
    print("对话结果")
    print("=" * 80)

    messages = result.get("messages", [])
    for i, msg in enumerate(messages, 1):
        print(f"\n【消息 {i}】")
        print(f"类型: {msg.__class__.__name__}")
        print(f"内容: {msg.content}")

        # 如果是 AIMessage，显示额外信息
        if hasattr(msg, "response_metadata") and msg.response_metadata:
            metadata = msg.response_metadata
            print(f"模型: {metadata.get('model_name', 'N/A')}")
            if "token_usage" in metadata:
                tokens = metadata["token_usage"]
                print(
                    f"Token 使用: 输入={tokens.get('prompt_tokens')}, 输出={tokens.get('completion_tokens')}, 总计={tokens.get('total_tokens')}"
                )

    print("\n" + "=" * 80 + "\n")


def delete_human_message(
    state: MessagesState, config: RunnableConfig | None = None
) -> Any:
    """删除状态中的人类消息"""
    human_message = state["messages"][0]
    return {"messages": [RemoveMessage(id=human_message.id)]}


graph_builder = StateGraph(MessagesState)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("delete_human_message", delete_human_message)

graph_builder.add_edge("chatbot", "delete_human_message")

graph_builder.set_entry_point("chatbot")
graph_builder.set_finish_point("delete_human_message")

graph = graph_builder.compile()

result = graph.invoke({"messages": [("human", "你好， 你是？")]})
format_output(result)
