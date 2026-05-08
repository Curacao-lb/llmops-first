import dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from typing import TypedDict, Annotated, Any
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END

dotenv.load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")


# 1.创建状态图,并使用GraphState作为状态数据
class GraphState(TypedDict):
    """图结构的状态数据"""

    messages: Annotated[list[BaseMessage], add_messages]


def chatbot(state: GraphState, config: RunnableConfig | None = None) -> Any:
    """聊天机器人节点,使用大语言模型根据传递的消息列表生成内容"""
    ai_messages = llm.invoke(state["messages"], config=config)
    return {"messages": [ai_messages]}


graph_builder = StateGraph(GraphState)

# 2.添加节点
graph_builder.add_node("llm", chatbot)

# 3.添加边
graph_builder.set_entry_point("llm")  # 等价于add_edge->START
graph_builder.set_finish_point("llm")  # 等价于add_edge->END
# graph_builder.add_edge(START, "llm")
# graph_builder.add_edge("llm", END)

# 4.编译图为Runnable可运行组件
graph = graph_builder.compile()

# 5.调用图架构应用
print(graph.invoke({"messages": [("human", "你好，你是？我叫Roxiaobin，我喜欢徒步")]}))
