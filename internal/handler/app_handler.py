from flask import request, jsonify
from openai import OpenAI, APIError, APITimeoutError, APIConnectionError
import os
import httpx

from internal.schema.app_schema import CompletionReq
from pkg.response import Response, HttpCode


class AppHandler:
    #  应用控制器

    def ping(self):
        return {"ping": "pong"}

    def completion(self):
        """聊天接口"""
        req = CompletionReq()
        if not req.validate():
            return req.errors

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
            resp = Response(
                code=HttpCode.SUCCESS, message="", data={"content": content}
            )
            return jsonify(resp), 200

        except APITimeoutError:
            resp = Response(
                code=HttpCode.INTERNAL_ERROR, message="请求超时，请稍后重试", data=None
            )
            return jsonify(resp), 504
        except APIConnectionError:
            resp = Response(
                code=HttpCode.INTERNAL_ERROR,
                message="无法连接到AI服务，请检查网络或稍后重试",
                data=None,
            )
            return jsonify(resp), 503
        except APIError as e:
            resp = Response(
                code=HttpCode.INTERNAL_ERROR, message=f"AI服务异常: {str(e)}", data=None
            )
            return jsonify(resp), 500
