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

    def get_app(self, id: uuid.UUID) -> App:
        """根据ID获取应用信息"""
        return self.db.session.query(App).get(id)
        return app

    def update_app(self, id: uuid.UUID) -> App:
        """更新应用信息"""
        app = self.db.session.query(App).get(id)
        app.name = "robin的机器人"
        self.db.session.commit()
        return app

    def delete_app(self, id: uuid.UUID) -> bool:
        """删除应用信息"""
        app = self.db.session.query(App).get(id)
        if app is None:
            return False
        self.db.session.delete(app)
        self.db.session.commit()
        return True
