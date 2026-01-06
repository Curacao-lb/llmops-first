from flask import Flask,Blueprint
# 使用魔术变量（__all__），这里就可以导入 AppHandler
from internal.handler import AppHandler
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

        # 2.将URL与对应的控制器方法做绑定
        app_handler = AppHandler()

        # 3.将这个BP蓝图还有对应的路由，在控制器里的方法进行映射
        bp.add_url_rule('/ping', view_func=app_handler.ping,methods=['GET'])

        # 4.应用上去注册蓝图
        app.register_blueprint(bp)
        # 现在我们只需要传入一个APP的应用，我们就可以去访问对应的接口了


