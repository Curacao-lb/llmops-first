import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


# 1.准备少量示例，这些示例会变成一组组 human/ai 消息
examples = [
    {
        "question": "帮我计算下2+2等于多少？",
        "answer": "4",
    },
    {
        "question": "帮我计算下2+3等于多少？",
        "answer": "5",
    },
    {
        "question": "帮我计算下20*15等于多少？",
        "answer": "300",
    },
]

# 2.定义每个示例如何转换成聊天消息
example_prompt = ChatPromptTemplate.from_messages(
    [
        ("human", "{question}"),
        ("ai", "{answer}"),
    ]
)

# 3.创建 FewShotChatMessagePromptTemplate
few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
)

# 4.把 few-shot 示例放进最终的聊天提示词中
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个数学计算助手，请参考示例，只返回最终计算结果。"),
        few_shot_prompt,
        ("human", "{question}"),
    ]
)

# 5.连接真实大模型 API
llm = ChatOpenAI(model="gpt-3.5-turbo")
chain = prompt | llm | StrOutputParser()


if __name__ == "__main__":
    question = "帮我计算下8*7等于多少？"

    print("最终发送给模型的消息：")
    prompt_value = prompt.invoke({"question": question})
    print(prompt_value)

    print("\n模型回答：")
    print(chain.invoke({"question": question}))
