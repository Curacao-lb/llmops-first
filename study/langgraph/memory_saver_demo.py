import dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

dotenv.load_dotenv()

# 1. 创建大语言模型
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# 2. 定义工具
@tool
def get_weather(location: str) -> str:
    """获取指定位置的天气信息"""
    weather_data = {
        "北京": "晴天，温度 25°C",
        "上海": "多云，温度 28°C",
        "深圳": "雨天，温度 26°C",
    }
    return weather_data.get(location, "未知位置")


@tool
def get_time(timezone: str) -> str:
    """获取指定时区的时间"""
    time_data = {
        "UTC": "2024-01-15 12:00:00",
        "CST": "2024-01-15 20:00:00",
        "EST": "2024-01-15 07:00:00",
    }
    return time_data.get(timezone, "未知时区")


tools = [get_weather, get_time]

# 3. 创建内存检查点
memory = MemorySaver()

# 4. 使用 create_react_agent 创建 ReAct 智能体
agent = create_react_agent(model=model, tools=tools, checkpointer=memory)

# 5. 第一次调用智能体并输出结果
print("=" * 80)
print("第一次调用：询问天气和时间")
print("=" * 80)
result1 = agent.invoke(
    {"messages": [("human", "你好，我想了解一下北京的天气，还有 UTC 时区的时间")]},
    config={"configurable": {"thread_id": "user_123"}},
)
print(result1)

# 6. 二次调用检测图结构是否存在在记忆
print("\n" + "=" * 80)
print("第二次调用：基于之前的对话继续提问")
print("=" * 80)
result2 = agent.invoke(
    {"messages": [("human", "你知道我刚才问了什么吗？")]},
    config={"configurable": {"thread_id": "user_123"}},
)
print(result2)
