import dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import SystemMessage

dotenv.load_dotenv()

# 1.创建提示模板
prompt = ChatPromptTemplate(
    [
        ("system", "你是OpenAI开发的聊天机器人，请根据对应的上下文回复用户问题"),
        MessagesPlaceholder("history"),
        ("human", "{query}"),
    ]
)

# 2.创建大语言模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 3.创建消息历史存储（v1.0 新方式）
store = {}
# 存储每个会话的摘要
summaries = {}


# 会话历史管理器
def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


# 摘要生成函数
def generate_summary(session_id: str, old_summary: str, new_messages: list) -> str:
    """
    生成新的摘要
    :param session_id: 会话ID
    :param old_summary: 旧的摘要
    :param new_messages: 需要摘要的新消息列表
    :return: 新的摘要
    """
    # 构建摘要提示词
    messages_text = "\n".join([f"{msg.type}: {msg.content}" for msg in new_messages])

    summary_prompt = f"""你是一个强大的聊天机器人，请根据用户提供的谈话内容，总结摘要，并将其添加到先前提供的摘要中，返回一个新的摘要。
除了新摘要其他任何数据都不要生成。
如果用户的对话信息里有一些关键的信息，比方说姓名、爱好、性别、重要事件等等，这些全部都要包括在生成的摘要中。
摘要尽可能要还原用户的对话记录。

当前摘要：{old_summary if old_summary else "无"}

新的对话：
{messages_text}

请生成新摘要："""

    # 调用 LLM 生成摘要
    response = llm.invoke([SystemMessage(content=summary_prompt)])
    return response.content


# 摘要缓冲混合记忆管理
def manage_summary_buffer_memory(session_id: str, max_messages: int = 6):
    """
    管理摘要缓冲混合记忆
    :param session_id: 会话ID
    :param max_messages: 缓冲区最大消息数（超过则生成摘要）
    """
    history = get_session_history(session_id)
    messages = history.messages

    # 如果消息数超过阈值，生成摘要
    if len(messages) > max_messages:
        # 获取旧摘要
        old_summary = summaries.get(session_id, "")

        # 取出最早的2条消息（1轮对话）用于生成摘要
        messages_to_summarize = messages[:2]

        print("\n[摘要生成中...]")
        # 生成新摘要
        new_summary = generate_summary(session_id, old_summary, messages_to_summarize)
        summaries[session_id] = new_summary
        print(f"[新摘要生成成功]: {new_summary}\n")

        # 从历史中删除已摘要的消息
        history.messages = messages[2:]


# 构建链应用
def process_messages(input_dict):
    """处理消息：加载历史 -> 添加摘要 -> 返回"""
    session_id = input_dict["session_id"]
    query = input_dict["query"]

    # 获取历史消息
    history = get_session_history(session_id)
    messages = history.messages.copy()

    # 如果有摘要，将摘要添加到消息开头
    summary = summaries.get(session_id, "")
    if summary:
        # 在消息列表开头插入摘要
        summary_message = SystemMessage(content=f"历史对话摘要：{summary}")
        messages = [summary_message] + messages

    return {"query": query, "history": messages}


chain = process_messages | prompt | llm | StrOutputParser()

# 6.死循环构建对话命令行
session_id = "user_session_001"

print("=" * 60)
print("摘要缓冲混合记忆演示")
print("当历史消息超过6条时，会自动将最早的对话生成摘要")
print("输入 'q' 退出")
print("=" * 60)

while True:
    query = input("\nHuman: ")

    if query == "q":
        exit(0)

    # 流式生成响应
    response = chain.stream({"query": query, "session_id": session_id})

    print("AI: ", end="", flush=True)
    ai_response = ""
    for chunk in response:
        print(chunk, end="", flush=True)
        ai_response += chunk
    print("")

    # 将本轮对话保存到历史中
    history = get_session_history(session_id)
    history.add_user_message(query)
    history.add_ai_message(ai_response)

    # 管理摘要缓冲记忆（超过6条消息则生成摘要）
    manage_summary_buffer_memory(session_id, max_messages=6)

    # 打印调试信息
    current_summary = summaries.get(session_id, "")
    print(f"\n[DEBUG] 当前历史消息数: {len(history.messages)}")
    print(f"[DEBUG] 当前摘要: {current_summary if current_summary else '(无)'}")
    print(f"[DEBUG] 缓冲区阈值: 6条消息")
