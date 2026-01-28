from flask import request
from openai import OpenAI, APIError, APITimeoutError, APIConnectionError
import os
import httpx

from internal.schema.app_schema import CompletionReq
from pkg.response import success_json, validate_error_json, fail_json
from internal.exception import CustomException
from internal.service import AppService
from injector import inject
from dataclasses import dataclass
from pkg.response import success_message
import uuid


@inject
@dataclass
class AppHandler:
    #  应用控制器
    app_service: AppService

    def ping(self):
        # raise CustomException("数据未找到")
        return {"ping": "pong"}

    def create_app(self):
        """调用服务创建新的APP记录"""
        app = self.app_service.create_app()
        return success_message(f"应用已经成功创建了,id为{app.id}")

    def get_app(self, id: uuid.UUID):
        app = self.app_service.get_app(id)
        return success_json(
            f"应用已经成功查询了,id为{app.id}"
        )  # 直接传模型对象,Flask 会自动序列化

    def update_app(self, id: uuid.UUID):
        app = self.app_service.update_app(id)
        return success_json(f"应用已经成功更新了,id为{app.id}，名字为{app.name}")

    def delete_app(self, id: uuid.UUID):
        result = self.app_service.delete_app(id)
        if result:
            return success_message(f"应用已经成功删除了, id为{id}")
        else:
            return fail_json({"message": "应用不存在或删除失败"})

    def completion(self):
        """聊天接口"""
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 1.提取从接口中获取的输入，假定是post
        query = request.json.get("query")
        # 2.构建openAI客户端，并发起请求（设置超时时间）
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            timeout=httpx.Timeout(60.0, connect=10.0),  # 总超时60秒，连接超时10秒
        )

        try:
            # 3.得到请求响应，然后将openAI得到的响应传递给前端
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "你是OpenAI开发的聊天机器人，请根据用户的输入回复对应的信息",
                    },
                    {"role": "user", "content": query},
                ],
            )
            # 消息的内容
            content = completion.choices[0].message.content
            return success_json({"content": content})

        except APITimeoutError:
            return fail_json({"message": "请求超时，请稍后重试"})
        except APIConnectionError:
            return fail_json({"message": "无法连接到AI服务，请检查网络或稍后重试"})
        except APIError as e:
            return fail_json({"message": f"AI服务异常: {str(e)}"})
