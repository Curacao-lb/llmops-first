from pkg.sqlalchemy import SQLAlchemy
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
        # 使用 auto_commit 自动提交,无需手动 commit
        with self.db.auto_commit():
            app = App()
            app.id = uuid.uuid4()
            app.account_id = uuid.uuid4()
            app.name = "测试机器人"
            app.icon = ""
            app.description = "这是一个简单的聊天机器人"
            self.db.session.add(app)
        return app

    def get_app(self, id: uuid.UUID) -> App:
        """根据ID获取应用信息"""
        return self.db.session.query(App).get(id)

    def update_app(self, id: uuid.UUID) -> App:
        """更新应用信息"""
        with self.db.auto_commit():
            app = self.db.session.query(App).get(id)
            app.name = "robin的机器人"
        return app

    def delete_app(self, id: uuid.UUID) -> bool:
        """删除应用信息"""
        app = self.db.session.query(App).get(id)
        if app is None:
            return False
        with self.db.auto_commit():
            self.db.session.delete(app)
        return True
