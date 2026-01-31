import dotenv
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


# 1.编排prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是我开发的聊天机器人，请回答用户问题，现在的时间是{now}"),
        ("user", "{question}"),
    ]
).partial(now=datetime.now())

# 2.创建大语言模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

response = llm.stream(prompt.invoke({"question": "你能介绍一下外研社和外研在线吗"}))

for chunk in response:
    print(chunk.content, end="", flush=True)
