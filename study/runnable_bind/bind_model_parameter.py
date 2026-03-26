import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

# 测试 bind() 方法能否修改模型参数

print("=== 实验：bind() 能否修改 model 参数？ ===\n")

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "请用一句话介绍你自己，包括你的模型名称"),
        ("human", "你是谁？"),
    ]
)

# 创建一个使用 gpt-3.5-turbo 的 LLM 实例
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

print("--- 测试1：不使用 bind()，直接调用 ---")
chain1 = prompt | llm | StrOutputParser()
result1 = chain1.invoke({})
print(f"结果: {result1}\n")

print("--- 测试2：尝试使用 bind(model='gpt-4o') ---")
try:
    # 尝试通过 bind() 修改 model 参数
    llm_with_bind = llm.bind(model="gpt-4-mini")
    chain2 = prompt | llm_with_bind | StrOutputParser()
    result2 = chain2.invoke({})
    print(f"结果: {result2}\n")
except Exception as e:
    print(f"错误: {e}\n")

print("--- 测试3：bind() 实际传递的是什么？ ---")
# bind() 方法会将参数传递给底层的 API 调用
# 但 model 参数在 ChatOpenAI 初始化时就已经确定了
llm_with_bind = llm.bind(model="gpt-4o")
print(f"原始 LLM 的 model: {llm.model_name}")
print(f"bind 后的对象类型: {type(llm_with_bind)}")
# bind() 返回的是 RunnableBinding 对象，它会将额外参数传递给 invoke 方法
print(f"bind() 绑定的参数会作为 kwargs 传递给底层 API\n")

print("=== 结论 ===")
print("1. bind(model='gpt-4o') 不会改变实际使用的模型")
print("2. model 参数在 ChatOpenAI 初始化时就固定了")
print("3. bind() 主要用于绑定运行时参数（如 temperature, max_tokens, stop 等）")
print("4. 如果要使用不同的模型，应该创建新的 ChatOpenAI 实例\n")

print("=== 正确做法：创建新的 LLM 实例 ===")
llm_gpt4 = ChatOpenAI(model="gpt-4o", temperature=0)
chain3 = prompt | llm_gpt4 | StrOutputParser()
result3 = chain3.invoke({})
print(f"使用 gpt-4o 的结果: {result3}\n")

print("=== bind() 的正确用途示例 ===")
# bind() 适合绑定这些运行时参数：
llm_configured = llm.bind(
    temperature=0.7,  # 可以修改
    max_tokens=100,  # 可以修改
    stop=["\n\n"],  # 可以修改
    presence_penalty=0.5,  # 可以修改
)
chain4 = prompt | llm_configured | StrOutputParser()
result4 = chain4.invoke({})
print(f"使用 bind() 配置运行时参数的结果: {result4}")
