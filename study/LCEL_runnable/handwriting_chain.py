import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from typing import Any


dotenv.load_dotenv()

# 1.构建组件
prompt = ChatPromptTemplate.from_template("{query}")
llm = ChatOpenAI(model="gpt-3.5-turbo")
parser = StrOutputParser()


# 正常情况下我们只需要将上面三个组件构成一个列表
# 因此我们封装成一个Chain的类 - 2.定义一个链
class Chain:
    steps: list = []

    # 构造函数
    def __init__(self, steps: list):
        self.steps = steps

    # 写一个自定义的invoke方法
    def customInvoke(self, input: Any) -> Any:
        for step in self.steps:
            input = step.invoke(input)
            print("步骤：", step)
            print("输出：", input)
            print("============================")
        return input


# 然后实例化- 3. 编排链
chain = Chain([prompt, llm, parser])

# 4.执行链并获取结果
print(chain.customInvoke({"query": "你好，你是？"}))
