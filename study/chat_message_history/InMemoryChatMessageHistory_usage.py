from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)

# 不能直接实例化，只能实例化其子类
# chat_history = BaseChatMessageHistory()

chat_history = InMemoryChatMessageHistory()

chat_history.add_user_message("你好，我是Robin，你是谁？")

chat_history.add_ai_message("你好，我是ChatGPT，有什么可以帮助到你的？")

print(chat_history)
