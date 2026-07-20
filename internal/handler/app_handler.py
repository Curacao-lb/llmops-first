"""app_handler 模块：应用相关的 HTTP 接口处理器。

提供应用的增删改查，以及基于 LangChain / LangGraph 的聊天调试、
带记忆的聊天调试与流式（SSE）聊天调试等接口。
"""

import uuid
from dataclasses import dataclass
from typing import Any, cast

from flask import current_app, request
from flask_login import current_user, login_required
from injector import inject

from internal.model import Account
from internal.schema.app_schema import (
    CreateAppReq,
    DebugChatReq,
    FallbackHistoryToDraftReq,
    GetAppResp,
    GetPublishHistoriesWithPageReq,
    GetPublishHistoriesWithPageResp,
    UpdateDebugConversationSummaryReq,
)
from internal.service import AppService, RetrievalService
from pkg.paginator import PageModel
from pkg.response import (
    success_json,
    success_message,
    validate_error_json,
)
from pkg.response.response import compact_generate_response


@inject
@dataclass
class AppHandler:
    """应用控制器：处理应用的增删改查与会话调试相关接口。"""

    app_service: AppService
    retrieval_service: RetrievalService

    @login_required
    def ping(self):
        """探活接口：返回固定的 pong 响应，用于联调验证服务是否正常。"""
        from internal.entity.dataset_entity import RetrievalSource, RetrievalStrategy

        account = cast(Account, current_user)
        dataset_retrieval = self.retrieval_service.create_langchain_tool_from_search(
            flask_app=current_app,
            dataset_ids=[
                uuid.UUID("854ba4fa-51d9-40be-8f38-57d6e3e72ad4"),
                uuid.UUID("9c58c437-0375-4fdc-b6e5-c1ee3387caf9"),
            ],
            account_id=cast(uuid.UUID, account.id),
            retrieval_strategy=RetrievalStrategy.SEMANTIC,
            k=10,
            score=0.5,
            retrival_source=RetrievalSource.HIT_TESTING,
        )

        print("工具名称：", dataset_retrieval.name)
        print("工具描述：", dataset_retrieval.description)
        print("工具参数：", dataset_retrieval.args)

        content = dataset_retrieval.invoke({"query": "能简单介绍一下什么是LLMOps吗"})

        return success_json({"content": content})

    @login_required
    def create_app(self):
        """调用服务创建新的APP记录"""

        # 1.提取请求并校验
        req = CreateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 2.调用服务创建应用信息
        app = self.app_service.create_app(req, account=cast(Account, current_user))
        return success_json({"id": app.id})

    @login_required
    def get_app(self, app_id: uuid.UUID):
        """获取指定的应用基础信息"""
        # 1.获取应用基础信息
        app = self.app_service.get_app(app_id, account=cast(Account, current_user))
        # 2.确保草稿配置存在：只读属性不再自动创建，这里显式执行「取不到就创建」
        self.app_service.get_draft_app_config_in_get_app(app)
        # 3.序列化并返回应用基础信息
        resp = GetAppResp()
        return success_json(resp.dump(app))

    @login_required
    def get_draft_app_config(self, app_id: uuid.UUID):
        """根据传递的应用id获取应用的最新草稿配置"""
        return success_json(
            self.app_service.get_draft_app_config(
                app_id, account=cast(Account, current_user)
            )
        )

    @login_required
    def update_draft_app_config(self, app_id: uuid.UUID):
        """根据传递的应用id+草稿配置更新应用的最新草稿配置"""

        # 1.获取草稿请求的json数据
        draft_app_config = request.get_json(force=True, silent=True) or {}
        self.app_service.update_draft_app_config(
            app_id, draft_app_config, account=cast(Account, current_user)
        )

        # draft_app_config = self.app_service._validate_draft_app_config(
        #     draft_app_config, current_user
        # )

        return success_message("更新应用草稿配置成功")
        # return success_json(draft_app_config)

    @login_required
    def publish(self, app_id: uuid.UUID):
        """发布/更新应用"""

        self.app_service.publish_draft_app_config(
            app_id, account=cast(Account, current_user)
        )
        return success_message("发布/更新应用配置成功")

    @login_required
    def cancel_publish(self, app_id: uuid.UUID):
        """根据传递的应用id,取消发布指定的应用配置信息"""
        self.app_service.cancel_publish_app_config(app_id, cast(Account, current_user))
        return success_message("取消发布应用成功")

    @login_required
    def get_publish_histories_with_page(self, app_id: uuid.UUID):
        """根据传递的应用id获取应用发布历史列表"""
        # 1.获取请求数据并校验
        req = GetPublishHistoriesWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务获取分页列表数据
        app_config_versions, paginator = (
            self.app_service.get_publish_histories_with_page(
                app_id, req, account=cast(Account, current_user)
            )
        )
        resp = GetPublishHistoriesWithPageResp(many=True)
        return success_json(
            PageModel(
                list=cast(list[Any], resp.dump(app_config_versions)),
                paginator=paginator,
            )
        )

    @login_required
    def fallback_history_to_draft(self, app_id: uuid.UUID):
        """根据传递的应用id+历史配置版本id,退回指定版本到草稿中"""

        # 1.提取数据并校验
        req = FallbackHistoryToDraftReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 2.调用服务回退指定版本到草稿
        self.app_service.fallback_history_to_draft(
            app_id,
            uuid.UUID(cast(str, req.app_config_version_id.data)),
            account=cast(Account, current_user),
        )
        return success_message("回退历史配置到草稿成功")

    @login_required
    def get_debug_conversation_summary(self, app_id: uuid.UUID):
        """根据传递的应用id获取调试会话长期记忆"""

        summary = self.app_service.get_debug_conversation_summary(
            app_id, account=cast(Account, current_user)
        )
        return success_json({"summary": summary})

    @login_required
    def update_debug_conversation_summary(self, app_id: uuid.UUID):
        """根据传递的应用id+摘要信息更新调试会话长期记忆"""

        # 1.提取数据并校验
        req = UpdateDebugConversationSummaryReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务更新调试会话长期记忆
        self.app_service.update_debug_conversation_summary(
            app_id,
            cast(str, req.summary.data),
            account=cast(Account, current_user),
        )
        return success_message("更新AI应用长期记忆成功")

    @login_required
    def delete_debug_conversation(self, app_id: uuid.UUID):
        """根据传递的应用id，清空该应用的调试会话记录"""

        self.app_service.delete_debug_conversation(
            app_id,
            account=cast(Account, current_user),
        )
        return success_message("清空应用调试会话记录成功")

    @login_required
    def debug_chat(self, app_id: uuid.UUID):
        """根据传递的应用id+query，发起调试对话"""
        # 1.提取数据并校验数据
        req = DebugChatReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务发起会话调试
        response = self.app_service.debug_chat(
            app_id, req, account=cast(Account, current_user)
        )
        return compact_generate_response(response)
