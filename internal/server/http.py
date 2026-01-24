from flask import Flask
from internal.router import Router
from internal.exception import CustomException
from pkg.response import json, Response, HttpCode
from flask_sqlalchemy import SQLAlchemy
import os


class Http(Flask):
    """
    http 服务引擎
    Http 类继承了 Flask 并且要注册钩子,必须手动写 __init__。
    """

    # *args 是非命名的参数,比如传入 1 'name' false 这种等等
    # **kwargs 是命名的参数,比如传入 name='name' age=18 这种等等
    def __init__(self, *args, conf: "Config", db: SQLAlchemy, router: Router, **kwargs):
        # 使用super去调用父类的构造函数,将整个参数进行实例化。
        # 要不然的话继承别人,如果你不去实现它的构造函数是很容易出错的。
        super(Http, self).__init__(*args, **kwargs)
        # 通过对象的方式去将我们这个类加载到这个flask应用中
        self.config.from_object(conf)

        # 初始化flask扩展
        db.init_app(self)

        # 注册全局异常处理器
        self.register_error_handler(Exception, self._register_error_handlers)

        # 注册应用路由
        router.register_router(self)

    def _register_error_handlers(self, error: Exception):
        """注册全局异常处理器"""

        # 1.先来判断一下异常信息是不是我们的自定义异常，如果是的话，可以提取massage和code等信息
        if isinstance(error, CustomException):
            return json(
                Response(message=error.message, code=error.code, data=error.data)
            )

        # 如果不是我们的自定义异常，则有可能是程序、数据库抛出的异常，也可以提取信息，设置为FAIL状态码
        if self.debug or os.getenv("FLASK_ENV") == "development":
            return error

        # 2.如果不是我们的自定义异常，则有可能是程序或者是数据库抛出的异常，也可以提取信息，然后设置为fail状态码。
        return json(Response(message=str(error), code=HttpCode.FAIL, data={}))
