import dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field


dotenv.load_dotenv()


class TavilySearchArgsSchema(BaseModel):
    query: str = Field(description="执行实时搜索的查询语句")


# 1.定义工具与工具列表
tavily_search = TavilySearch(
    name="tavily_search",
    description=(
        "一个用于实时互联网信息搜索的工具。"
        "当你需要查询新闻、实时事件、互联网资料、最新信息或普通网页内容时，可以使用该工具。"
        "该工具的输入是搜索查询语句。"
    ),
    args_schema=TavilySearchArgsSchema,
    max_results=5,
    topic="general",
)

tools = [tavily_search]


# 2.定义智能体提示模板
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个可以调用工具的智能助手。"
            "当用户询问最新信息、实时事件、新闻或网页资料时，请调用搜索工具。"
            "工具返回结果后，请基于工具结果用中文回答用户。",
        ),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


# 3.创建大语言模型与工具调用智能体
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)


# 4.创建智能体执行体
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
)


# 5.执行智能体并检索
if __name__ == "__main__":
    result = agent_executor.invoke({"input": "马拉松世界纪录是多少？"})
    print(result["output"])
