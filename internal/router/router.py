from dataclasses import dataclass

from flask import Blueprint, Flask, send_from_directory
from injector import inject

# 使用魔术变量（__all__），这里就可以导入 AppHandler
from internal.handler import (
    AccountHandler,
    AIHandler,
    ApiKeyHandler,
    ApiToolHandler,
    AppHandler,
    AuthHandler,
    BuiltinToolHandler,
    DatasetHandler,
    OAuthHandler,
    OpenAPIHandler,
    UploadFileHandler,
    WorkflowHandler,
)
from internal.handler.builtin_app_handler import BuiltinAppHandler
from internal.service import CosService


# dataclass 可以自动生成 __init__，减少样板代码，替代下方注释掉的手写 __init__。
@inject
@dataclass
class Router:
    """路由"""

    app_handler: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler
    dataset_handler: DatasetHandler
    oauth_handler: OAuthHandler
    account_handler: AccountHandler
    auth_handler: AuthHandler
    upload_file_handler: UploadFileHandler
    ai_handler: AIHandler
    api_key_handler: ApiKeyHandler
    openapi_handler: OpenAPIHandler
    builtin_app_handler: BuiltinAppHandler
    workflow_handler: WorkflowHandler

    """
    dataclass 自动生成 __init__ 和 self.app_handler
    """

    # @inject
    # def __init__(self, app_handler: AppHandler):
    #     self.app_handler = app_handler

    def register_router(self, app: Flask):
        """注册路由"""
        # 1.创建一个蓝图 - 可以看成是一组路由的集合
        bp = Blueprint("llmops", __name__, url_prefix="")
        openapi_bp = Blueprint("openapi", __name__, url_prefix="")

        # 2.使用依赖注入的 app_handler,不需要手动创建
        # self.app_handler 已经通过 @inject 和 @dataclass 自动注入了

        # 3.将这个BP蓝图还有对应的路由，在控制器里的方法进行映射
        bp.add_url_rule("/ping", view_func=self.app_handler.ping, methods=["GET"])

        bp.add_url_rule(
            "/apps", view_func=self.app_handler.create_app, methods=["POST"]
        )

        # 获取应用分页列表数据
        bp.add_url_rule(
            "/apps",
            endpoint="get_apps_with_page",
            view_func=self.app_handler.get_apps_with_page,
            methods=["GET"],
        )

        bp.add_url_rule("/apps/<uuid:app_id>", view_func=self.app_handler.get_app)

        # 更新指定应用信息
        bp.add_url_rule(
            "/apps/<uuid:app_id>",
            methods=["POST"],
            view_func=self.app_handler.update_app,
        )

        # 删除指定应用
        bp.add_url_rule(
            "/apps/<uuid:app_id>/delete",
            methods=["POST"],
            view_func=self.app_handler.delete_app,
        )

        # 创建应用副本
        bp.add_url_rule(
            "/apps/<uuid:app_id>/copy",
            methods=["POST"],
            view_func=self.app_handler.copy_app,
        )

        bp.add_url_rule(
            "/apps/<uuid:app_id>/draft-app-config",
            view_func=self.app_handler.get_draft_app_config,
        )

        bp.add_url_rule(
            "/apps/<uuid:app_id>/draft-config",
            view_func=self.app_handler.update_draft_app_config,
            methods=["POST"],
        )

        bp.add_url_rule(
            "/apps/<uuid:app_id>/publish",
            view_func=self.app_handler.publish,
            methods=["POST"],
        )

        # 取消发布接口
        bp.add_url_rule(
            "/apps/<uuid:app_id>/cancel-publish",
            view_func=self.app_handler.cancel_publish,
            methods=["POST"],
        )

        # 获取应用的发布历史列表接口
        bp.add_url_rule(
            "/apps/<uuid:app_id>/publish-histories",
            view_func=self.app_handler.get_publish_histories_with_page,
            methods=["POST"],
        )

        # 回退指定的历史配置到草稿
        bp.add_url_rule(
            "/apps/<uuid:app_id>/fallback-history",
            view_func=self.app_handler.fallback_history_to_draft,
            methods=["POST"],
        )

        # 获取指定应用的调试会话长期记忆
        bp.add_url_rule(
            "/apps/<uuid:app_id>/summary",
            view_func=self.app_handler.get_debug_conversation_summary,
        )
        # 更新指定应用的调试会话长期记忆
        bp.add_url_rule(
            "/apps/<uuid:app_id>/summary",
            methods=["POST"],
            view_func=self.app_handler.update_debug_conversation_summary,
        )
        # 根据传递的应用id，删除指定的应用调试会话
        bp.add_url_rule(
            "/apps/<uuid:app_id>/conversations/delete-debug-conversation",
            methods=["POST"],
            view_func=self.app_handler.delete_debug_conversation,
        )

        # 应用调试对话
        bp.add_url_rule(
            "/apps/<uuid:app_id>/conversations",
            methods=["POST"],
            view_func=self.app_handler.debug_chat,
        )

        # 停止某次应用调试对话
        bp.add_url_rule(
            "/apps/<uuid:app_id>/conversations/tasks/<uuid:task_id>/stop",
            methods=["POST"],
            view_func=self.app_handler.stop_debug,
        )

        # 获取应用的调试会话消息列表
        bp.add_url_rule(
            "/apps/<uuid:app_id>/conversations/messages",
            methods=["GET"],
            view_func=self.app_handler.get_debug_conversation_messages_with_page,
        )

        # 知识库模块
        bp.add_url_rule(
            "/datasets",
            view_func=self.dataset_handler.get_datasets_with_page,
            methods=["GET"],
        )

        # 内置插件广场模块
        bp.add_url_rule(
            "/builtin-tools", view_func=self.builtin_tool_handler.get_builtin_tools
        )
        bp.add_url_rule(
            "/builtin-tools/<string:provider_name>/tools/<string:tool_name>",
            view_func=self.builtin_tool_handler.get_provider_tool,
        )
        bp.add_url_rule(
            "/builtin-tools/<string:provider_name>/icon",
            view_func=self.builtin_tool_handler.get_provider_icon,
        )
        bp.add_url_rule(
            "/builtin-tools/categories",
            view_func=self.builtin_tool_handler.get_categories,
        )

        # 自定义API插件模块
        bp.add_url_rule(
            "/api-tools/validate-openapi-schema",
            methods=["POST"],
            view_func=self.api_tool_handler.validate_openapi_schema,
        )

        bp.add_url_rule(
            "/api-tools",
            methods=["POST"],
            view_func=self.api_tool_handler.create_api_tool_provider,
        )

        bp.add_url_rule(
            "/api-tools",
            view_func=self.api_tool_handler.get_api_tool_providers_with_page,
        )

        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>",
            view_func=self.api_tool_handler.get_api_tool_provider,
        )

        # :/api-tools/:provider_id/tools/:tool_name
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>/tools/<string:tool_name>",
            view_func=self.api_tool_handler.get_api_tool,
        )

        # /api-tools/:api_tool_provider_id/delete
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>/delete",
            methods=["POST"],
            view_func=self.api_tool_handler.delete_api_tool_provider,
        )

        # :/api-tools/:provider_id
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>",
            methods=["POST"],
            view_func=self.api_tool_handler.update_api_tool_provider,
        )

        # 授权认证模块路由
        bp.add_url_rule(
            "/oauth/<string:provider_name>",
            view_func=self.oauth_handler.provider,
        )
        bp.add_url_rule(
            "/oauth/authorize/<string:provider_name>",
            methods=["POST"],
            view_func=self.oauth_handler.authorize,
        )

        # 账号设置模块相关路由
        bp.add_url_rule(
            "/account", view_func=self.account_handler.get_current_user
        )  # 获取用户信息
        bp.add_url_rule(
            "/account/password",
            methods=["POST"],
            view_func=self.account_handler.update_password,
        )  # 更新账号密码
        bp.add_url_rule(
            "/account/name",
            methods=["POST"],
            view_func=self.account_handler.update_name,
        )  # 更新账号名称
        bp.add_url_rule(
            "/account/avatar",
            methods=["POST"],
            view_func=self.account_handler.update_avatar,
        )  # 更新账号头像信息

        bp.add_url_rule(
            "/auth/password-login",
            methods=["POST"],
            view_func=self.auth_handler.password_login,
        )  # 账号密码登录

        bp.add_url_rule(
            "/auth/logout", methods=["POST"], view_func=self.auth_handler.logout
        )  # 退出登录

        # 上传文件模块
        bp.add_url_rule(
            "/upload-files/image",
            endpoint="upload_image",
            methods=["POST"],
            view_func=self.upload_file_handler.upload_image,
        )
        bp.add_url_rule(
            "/api/upload-files/image",
            endpoint="api_upload_image",
            methods=["POST"],
            view_func=self.upload_file_handler.upload_image,
        )
        bp.add_url_rule(
            "/uploaded-files/<path:filename>",
            view_func=self.get_uploaded_file,
            methods=["GET"],
        )

        # AI辅助模块

        # 利用AI优化预设Prompt
        bp.add_url_rule(
            "/ai/optimize-prompt",
            methods=["POST"],
            view_func=self.ai_handler.optimize_prompt,
        )

        # 根据传递的消息id获取建议问题列表
        bp.add_url_rule(
            "/ai/suggested-questions",
            methods=["POST"],
            view_func=self.ai_handler.generate_suggested_questions,
        )

        # API 密钥模块

        # 获取API密钥分页列表数据
        bp.add_url_rule(
            "/openapi/api-keys", view_func=self.api_key_handler.get_api_keys_with_page
        )

        # 新增、修改API密钥接口，修改状态
        bp.add_url_rule(
            "/openapi/api-keys",
            methods=["POST"],
            view_func=self.api_key_handler.create_api_key,
        )

        bp.add_url_rule(
            "/openapi/api-keys/<uuid:api_key_id>",
            methods=["POST"],
            view_func=self.api_key_handler.update_api_key,
        )

        bp.add_url_rule(
            "/openapi/api-keys/<uuid:api_key_id>/is-active",
            methods=["POST"],
            view_func=self.api_key_handler.update_api_key_is_active,
        )

        bp.add_url_rule(
            "/openapi/api-keys/<uuid:api_key_id>/delete",
            methods=["POST"],
            view_func=self.api_key_handler.delete_api_key,
        )

        openapi_bp.add_url_rule(
            "/openapi/chat", methods=["POST"], view_func=self.openapi_handler.chat
        )

        # 内置应用模块
        bp.add_url_rule(
            "/builtin-apps/categories",
            view_func=self.builtin_app_handler.get_builtin_app_categories,
        )
        bp.add_url_rule(
            "/builtin-apps", view_func=self.builtin_app_handler.get_builtin_apps
        )
        bp.add_url_rule(
            "/builtin-apps/add-builtin-app-to-space",
            methods=["POST"],
            view_func=self.builtin_app_handler.add_builtin_app_to_space,
        )

        # 工作流模块
        # 获取工作流分页列表数据
        bp.add_url_rule(
            "/workflows",
            view_func=self.workflow_handler.get_workflows_with_page,
        )
        # 新增工作流
        bp.add_url_rule(
            "/workflows",
            methods=["POST"],
            view_func=self.workflow_handler.create_workflow,
        )
        # 获取指定工作流详情
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>",
            view_func=self.workflow_handler.get_workflow,
        )
        # 更新指定工作流基础信息
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>",
            methods=["POST"],
            view_func=self.workflow_handler.update_workflow,
        )
        # 删除指定工作流
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/delete",
            methods=["POST"],
            view_func=self.workflow_handler.delete_workflow,
        )
        # 获取指定工作流的草稿图配置
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/draft",
            view_func=self.workflow_handler.get_draft_graph,
        )
        # 更新指定工作流的草稿图配置
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/draft",
            methods=["POST"],
            view_func=self.workflow_handler.update_draft_graph,
        )
        # 调试指定工作流
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/debug",
            methods=["POST"],
            view_func=self.workflow_handler.debug_workflow,
        )
        # 发布指定工作流
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/publish",
            methods=["POST"],
            view_func=self.workflow_handler.publish_workflow,
        )
        # 取消发布指定工作流
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/cancel-publish",
            methods=["POST"],
            view_func=self.workflow_handler.cancel_publish_workflow,
        )

        # 4.应用上去注册蓝图
        app.register_blueprint(bp)
        # 现在我们只需要传入一个APP的应用，我们就可以去访问对应的接口了
        app.register_blueprint(openapi_bp)

    def get_uploaded_file(self, filename: str):
        """读取本地上传文件"""

        return send_from_directory(CosService.get_local_upload_dir(), filename)
