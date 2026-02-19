import dotenv
from openai import OpenAI
from langchain_community.chat_message_histories import FileChatMessageHistory

dotenv.load_dotenv()

# 1.创建OpenAI客户端
client = OpenAI(base_url="https://hk.xty.app/v1")
chat_history = FileChatMessageHistory("./memory.txt")

# 2.创建一个死循环用于人机对话
while True:

    # 3.获取用户输入
    content = input("请输入您的问题(输入quit退出)：")

    # 4.判断用户是否想要退出
    if content == "quit":
        break

    # 5.调用OpenAI API
    print("AI: ", flush=True, end="")
    system_prompt = (
        "你是OpenAI开发的ChatGPT聊天机器人，可以根据相应的上下文回复用户信息，上下文里存放的是人类与你交互对话的信息列表。 \n\n"
        # 在chat_history中写了一个魔术方法，这个魔术方法为__str__。如果需要使用到字符串时，可以直接打印出来
        f"<context>{chat_history}</context>\n\n"
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        stream=True,
    )
    ai_content = ""
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content is not None:
            ai_content += content
            print(content, flush=True, end="")
    chat_history.add_user_message(content)
    chat_history.add_ai_message(ai_content)
    print("")
