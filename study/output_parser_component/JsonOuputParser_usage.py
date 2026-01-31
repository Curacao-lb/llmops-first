from langchain_core.output_parsers import JsonOutputParser
import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

dotenv.load_dotenv()

# 1.创建一个json数据结构，用于告诉大语言模型这个json长什么样子


class Joke(BaseModel):
    # 冷笑话
    joke: str = Field(description="冷笑话")
    # 冷笑话的笑点
    punchline: str = Field(description="冷笑话的笑点")


parser = JsonOutputParser(pydantic_object=Joke)
print(parser.get_format_instructions())
print("+++++++++++++++++++++++++++++++++++++")

# 2.构建一个提示模板
prompt = ChatPromptTemplate.from_template(
    "请根据用户的提问进行回答。\n{format_instruction}\n{query}"
).partial(format_instruction=parser.get_format_instructions())

print(prompt)
print("+++++++++++++++++++++++++++++++++++++")

# 3.构建openAI大语言模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 4.传递提示并进行解析
joke = parser.invoke(llm.invoke(prompt.invoke({"query": "讲一个关于程序员的冷笑话"})))

print(joke)
# 这里的打印结果：
# {
# 'joke': '程序员最讨厌去医院，因为医生一开口就说：“我们先重启试试。”',
# 'punchline': '程序员发现，原来不只电脑靠重启。'
# }
