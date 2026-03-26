import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

# bind() 方法的正确用法演示
# bind() 用于将参数绑定到 Runnable 对象上，创建一个新的 Runnable

print("=== 示例1：bind() 绑定 stop 参数（生成场景）===")
prompt1 = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个故事创作者，请根据用户的开头继续写故事"),
        ("human", "{text}"),
    ]
)

llm = ChatOpenAI(model="gpt-3.5-turbo")

# 使用 bind() 绑定 stop 参数
# 当模型生成内容时遇到 "结束" 或 "end" 会立即停止
chain1 = prompt1 | llm.bind(stop=["结束", "end"]) | StrOutputParser()

content1 = chain1.invoke({"text": "从前有一座山"})
print(f"输出: {content1}")
print("说明: 模型生成故事时如果遇到停止词会立即停止\n")

print("=== 示例2：bind() 绑定多个参数 ===")
prompt2 = ChatPromptTemplate.from_messages(
    [
        ("system", "请用简短的语言回答"),
        ("human", "{question}"),
    ]
)

# bind() 可以同时绑定多个参数
chain2 = (
    prompt2
    | llm.bind(
        temperature=0.1,  # 降低随机性
        max_tokens=50,  # 限制输出长度
        stop=["\n\n"],  # 遇到双换行停止
    )
    | StrOutputParser()
)

content2 = chain2.invoke({"question": "什么是Python？"})
print(f"输出: {content2}")
print("说明: bind() 同时绑定了 temperature、max_tokens 和 stop 参数\n")

print("=== 示例3：为什么重复场景下 stop 不生效 ===")
prompt3 = ChatPromptTemplate.from_messages(
    [
        ("system", "请重复用户的输入"),
        ("human", "{query}"),
    ]
)

chain3 = prompt3 | llm.bind(stop=["world"]) | StrOutputParser()
content3 = chain3.invoke({"query": "hello world"})
print(f"输出: {content3}")
print("说明: 模型直接返回完整输入，不会逐词生成，所以 stop 参数不会截断")
print("     stop 参数只在模型'创造性生成'新内容时才会检测停止词\n")

print("=== 示例4：bind() 的实际应用场景 ===")
prompt4 = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个代码生成助手"),
        ("human", "写一个 {language} 函数来 {task}"),
    ]
)

# 在代码生成场景中，使用 stop 参数来控制输出边界
chain4 = (
    prompt4
    | llm.bind(
        stop=["```", "---", "注意："], temperature=0.3  # 遇到代码块结束或分隔符停止
    )
    | StrOutputParser()
)

content4 = chain4.invoke({"language": "Python", "task": "计算斐波那契数列"})
print(f"输出: {content4}")
print("说明: 在代码生成中，stop 参数可以防止模型生成过多的解释文本")
