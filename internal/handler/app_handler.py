from flask import request
from openai import OpenAI
import os

from internal.schema.app_schema  import CompletionReq

class AppHandler:
    #  应用控制器

    def ping(self):
        return {'ping': 'pong'}

    def completion(self):
        """聊天接口"""
        req = CompletionReq()
        if not req.validate():
            return req.errors

        # 1.提取从接口中获取的输入，假定是post
        query = request.json.get('query')
        # 2.构建openAI客户端，并发起请求
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_API_BASE')
        )
        # 3.得到请求响应，然后将openAI得到的响应传递给前端
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo", # 如果这个上下文长度不够多的话，你也可以使用gpt-3.5-turbo-16K也可以。 
            messages=[
                # 第一条消息角色必定是系统消息
                {"role": "system", "content": "你是OpenAI开发的聊天机器人，请根据用户的输入回复对应的信息"},
                # 输入用户的消息
                {"role": "user", "content": query}
            ]
        )
        # 消息的内容
        content = completion.choices[0].message.content

        # 然后将接口的消息返回给前端
        return content