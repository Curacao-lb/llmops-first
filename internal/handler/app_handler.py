from flask import request
from openai import APIError, APITimeoutError, APIConnectionError

from internal.schema.app_schema import CompletionReq
from pkg.response import success_json, validate_error_json, fail_json
from internal.exception import CustomException
from internal.service import AppService
from injector import inject
from dataclasses import dataclass
from pkg.response import success_message
import uuid

# LangChain 相关导入
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


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

    def debug(self, app_id: uuid.UUID):
        """
        聊天接口 - 使用 LangChain 实现

        流程: prompt → llm → parser
        """
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 1. 提取用户输入
        query = request.json.get("query")

        # 2. 构建 Prompt 模板
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是OpenAI开发的聊天机器人，请根据用户的输入回复对应的信息",
                ),
                ("human", "{query}"),
            ]
        )

        # 3. 创建 LLM 实例 (会自动读取 OPENAI_API_KEY 和 OPENAI_API_BASE 环境变量)
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            timeout=60.0,  # 超时时间
        )

        # 4. 创建输出解析器 (将 AIMessage 转为纯字符串)
        parser = StrOutputParser()

        # 5. 使用 LCEL 构建链: prompt | llm | parser
        chain = prompt | llm | parser

        try:
            # 6. 执行链，获取结果
            content = chain.invoke({"query": query})
            return success_json({"content": content})

        except APITimeoutError:
            return fail_json({"message": "请求超时，请稍后重试"})
        except APIConnectionError:
            return fail_json({"message": "无法连接到AI服务，请检查网络或稍后重试"})
        except APIError as e:
            return fail_json({"message": f"AI服务异常: {str(e)}"})
