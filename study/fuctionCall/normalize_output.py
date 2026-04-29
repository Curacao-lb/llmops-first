import dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Literal

dotenv.load_dotenv()


class RouteQuery(BaseModel):
    """将用户查询映射到对应的数据源上"""

    datasource: Literal["python_docs", "js_docs", "golang_docs"] = Field(
        description="根据用户的问题,选择哪个数据源最相关以回答用户的问题"
    )


llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
structured_llm = llm.with_structured_output(
    RouteQuery,
    method="json_mode",
)

question = """
请帮我检查一下为什么下面的代码不工作了

var 1a = 123
"""

res = structured_llm.invoke(
    [
        SystemMessage(
            content=(
                "你是一个查询路由器。根据用户问题选择最相关的数据源。"
                "必须只输出一个 JSON 对象，不要输出解释文字。"
                "JSON 格式必须是："
                '{"datasource":"python_docs|js_docs|golang_docs"}'
            )
        ),
        HumanMessage(content=question),
    ]
)
print(res)
