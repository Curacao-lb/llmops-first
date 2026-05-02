import dotenv
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

try:
    from study.custom_function_call.weather_tool import weather_tool
except ModuleNotFoundError:
    from weather_tool import weather_tool


dotenv.load_dotenv()


# 1.定义工具列表（高德天气 + Tavily实时搜索）
tavily_search_tool = TavilySearch(
    name="tavily_search_tool",
    description="用于实时互联网信息搜索，适合查询新闻、最新事件、网页资料或外部知识。",
    max_results=5,
    topic="general",
)

tools = [weather_tool, tavily_search_tool]
tool_dict = {tool.name: tool for tool in tools}


# 2.创建prompt（包含系统消息、人类消息）
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个可以调用工具的智能助手。"
            "当用户询问天气、温度、穿衣建议时，必须调用天气预报工具；"
            "当用户询问实时新闻、最新资料、网页内容时，必须调用实时搜索工具。"
            "工具返回结果后，请基于工具结果用中文回答用户。",
        ),
        ("human", "{query}"),
    ]
)


# 3.创建大语言模型并绑定工具
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_with_tool = llm.bind_tools(tools, tool_choice="auto")


# 4.创建链应用，使用RunnablePassthrough
chain = {"query": RunnablePassthrough()} | prompt | llm_with_tool


# 5.调用链应用，并获取输出响应
# query = "贵阳现在天气怎么样，有什么时候穿的衣服呢？"
query = "帮我调用工具马拉松的世界记录是多少?"
response = chain.invoke(query)
tool_calls = response.tool_calls


# 6.1判断是工具调用还是正常输出结果，如果是正常输出结果就直接print .content
if len(tool_calls) <= 0:
    print("生成内容：", response.content)
else:
    # 6.2如果是工具调用的话，将历史的系统消息、人类消息、AI消息组合
    messages = prompt.invoke({"query": query}).to_messages()
    messages.append(response)

    # 7.循环遍历所有工具并调用信息
    for tool_call in tool_calls:
        tool = tool_dict.get(tool_call.get("name"))
        if tool is None:
            raise ValueError(f"未找到工具：{tool_call.get('name')}")

        print("正在执行工具: ", tool.name)
        content = tool.invoke(tool_call.get("args"))
        print("工具返回结果: ", content)

        tool_call_id = tool_call.get("id")
        messages.append(
            ToolMessage(
                content=str(content),
                tool_call_id=tool_call_id,
            )
        )

    print("输出内容: ", llm_with_tool.invoke(messages).content)
