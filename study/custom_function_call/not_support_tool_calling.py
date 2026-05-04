import dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools.render import render_text_description_and_args
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


# 2.将工具描述渲染成适合放进prompt的文本
tools_description = render_text_description_and_args(tools)


# 3.创建prompt，把工具描述放到提示词中，让不支持函数调用的模型自己输出JSON
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个可以使用工具的智能助手，但当前模型不支持原生函数调用。"
            "你需要根据用户问题和工具列表，判断是否需要调用工具。"
            "如果需要调用工具，只输出JSON，不要输出任何解释。"
            "JSON格式："
            '{"name": "工具名称", "args": {"参数名": "参数值"}}。'
            "如果不需要调用工具，只输出JSON："
            '{"name": null, "args": {}, "answer": "直接回答内容"}。'
            "可用工具列表：\n{tools_description}",
        ),
        ("human", "{query}"),
    ]
)


# 4.创建大语言模型和链应用，不使用bind_tools
llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
parser = JsonOutputParser()
chain = (
    {
        "query": RunnablePassthrough(),
        "tools_description": lambda _: tools_description,
    }
    | prompt
    | llm
    | parser
)


# 5.调用链应用，获取模型输出的工具调用意图
query = "贵阳现在天气怎么样，有什么时候穿的衣服呢？"
tool_call = chain.invoke(query)
print("模型输出：", tool_call)


# 6.判断是工具调用还是正常输出结果
if not tool_call.get("name"):
    print("生成内容：", tool_call.get("answer"))
else:
    # 7.执行工具，并把工具结果再次传给大模型生成最终回答
    tool = tool_dict.get(tool_call.get("name"))
    if tool is None:
        raise ValueError(f"未找到工具：{tool_call.get('name')}")

    print("正在执行工具：", tool.name)
    content = tool.invoke(tool_call.get("args"))
    print("工具返回结果：", content)

    final_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个智能助手，请基于工具返回结果，用中文回答用户问题。",
            ),
            ("human", "用户问题：{query}\n工具返回结果：{content}"),
        ]
    )
    final_chain = final_prompt | llm
    final_message = final_chain.invoke({"query": query, "content": content})
    print("输出内容：", final_message.content)
