from internal.server import Http
from injector import Injector, Module, Binder
from internal.router import Router
from flask_sqlalchemy import SQLAlchemy
from .module import ExtensionModule

# 将.env加载到环境变量中
import dotenv

dotenv.load_dotenv()

from config import Config

conf = Config()


# 1. 创建 injector（依赖注入容器）
injector = Injector([ExtensionModule])


# router 从依赖注入的实体类型中去获取

# 2. 用 injector 获取 Router 实例
# injector 会：
#   - 看到 Router 需要 AppHandler
#   - 自动创建 AppHandler 实例
#   - 把 AppHandler 注入到 Router
#   - 返回完整的 Router 实例
# 3. 把 Router 传给 Http
app = Http(
    __name__, conf=conf, db=injector.get(SQLAlchemy), router=injector.get(Router)
)

if __name__ == "__main__":
    app.run(debug=True)
