"""app_handler 模块：应用相关的 HTTP 接口处理器。

提供应用的增删改查，以及基于 LangChain / LangGraph 的聊天调试、
带记忆的聊天调试与流式（SSE）聊天调试等接口。
"""

import json
import os
import uuid
from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Any

from flask import request
from flask_login import current_user, login_required
from injector import inject
from langchain_core.messages import HumanMessage, trim_messages
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from openai import APIError, APITimeoutError, APIConnectionError

from internal.core.agent.agents import FunctionCallAgent
from internal.core.agent.entities.agent_entity import AgentConfig
from internal.extension.chinese_file_chat_history import ChineseFileChatMessageHistory
from internal.schema.app_schema import (
    GetAppsWithPageReq,
    GetAppsWithPageResp,
    CreateAppReq,
)
from internal.service import AppService
from pkg.paginator import PageModel
from pkg.response import (
    compact_generate_response,
    fail_json,
    success_json,
    success_message,
    validate_error_json,
)


@inject
@dataclass
class AppHandler:
    """应用控制器：处理应用的增删改查与会话调试相关接口。"""

    app_service: AppService

    @login_required
    def ping(self):
        # """调试接口：基于示例问题生成建议问题列表，用于联调验证。"""
        pass

    @login_required
    def create_app(self):
        """调用服务创建新的APP记录"""

        # 1.提取请求并校验
        req = CreateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 2.调用服务创建应用信息
        app = self.app_service.create_app(req, account=current_user)
        return success_json({"id": app.id})

    @login_required
    def get_app(self, app_id: uuid.UUID):
        """根据应用 id 查询应用记录。"""
        app = self.app_service.get_app(app_id, account=current_user)
        return success_json(f"应用已经成功查询了,id为{app.id}")
