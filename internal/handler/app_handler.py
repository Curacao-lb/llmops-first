"""app_handler 模块：应用相关的 HTTP 接口处理器。

提供应用的增删改查，以及基于 LangChain / LangGraph 的聊天调试、
带记忆的聊天调试与流式（SSE）聊天调试等接口。
"""

import uuid
from dataclasses import dataclass

from flask import request
from flask_login import current_user, login_required
from injector import inject

from internal.schema.app_schema import (
    CreateAppReq,
    GetAppResp,
    GetPublishHistoriesWithPageReq,
    GetPublishHistoriesWithPageResp,
)
from internal.service import AppService
from pkg.paginator import PageModel
from pkg.response import (
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
        """探活接口：返回固定的 pong 响应，用于联调验证服务是否正常。"""
        return success_message("pong")

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
        """获取指定的应用基础信息"""
        # 1.获取应用基础信息
        app = self.app_service.get_app(app_id, account=current_user)
        # 2.确保草稿配置存在：只读属性不再自动创建，这里显式执行「取不到就创建」
        self.app_service.get_draft_app_config_in_get_app(app)
        # 3.序列化并返回应用基础信息
        resp = GetAppResp()
        return success_json(resp.dump(app))

    @login_required
    def get_draft_app_config(self, app_id: uuid.UUID):
        """根据传递的应用id获取应用的最新草稿配置"""
        return success_json(
            self.app_service.get_draft_app_config(app_id, account=current_user)
        )

    @login_required
    def update_draft_app_config(self, app_id: uuid.UUID):
        """根据传递的应用id+草稿配置更新应用的最新草稿配置"""

        # 1.获取草稿请求的json数据
        draft_app_config = request.get_json(force=True, silent=True) or {}
        self.app_service.update_draft_app_config(
            app_id, draft_app_config, account=current_user
        )

        # draft_app_config = self.app_service._validate_draft_app_config(
        #     draft_app_config, current_user
        # )

        return success_message("更新应用草稿配置成功")
        # return success_json(draft_app_config)

    @login_required
    def publish(self, app_id: uuid.UUID):
        """发布/更新应用"""

        self.app_service.publish_draft_app_config(app_id, account=current_user)
        return success_message("发布/更新应用配置成功")

    @login_required
    def cancel_publish(self, app_id: uuid.UUID):
        """根据传递的应用id,取消发布指定的应用配置信息"""
        self.app_service.cancel_publish_app_config(app_id, current_user)
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
                app_id, req, account=current_user
            )
        )
        resp = GetPublishHistoriesWithPageResp(many=True)
        return success_json(
            PageModel(list=resp.dump(app_config_versions), paginator=paginator)
        )
