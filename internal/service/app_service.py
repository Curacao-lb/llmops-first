from flask_sqlalchemy import SQLAlchemy
from injector import inject
from dataclasses import dataclass
from internal.model import App
import uuid


@inject
@dataclass
class AppService:
    """应用服务逻辑"""

    db: SQLAlchemy

    def create_app(self) -> App:
        """创建新的应用记录"""
        # 1.创建模型的实体类
        app = App()
        app.id = uuid.uuid4()
        app.account_id = uuid.uuid4()
        app.name = "测试机器人"
        app.icon = ""
        app.description = "这是一个简单的聊天机器人"

        # 2.将实体类添加到Session会话中
        self.db.session.add(app)

        # 3.提交Session会话
        self.db.session.commit()

        return app
