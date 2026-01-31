from langchain_core.output_parsers import StrOutputParser
import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

# 1.编排提示模板
prompt = ChatPromptTemplate.from_template("{query}")

# 2.构建大语言模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 3.创建字符串输出解析器
parser = StrOutputParser()

# 4.调用大语言模型生成结果并解析
content1 = parser.invoke(
    llm.invoke(prompt.invoke({"query": "你好,你是谁？用15个字回答我"}))
)
content2 = llm.invoke(prompt.invoke({"query": "你好,你是谁？用15个字回答我"}))

print(content1)
print("+++++++++++++++++++++++++++++++++")
print(content2)
