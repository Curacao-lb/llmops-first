### BaseAgent.invoke 方法详解

> 文件位置：`internal/core/agent/agents/base_agent.py`（第 62~146 行）

### 这个方法要解决什么问题

`invoke` 方法的注释写着"块内容响应，一次性生成完整内容后返回"。

关键在于理解它和 `stream` 的关系：

- `stream` 方法是**流式**的，像挤牙膏一样一点一点往外吐数据。比如 AI 回答"你好世界"，它可能先吐"你"，再吐"好"，再吐"世界"，分好几次给你。
- `invoke` 方法是**一次性**的，它在内部偷偷调用了 `stream`，把这些零碎的片段全部收集起来、拼装好，最后一次性返回一个完整的结果 `AgentResult`。

打个比方：`stream` 是快递员分好几趟把拆散的家具零件送到你家，`invoke` 则是帮你把所有零件收齐、组装成一个完整的柜子，再交给你。

### 几个关键概念

- **AgentThought（智能体想法/事件）**：AI 干活过程中产生的一个个"事件片段"。每个片段有个 `event` 字段表示它是什么类型的事件，还有 `id` 表示它属于哪个事件。
- **event 类型**（来自 `QueueEvent`）：
  - `AGENT_MESSAGE`：AI 正在吐答案文字（这个是**一点点累加**的）
  - `AGENT_THOUGHT` / `AGENT_ACTION` / `DATASET_RETRIEVAL` 等：AI 的思考、调用工具、查知识库等动作（这些是**整块**给的）
  - `PING`：心跳信号，没有实际内容，用来保持连接
  - `STOP` / `TIMEOUT` / `ERROR`：停止 / 超时 / 出错
- **AgentResult（最终结果）**：最后打包好的完整结果，包含原始问题、完整答案、所有推理步骤、总耗时等。

### 一个关键难点：为什么 AGENT_MESSAGE 要特殊处理

这是整段代码最绕的地方。记住一句话：

> 同一个 id 的 AGENT_MESSAGE 事件会来很多次，每次只带一小段文字，需要把它们拼接起来；而其他类型的事件同一个 id 只来一次，直接覆盖即可。

代码里用一个字典 `agent_thoughts`（key 是事件 id，value 是事件内容）来存所有事件。

- 遇到 `AGENT_MESSAGE`：如果这个 id 第一次见 → 存进去；如果已经见过 → 把新来的文字**拼接**到旧的后面。
- 遇到其他事件：直接放进字典，同 id 就**覆盖**。

### 结合一个完整例子走一遍

假设用户问：**"北京今天天气怎么样？"**，AI 需要先调用一个天气工具，再回答。

#### 第一部分：解析用户输入

```python
content = input["messages"][0].content
```

拿到用户的第一条消息内容。这里分两种情况：

- 如果 `content` 是纯字符串（比如 `"北京今天天气怎么样？"`）→ 直接作为 `query`。
- 如果 `content` 是列表（说明用户可能同时发了**文字 + 图片**）→ 从列表里取出文字部分当 `query`，再把所有图片的 url 提取到 `image_urls`。

我们的例子是纯文字，所以：`query = "北京今天天气怎么样？"`，`image_urls = []`。

然后创建一个空的结果容器：`agent_result = AgentResult(query=..., image_urls=...)`，还有一个空字典 `agent_thoughts = {}`。

#### 第二部分：循环收集 stream 吐出来的事件

假设 `stream` 依次吐出下面这些事件（简化形式表示）：

| 顺序 | id | event | 内容 |
|------|-----|-------|------|
| 1 | `ping-1` | PING | （空，心跳） |
| 2 | `act-1` | AGENT_ACTION | tool=天气工具, 调用参数={city:北京} |
| 3 | `msg-1` | AGENT_MESSAGE | answer="北京" |
| 4 | `msg-1` | AGENT_MESSAGE | answer="今天" |
| 5 | `msg-1` | AGENT_MESSAGE | answer="晴，25度" |
| 6 | `end-1` | AGENT_END | （结束标记） |

逐个看循环里发生了什么：

- **事件1 `ping-1`**：`event == PING`，直接跳过，什么都不做。（心跳不需要记录）
- **事件2 `act-1`**：不是 PING，也不是 AGENT_MESSAGE，走"其他事件"分支 → `agent_thoughts["act-1"] = 这个事件`。它也不是 STOP/ERROR/TIMEOUT，所以异常判断不触发。
- **事件3 `msg-1`（answer="北京"）**：是 AGENT_MESSAGE。字典里还没有 `msg-1` → 初始化：`agent_thoughts["msg-1"] = 事件`。然后：`agent_result.answer += "北京"` → 现在答案是 `"北京"`。
- **事件4 `msg-1`（answer="今天"）**：又是 AGENT_MESSAGE，且 `msg-1` 已存在 → 做**叠加**：

  ```python
  agent_thoughts["msg-1"] = agent_thoughts["msg-1"].model_copy(update={
      "thought": 旧thought + 新thought,
      "answer":  "北京" + "今天",   # 拼接
      "latency": 用最新的耗时,
  })
  ```

  `model_copy` 意思是复制一份并更新指定字段（因为 pydantic 对象不方便直接改）。然后：`agent_result.answer += "今天"` → 答案变成 `"北京今天"`。

- **事件5 `msg-1`（answer="晴，25度"）**：同上继续叠加 → 字典里的 answer 变成 `"北京今天晴，25度"`，`agent_result.answer` 也变成 `"北京今天晴，25度"`。
- **事件6 `end-1`**：不是 PING、不是 AGENT_MESSAGE，走"其他事件"分支 → 存进字典。不是异常事件，异常判断不触发。

> 补充：如果某个事件是 STOP/TIMEOUT/ERROR，就把结果状态改成对应状态；如果是 ERROR，还把出错的 `observation` 记到 `error` 字段里。上面这个例子一切正常，所以没触发。

#### 第三部分：收尾打包

循环结束后，`agent_thoughts` 字典里有 3 个条目：`act-1`、`msg-1`（已拼好完整答案）、`end-1`。

- **转列表**：把字典的所有 value 转成列表存进结果：

  ```python
  agent_result.agent_thoughts = [act-1事件, msg-1事件, end-1事件]
  ```

  这就是完整的"推理步骤清单"。

- **完善 message**：从这些事件里找出那个 `AGENT_MESSAGE` 事件，把它的 `message`（产生答案所用的消息列表）赋给 `agent_result.message`。`next(..., [])` 的意思是"找第一个符合条件的，找不到就用空列表"。
- **更新总耗时**：把所有事件的 `latency`（耗时）加起来，得到总耗时 `agent_result.latency`。

最后 `return agent_result`，返回的这个对象里就有了：

- `query` = "北京今天天气怎么样？"
- `answer` = "北京今天晴，25度"（完整答案）
- `agent_thoughts` = 完整的推理过程列表
- `latency` = 总耗时

### 一句话总结

这个方法就是**"把流式的零碎输出收集起来，拼成一个完整结果"**的转换器。它逐个处理 stream 吐出的事件：心跳事件忽略，答案文字类事件（AGENT_MESSAGE）一段段拼接起来，其他动作类事件按 id 存起来，遇到异常就记录状态，最后把答案、推理步骤、耗时等打包成一个 `AgentResult` 返回。

核心记这三点就够了：

1. `invoke` = 内部跑 `stream` + 收集拼装。
2. `AGENT_MESSAGE` 特殊，要**累加拼接**；其他事件直接**覆盖存储**。
3. 用字典按 `id` 去重/合并，最后转成列表输出。

### 延伸：为什么要重写 invoke，而不直接用 LangChain 的

`BaseAgent` 继承了 LangChain 的 `Runnable`，而 `Runnable` 规定了 `invoke` / `stream` 等标准方法。这里的 `invoke` 就是**重写（override）了父类的默认实现**。

原因是 LangChain 默认的 `invoke` 只返回最终答案，满足不了这个平台的业务需求。项目需要的是 `AgentResult` 里那一大堆信息：完整答案、每一步推理过程（`agent_thoughts`）、token 消耗与费用、耗时、状态、错误等。

而且这些数据来自项目自建的**队列机制（AgentQueueManager）**：`stream` 内部起子线程跑真正的 agent，agent 把一个个自定义事件塞进队列，主线程再从队列里监听并 yield。既然数据源头是自定义的，消费和打包它的 `invoke` 自然也得自己写。

之所以沿用 `invoke` 这个名字而不另起新方法，是为了**保持接口统一**：在任何需要 `Runnable` 的地方都能直接塞这个 Agent 进去，像用普通 LangChain 组件一样调用，行为兼容。总结就是——接口沿用，实现替换。
