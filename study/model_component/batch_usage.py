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

"""
这里的批处理它会将每一个任务单独进行处理。
所以这两条提示它其实并没有进行关联。
只是在底层langchain他会去开创一个线程，将这些批处理挨个去发起请求，最后得到所有请求，然后再总结汇总给我们
"""
ai_messages = llm.batch(
    [
        prompt.invoke({"question": "你好,你是谁？"}),
        prompt.invoke({"question": "今天天气怎么样"}),
        prompt.invoke({"question": "帮我写一个关于夏天的诗句"}),
    ]
)

# 成功输出三条数据
for m in ai_messages:
    print(m.content)
    print("+++++++++++++++++++++++++++")
