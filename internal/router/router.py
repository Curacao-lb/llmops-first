from flask import Flask, Blueprint

# 使用魔术变量（__all__），这里就可以导入 AppHandler
from internal.handler import AppHandler, BuiltinToolHandler, ApiToolHandler
from dataclasses import dataclass

"""
下面注释的代码
由dataclass替代
dataclass 可以自动生成 __init__，减少样板代码：
"""
from injector import inject


@inject
@dataclass
class Router:
    """路由"""

    app_handler: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler

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

        # 2.使用依赖注入的 app_handler,不需要手动创建
        # self.app_handler 已经通过 @inject 和 @dataclass 自动注入了

        # 3.将这个BP蓝图还有对应的路由，在控制器里的方法进行映射
        bp.add_url_rule("/ping", view_func=self.app_handler.ping, methods=["GET"])
        bp.add_url_rule(
            "/apps/<uuid:app_id>/debug",
            view_func=self.app_handler.debug,
            methods=["POST"],
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/memory_debug",
            view_func=self.app_handler.memory_debug,
            methods=["POST"],
        )
        # bp.add_url_rule("/app", methods=["POST"], view_func=self.app_handler.create_app)
        # bp.add_url_rule("/app/<uuid:id>", view_func=self.app_handler.get_app)
        # bp.add_url_rule(
        #     "/app/<uuid:id>", view_func=self.app_handler.update_app, methods=["POST"]
        # )
        # bp.add_url_rule(
        #     "/app/<uuid:id>/delete",
        #     view_func=self.app_handler.delete_app,
        #     methods=["POST"],
        # )

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
            view_func=self.api_tool_handler.create_api_tool,
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

        # 4.应用上去注册蓝图
        app.register_blueprint(bp)
        # 现在我们只需要传入一个APP的应用，我们就可以去访问对应的接口了
