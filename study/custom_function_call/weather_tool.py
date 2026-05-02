import asyncio
import os
from typing import Any, Optional, Type

import requests
import dotenv
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


dotenv.load_dotenv()


class WeatherToolInput(BaseModel):
    """天气预报工具的入参。"""

    city: str = Field(description="需要查询天气预报的城市名，例如：北京、上海、深圳")


class WeatherTool(BaseTool):
    """通过城市名称查询天气预报。"""

    name: str = "weather_tool"
    description: str = (
        "根据城市名查询天气预报。工具会先调用高德地图行政区域查询接口获取城市行政编码，"
        "再使用行政编码调用天气预报接口返回天气信息。"
    )
    args_schema: Type[BaseModel] = WeatherToolInput
    return_direct: bool = True

    amap_api_key: Optional[str] = Field(
        default=None,
        description="高德开放平台 API Key，未传入时读取 AMAP_API_KEY 或 GAODE_API_KEY 环境变量",
    )
    request_timeout: int = 10

    district_url: str = "https://restapi.amap.com/v3/config/district"
    weather_url: str = "https://restapi.amap.com/v3/weather/weatherInfo"

    def _run(
        self,
        city: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """同步调用工具。"""

        api_key = self._get_api_key()
        district = self._get_district(city=city, api_key=api_key)
        adcode = district["adcode"]
        weather = self._get_weather(adcode=adcode, api_key=api_key)
        return self._format_weather(city=city, district=district, weather=weather)

    async def _arun(
        self,
        city: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """异步调用工具。"""

        return await asyncio.to_thread(self._run, city)

    def _get_api_key(self) -> str:
        api_key = self.amap_api_key or os.getenv("AMAP_API_KEY") or os.getenv("GAODE_API_KEY")
        if not api_key:
            raise ValueError(
                "缺少高德开放平台 API Key，请设置环境变量 AMAP_API_KEY/GAODE_API_KEY，"
                "或在初始化 WeatherTool(amap_api_key='你的key') 时传入。"
            )
        return api_key

    def _get_district(self, city: str, api_key: str) -> dict[str, Any]:
        params = {
            "key": api_key,
            "keywords": city,
            "subdistrict": 0,
            "extensions": "base",
        }
        data = self._request_json(self.district_url, params=params)
        districts = data.get("districts") or []
        if not districts:
            raise ValueError(f"未查询到城市 {city} 对应的行政区域信息。")

        district = districts[0]
        adcode = district.get("adcode")
        if not adcode:
            raise ValueError(f"未查询到城市 {city} 对应的行政编码。")
        return district

    def _get_weather(self, adcode: str, api_key: str) -> dict[str, Any]:
        params = {
            "key": api_key,
            "city": adcode,
            "extensions": "all",
        }
        return self._request_json(self.weather_url, params=params)

    def _request_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        response = requests.get(url, params=params, timeout=self.request_timeout)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1":
            info = data.get("info") or "未知错误"
            info_code = data.get("infocode") or "unknown"
            raise ValueError(f"接口调用失败：{info}，错误码：{info_code}")

        return data

    def _format_weather(
        self,
        city: str,
        district: dict[str, Any],
        weather: dict[str, Any],
    ) -> str:
        forecasts = weather.get("forecasts") or []
        if not forecasts:
            raise ValueError(f"未查询到城市 {city} 的天气预报信息。")

        forecast = forecasts[0]
        province = forecast.get("province") or district.get("name") or ""
        report_city = forecast.get("city") or district.get("name") or city
        report_time = forecast.get("reporttime") or "未知时间"
        casts = forecast.get("casts") or []

        lines = [
            f"{province}{report_city}天气预报",
            f"发布时间：{report_time}",
        ]

        for cast in casts:
            date = cast.get("date", "")
            week = cast.get("week", "")
            day_weather = cast.get("dayweather", "")
            night_weather = cast.get("nightweather", "")
            day_temp = cast.get("daytemp", "")
            night_temp = cast.get("nighttemp", "")
            day_wind = cast.get("daywind", "")
            day_power = cast.get("daypower", "")
            night_wind = cast.get("nightwind", "")
            night_power = cast.get("nightpower", "")

            lines.append(
                (
                    f"{date} 周{week}：白天{day_weather}，{day_temp}℃，"
                    f"{day_wind}风{day_power}级；夜间{night_weather}，"
                    f"{night_temp}℃，{night_wind}风{night_power}级"
                )
            )

        return "\n".join(lines)


weather_tool = WeatherTool()


if __name__ == "__main__":
    print("名称:", weather_tool.name)
    print("描述:", weather_tool.description)
    print("参数:", weather_tool.args)
    print("直接返回:", weather_tool.return_direct)
    print(weather_tool.invoke({"city": "北京"}))
