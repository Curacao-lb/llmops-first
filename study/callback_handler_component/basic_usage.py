import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import StdOutCallbackHandler

dotenv.load_dotenv()

# 1.编排prompt
prompt = ChatPromptTemplate.from_template("{query}")

# 2.创建大语言模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 3.创建链
chain = {"query": RunnablePassthrough()} | prompt | llm | StrOutputParser()

# 4.运行
result = chain.invoke("你好，你是？", config={"callbacks": [StdOutCallbackHandler()]})
print(result)
