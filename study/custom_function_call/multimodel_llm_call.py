import json
import os
from typing import Any, Optional, Type

import dotenv
import requests
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


dotenv.load_dotenv()


class GaodeWeatherArgsSchema(BaseModel):
    city: str = Field(description="需要查询天气预报的目标城市，例如：三亚")


class GaodeWeatherTool(BaseTool):
    """通过城市名称查询天气预报"""

    name: str = "gaode_weather"
    description: str = "当你想询问天气或与天气相关的问题时的工具"
    args_schema: Type[BaseModel] = GaodeWeatherArgsSchema

    def _run(
        self,
        city: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """查询指定城市未来几天的天气预报。"""

        session = requests.session()
        try:
            gaode_api_key = os.getenv("AMAP_API_KEY")
            if not gaode_api_key:
                return "高德开放平台 API Key 未配置"

            api_domain = "https://restapi.amap.com/v3"
            headers = {"Content-Type": "application/json; charset=utf-8"}

            city_response = session.request(
                method="GET",
                url=(
                    f"{api_domain}/config/district?"
                    f"keywords={city}&subdistrict=0&extensions=all&key={gaode_api_key}"
                ),
                headers=headers,
            )
            city_response.raise_for_status()
            city_data = city_response.json()

            if city_data.get("info") == "OK":
                districts = city_data.get("districts", [])
                if len(districts) > 0:
                    ad_code = districts[0].get("adcode")
                    weather_response = session.request(
                        method="GET",
                        url=(
                            f"{api_domain}/weather/weatherInfo?"
                            f"city={ad_code}&extensions=all&key={gaode_api_key}&output=json"
                        ),
                        headers=headers,
                    )
                    weather_response.raise_for_status()
                    weather_data = weather_response.json()
                    if weather_data.get("info") == "OK":
                        return json.dumps(weather_data, ensure_ascii=False)

            return f"获取{city}天气预报信息失败"
        except Exception:
            return f"获取{city}天气预报信息失败"
        finally:
            session.close()


# 1.构建prompt
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            [
                {"type": "text", "text": "请获取上传图片所在城市的天气预报"},
                {"type": "image_url", "image_url": {"url": "{image_url}"}},
            ],
        )
    ]
)

weather_prompt = ChatPromptTemplate.from_template(
    """请整理下传递的城市的天气预报信息,并以用户友好的方式输出

    <weather>
    {weather}
    <weather/>
    """
)

# 2.构建LLM并绑定工具
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools=[GaodeWeatherTool()], tool_choice="gaode_weather")

# 3.创建链应用并执行
sub_chain = (
    {"image_url": RunnablePassthrough()}
    | prompt
    | llm_with_tools
    | (lambda msg: msg.tool_calls[0]["args"])
    | GaodeWeatherTool()
)
chain = {"weather": sub_chain} | weather_prompt | llm | StrOutputParser()

print(
    chain.invoke(
        "https://qcloud.dpfile.com/pc/Z-KcN-8M1_5rs0EyyYuxjuDkbTZoH_uXkWX36fcK06mqZAE3BvNJoWAgKtYkjAMe.jpg"
    )
)
