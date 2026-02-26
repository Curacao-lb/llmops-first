import dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import trim_messages

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


# 会话历史管理器
def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    # 如果会话不存在
    if session_id not in store:
        # 创建新会话
        store[session_id] = InMemoryChatMessageHistory()
    # 返回该会话对应的消息历史对象
    return store[session_id]


# 4.创建消息修剪器（保留最近3轮对话 = 6条消息）
# 这是 v1.0 中替代 ConversationBufferWindowMemory 的方式
trimmer = trim_messages(
    max_tokens=6,  # 最多保留6条消息
    strategy="last",  # 保留最后的消息
    token_counter=lambda msgs: len(msgs),  # 按消息数量计数
    include_system=False,  # 不包含系统消息（系统消息在 prompt 中）
    allow_partial=False,  # 不允许部分消息
    start_on="human",  # 从 human 消息开始
)


# 5.构建链应用（使用 trimmer 修剪消息）
def process_messages(input_dict):
    """处理消息：加载历史 -> 修剪 -> 返回"""
    session_id = input_dict["session_id"]
    query = input_dict["query"]

    # 获取历史消息
    history = get_session_history(session_id)
    messages = history.messages

    # 使用 trimmer 修剪消息（保留最近6条）
    trimmed_messages = trimmer.invoke(messages)

    return {"query": query, "history": trimmed_messages}


chain = process_messages | prompt | llm | StrOutputParser()

# 6.死循环构建对话命令行
session_id = "user_session_001"

while True:
    query = input("Human: ")

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

    # 打印调试信息
    print(f"[DEBUG] 当前历史消息数: {len(history.messages)} (保留最近6条，即3轮对话)\n")
