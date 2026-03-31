import dotenv

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import ConfigurableField

dotenv.load_dotenv()

# 1.创建提示模板
prompt = PromptTemplate.from_template("请生成一个小于{x}的随机整数")

# 2.创建LLM大语言模型,并配置temperature参数为可在运行时配置,配置键位llm_temperature
llm = ChatOpenAI(model="gpt-3.5-turbo-16k").configurable_fields(
    temperature=ConfigurableField(
        id="llm_temperature",
        name="大语言模型的温度",
        description="温度越低,大语言模型生成的内容越确定,温度越高,生成内容越随机",
    )
)

# 3.构建链应用
chain = prompt | llm | StrOutputParser()

# 4.正常调用内容
# 4.1 写法1
# content = chain.invoke({"x": 100}, config={"configurable": {"llm_temperature": 0}})
# 4.2 写法2
content = chain.with_config(config={"llm_temperature": 0}).invoke({"x": 1000})
print(content)
