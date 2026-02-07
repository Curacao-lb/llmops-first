import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel

dotenv.load_dotenv()


def retrieval(query: str) -> str:
    """一个模拟的检索器函数"""
    print(f"正在检索{query}")
    return "我是Robin"


# 1.编排prompt
prompt = ChatPromptTemplate.from_template(
    """请根据用户的问题回答，可以参考对应的上下文进行生成

<context>
{context}
</context>

用户的提问是：{query}
"""
)

# 2.构建大语言模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 3.构建输出解析器
parser = StrOutputParser()

# 4.构建链
# 这里不写 runnable 也可以，管道运算符会将前面的数据转换为runnable
chain = (
    RunnableParallel(
        {"context": lambda x: retrieval(x["query"]), "query": lambda x: x["query"]}
    )
    | prompt
    | llm
    | parser
)

# 5.调用链
content = chain.invoke({"query": "你好"})

print(content)
