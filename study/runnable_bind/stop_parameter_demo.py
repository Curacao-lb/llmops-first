import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

# 示例1：stop参数不会截断输入内容的重复
print("=== 示例1：重复输入（stop参数无效）===")
prompt1 = ChatPromptTemplate.from_messages(
    [
        ("system", "你正在执行一项测试，请重复用户传递的内容，除了重复其他均不要操作"),
        ("human", "{query}"),
    ]
)
llm1 = ChatOpenAI(model="gpt-3.5-turbo", stop="world")
chain1 = prompt1 | llm1 | StrOutputParser()
content1 = chain1.invoke({"query": "hello world"})
print(f"输出: {content1}")
print(f"说明: 模型直接返回完整内容，stop参数不会截断\n")

# 示例2：stop参数会阻止模型生成额外内容
print("=== 示例2：让模型生成故事（stop参数有效）===")
prompt2 = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个故事讲述者"),
        ("human", "讲一个关于 {topic} 的故事"),
    ]
)
llm2 = ChatOpenAI(model="gpt-3.5-turbo", stop="world")
chain2 = prompt2 | llm2 | StrOutputParser()
content2 = chain2.invoke({"topic": "hello world程序"})
print(f"输出: {content2}")
print(f"说明: 当模型生成到'world'时会停止\n")

# 示例3：使用bind方法动态设置stop参数
print("=== 示例3：使用bind方法 ===")
prompt3 = ChatPromptTemplate.from_messages(
    [
        ("system", "请继续这句话，并添加更多内容"),
        ("human", "{text}"),
    ]
)
llm3 = ChatOpenAI(model="gpt-3.5-turbo")
# 使用bind动态绑定stop参数
llm_with_stop = llm3.bind(stop=["world", "世界"])
chain3 = prompt3 | llm_with_stop | StrOutputParser()
content3 = chain3.invoke({"text": "hello"})
print(f"输出: {content3}")
print(f"说明: 模型生成时遇到'world'或'世界'会停止\n")

# 示例4：如果你真的想截断包含"world"的文本
print("=== 示例4：手动截断文本 ===")
prompt4 = ChatPromptTemplate.from_messages(
    [
        ("system", "你正在执行一项测试，请重复用户传递的内容"),
        ("human", "{query}"),
    ]
)
llm4 = ChatOpenAI(model="gpt-3.5-turbo")
chain4 = prompt4 | llm4 | StrOutputParser()
content4 = chain4.invoke({"query": "hello world"})
# 手动截断
truncated = content4.split("world")[0].strip()
print(f"原始输出: {content4}")
print(f"截断后: {truncated}")
