import dotenv
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper


dotenv.load_dotenv()


search = GoogleSerperAPIWrapper()

google_serper_tool = GoogleSerperRun(
    name="google_serper_tool",
    description=(
        "一个用于谷歌实时信息搜索的工具。当需要查询新闻、实时事件、互联网资料、"
        "最新信息或普通网页内容时，可以调用该工具。"
    ),
    api_wrapper=search,
)


if __name__ == "__main__":
    print("名称:", google_serper_tool.name)
    print("描述:", google_serper_tool.description)
    print("参数:", google_serper_tool.args)
    print("直接返回:", google_serper_tool.return_direct)
    print(google_serper_tool.invoke("LangChain GoogleSerperRun 是什么"))
