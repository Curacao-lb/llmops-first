import dotenv
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import render_text_description_and_args

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
prompt = ChatPromptTemplate.from_template(
    """
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""
)

# 3.创建大语言模型与智能体
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = create_react_agent(
    llm=llm, tools=tools, prompt=prompt, tools_renderer=render_text_description_and_args
)

# 4.创建智能体执行体
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

# 5.执行智能体并检索
result = agent_executor.invoke({"input": "马拉松世界纪录是多少？"})

print(result["output"])
