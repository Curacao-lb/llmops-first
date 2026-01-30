from langchain_core.prompts import ChatPromptTemplate

system_chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是我开发的聊天机器人，请帮我回答用户的问题, 我叫{username}"),
    ]
)

human_chat_prompt = ChatPromptTemplate.from_messages([("human", "{query}")])

# 这里的加号是正常的，没有问题的，证明这里的加号也是实现了魔术方法__add__
chat_prompt = system_chat_prompt + human_chat_prompt

"""
  messages=[SystemMessage(content='你是我开发的聊天机器人，请帮我回答用户的问题, 我叫张三', additional_kwargs={}, response_metadata={}), HumanMessage(content='你好', additional_kwargs={}, response_metadata={})]
"""
print(chat_prompt.invoke({"username": "张三", "query": "你好"}))
