from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)

from langchain_core.messages import AIMessage

from datetime import datetime

# 这里的 from_template 底层调用python的 f-string
prompt = PromptTemplate.from_template("请讲一个关于{subject}的冷笑话")

prompt_value = prompt.invoke({"subject": "程序员"})

# format 返回的是纯文本
print(prompt.format(subject="程序员"))
# text='请讲一个关于程序员的冷笑话'
# invoke() 传入变量字典,填充模板，invoke 返回的是 Message 对象
print(prompt.invoke({"subject": "程序员"}))

# [HumanMessage(content='请讲一个关于程序员的冷笑话', additional_kwargs={}, response_metadata={})]
print(prompt_value.to_messages())

print("========================================")

chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是我开发的聊天机器人，请帮我回答用户的问题，当前时间为{now}"),
        # 有可能还有其他的消息，先占位
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template("请讲一个关于{subject}的冷笑话"),
    ]
).partial(now=datetime.now())

chat_prompt_value = chat_prompt.invoke(
    {
        # 这里的变量可以优先定义，使用partial方法,放到from_messages那边
        # "now": datetime.now(),
        "subject": "程序员",
        # 这里不能传入变量的
        "chat_history": [("human", "我是Robin"), AIMessage("我在学习langchain")],
    }
)

"""
messages=[
  SystemMessage(
    content='你是我开发的聊天机器人，请帮我回答用户的问题，当前时间为2026-01-30 14:09:16.829051', 
    additional_kwargs={}, response_metadata={}),
    HumanMessage(content='请讲一个关于程序员的冷笑话', additional_kwargs={}, response_metadata={})
]
"""
print(chat_prompt_value)

print("========================================")

"""
  to_string：

  System: 你是我开发的聊天机器人，请帮我回答用户的问题，当前时间为2026-01-30 14:20:31.039844
  Human: 我是Robin
  AI: 我在学习langchain
  Human: 请讲一个关于程序员的冷笑话
"""
print(chat_prompt_value.to_string())
