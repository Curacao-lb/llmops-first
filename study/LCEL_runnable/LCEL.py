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

# 2.创建链
chain = prompt | llm | parser

# 3.执行链并获取结果
print(chain.invoke({"query": "请讲一个程序员的中式冷笑话"}))
