# LangGraph `basic_usage.py` 详解

对应文件：[basic_usage.py](./basic_usage.py)

这个文件实现的是一个最小 LangGraph：输入一条用户消息，经过一个 `llm` 节点，调用大模型生成回复，然后结束。

## 整体流程

```text
输入 messages
    ↓
llm 节点 chatbot()
    ↓
返回新的 AIMessage
    ↓
合并到 messages
    ↓
输出完整消息列表
```

也就是说，它不是一个多轮循环图，而是一个“一次输入，一次模型调用，一次输出”的最小示例。

## 1. 导入依赖

```python
import dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from typing import TypedDict, Annotated, Any
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
```

几个关键对象：

- `ChatOpenAI`：LangChain 里的 OpenAI 聊天模型封装。
- `BaseMessage`：消息基类，`HumanMessage`、`AIMessage`、`SystemMessage` 都属于它。
- `RunnableConfig`：LangChain/LangGraph 运行时配置类型，比如 `thread_id`、`callbacks`、`tags`、`metadata` 等。
- `TypedDict`：定义状态字典的结构。
- `Annotated`：给某个字段附加额外元信息。这里用于告诉 LangGraph：`messages` 字段应该怎么合并。
- `add_messages`：LangGraph 提供的消息合并函数。
- `StateGraph`：LangGraph 的核心，用来创建“状态图”。
- `START` / `END`：图的开始和结束节点标记。当前代码 import 了，但实际用的是 `set_entry_point` / `set_finish_point`，所以 `START` 和 `END` 暂时没真正用上。

## 2. 加载环境变量

```python
dotenv.load_dotenv()
```

这会读取 `.env` 文件。通常你的 OpenAI Key 会放在里面：

```env
OPENAI_API_KEY=xxx
```

这样 `ChatOpenAI` 才能调用模型。

## 3. 创建模型

```python
llm = ChatOpenAI(model="gpt-4o-mini")
```

这里创建了一个聊天模型实例。

后面这行会真正调用大模型：

```python
llm.invoke(...)
```

## 4. 定义 GraphState

```python
class GraphState(TypedDict):
    """图结构的状态数据"""

    messages: Annotated[list[BaseMessage], add_messages]
```

这是整个 LangGraph 里最重要的概念之一：**State，状态**。

LangGraph 的节点之间不是随便传变量，而是统一传一个状态对象。

你的状态长这样：

```python
{
    "messages": [...]
}
```

也就是说，这个图只维护一个字段：`messages`。

`messages` 是一个消息列表，里面可以放：

```python
HumanMessage(...)
AIMessage(...)
SystemMessage(...)
```

或者像 `invoke` 里那样传 tuple：

```python
("human", "你好，你是？")
```

LangGraph/LangChain 会帮你转换成标准 message 对象。

## 5. 定义节点函数

```python
def chatbot(state: GraphState, config: RunnableConfig | None = None) -> Any:
    """聊天机器人节点,使用大语言模型根据传递的消息列表生成内容"""
    ai_messages = llm.invoke(state["messages"], config=config)
    return {"messages": [ai_messages]}
```

这个函数就是图里的一个节点。

LangGraph 节点函数通常长这样：

```python
def node(state):
    ...
    return partial_state
```

或者带 config：

```python
def node(state, config: RunnableConfig | None = None):
    ...
    return partial_state
```

这里的 `state` 是当前图状态，比如：

```python
{
    "messages": [
        HumanMessage(content="你好，你是？我叫Roxiaobin，我喜欢徒步")
    ]
}
```

然后这一行：

```python
ai_messages = llm.invoke(state["messages"], config=config)
```

把当前消息列表传给大模型，模型返回一个 `AIMessage`。

注意这里用的是：

```python
state["messages"]
```

而不是：

```python
state.messages
```

因为 `GraphState` 是 `TypedDict`，运行时本质还是普通 dict。

然后返回：

```python
return {"messages": [ai_messages]}
```

这个返回值不是完整 state，而是“本节点想更新的部分 state”。

LangGraph 会把这个返回值合并回原来的 state。

## 6. 创建图构建器

```python
graph_builder = StateGraph(GraphState)
```

这一步创建一个状态图。

你可以理解为：

```text
我要创建一张图，这张图运行时维护的状态结构是 GraphState。
```

此时还没有节点，也没有边，只是一个空图。

## 7. 添加节点

```python
graph_builder.add_node("llm", chatbot)
```

这行把 `chatbot` 函数注册成图里的一个节点，节点名叫 `"llm"`。

之后图里就有了一个节点：

```text
llm -> chatbot()
```

节点名 `"llm"` 是你自己取的，可以叫 `"chatbot"`、`"model"`、`"assistant"` 都行。

## 8. 添加边

```python
graph_builder.set_entry_point("llm")
graph_builder.set_finish_point("llm")
```

这两行表示：

```text
START -> llm -> END
```

也就是：

1. 图一开始先运行 `"llm"` 节点
2. `"llm"` 节点运行完之后，图结束

注释里的写法是等价的：

```python
graph_builder.add_edge(START, "llm")
graph_builder.add_edge("llm", END)
```

对于第一次学习，可以先这样理解：

```text
节点 = 做事的人
边 = 下一步去哪里
状态 = 每一步共享的数据
```

现在这张图只有一个节点，所以看起来有点简单。但 LangGraph 的优势是在多节点、多分支、循环、人类审批、工具调用的时候体现出来。

比如之后可以变成：

```text
START
  ↓
llm
  ↓
判断是否需要工具
  ↓ 是                ↓ 否
tool_node          END
  ↓
llm
```

## 9. 编译图

```python
graph = graph_builder.compile()
```

`StateGraph` 只是图的“设计稿”。

`compile()` 之后才变成可运行对象。

编译后的 `graph` 支持：

```python
graph.invoke(...)
graph.stream(...)
graph.batch(...)
```

这些接口和 LangChain 的 Runnable 风格一致。

## 10. 调用图

```python
print(graph.invoke({"messages": [("human", "你好，你是？我叫Roxiaobin，我喜欢徒步")]}))
```

这里传入初始 state：

```python
{
    "messages": [
        ("human", "你好，你是？我叫Roxiaobin，我喜欢徒步")
    ]
}
```

LangGraph 开始执行：

```text
START -> llm -> END
```

执行 `"llm"` 节点时，调用：

```python
chatbot(state, config)
```

然后 `chatbot` 返回：

```python
{
    "messages": [AIMessage(...)]
}
```

因为你对 `messages` 使用了 `Annotated[..., add_messages]`，所以最终结果不是覆盖原 messages，而是追加合并：

```python
{
    "messages": [
        HumanMessage(content="你好，你是？我叫Roxiaobin，我喜欢徒步"),
        AIMessage(content="你好，Roxiaobin！...")
    ]
}
```

这就是为什么输出里既有用户消息，也有 AI 回复。

## `Annotated` 的作用

这一行非常关键：

```python
messages: Annotated[list[BaseMessage], add_messages]
```

它可以拆成两层理解：

```python
list[BaseMessage]
```

表示 `messages` 的数据类型是消息列表。

```python
Annotated[..., add_messages]
```

表示给这个字段附加一个 LangGraph 合并规则：当节点返回新的 `messages` 时，不要简单覆盖，而是用 `add_messages` 合并。

## 不用 `Annotated` 会怎样？

如果你写成：

```python
class GraphState(TypedDict):
    messages: list[BaseMessage]
```

那么节点返回：

```python
return {"messages": [ai_messages]}
```

会把原来的 `messages` 覆盖掉。

最终输出大概率只剩：

```python
{
    "messages": [
        AIMessage(content="...")
    ]
}
```

用户原始输入那条 `HumanMessage` 就没了。

## 使用 `Annotated` 会怎样？

你现在的写法：

```python
messages: Annotated[list[BaseMessage], add_messages]
```

节点返回：

```python
return {"messages": [ai_messages]}
```

LangGraph 会理解为：

```text
旧 messages + 新 messages
```

所以最终变成：

```python
{
    "messages": [
        HumanMessage("你好"),
        AIMessage("你好呀")
    ]
}
```

区别就在这里：**覆盖 vs 追加合并**。

## 一个直观对比

不使用 `Annotated`：

```python
初始 state:
{"messages": [HumanMessage("你好")]}

节点返回:
{"messages": [AIMessage("你好呀")]}

最终 state:
{"messages": [AIMessage("你好呀")]}
```

使用 `Annotated[..., add_messages]`：

```python
初始 state:
{"messages": [HumanMessage("你好")]}

节点返回:
{"messages": [AIMessage("你好呀")]}

最终 state:
{"messages": [
    HumanMessage("你好"),
    AIMessage("你好呀")
]}
```

## 为什么不是直接在节点里手动 append？

你当然可以这么写：

```python
return {"messages": state["messages"] + [ai_messages]}
```

但这不推荐。

LangGraph 的设计是：节点只返回“这一步新增/更新了什么”，至于怎么合并，由 state schema 决定。

这样有几个好处：

1. 节点函数更简单
2. 多个节点更新同一个字段时更可控
3. 图的状态合并规则集中定义在 `GraphState`
4. `messages` 还能处理 message id、覆盖同 id 消息等更复杂逻辑

## 这个文件可以怎么记

第一次学 LangGraph，可以先记住四件事：

```python
class GraphState(TypedDict):
    ...
```

定义图里流动的数据。

```python
def chatbot(state):
    ...
    return {...}
```

定义一个节点做什么。

```python
graph_builder.add_node(...)
graph_builder.set_entry_point(...)
graph_builder.set_finish_point(...)
```

把节点连成图。

```python
graph = graph_builder.compile()
graph.invoke(...)
```

编译并运行。

这个文件就是 LangGraph 的最小骨架：

```text
State -> Node -> Edge -> Compile -> Invoke
```

而 `Annotated[..., add_messages]` 是为了告诉 LangGraph：`messages` 这个字段不是普通覆盖更新，而是聊天记录式的追加合并。
