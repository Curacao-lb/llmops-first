from pkg.sqlalchemy import SQLAlchemy
from injector import inject
from dataclasses import dataclass
from internal.model import App
from internal.schema.app_schema import GetAppsWithPageReq
from pkg.paginator import Paginator
from sqlalchemy import desc
from typing import Any
import uuid


@inject
@dataclass
class AppService:
    """应用服务逻辑"""

    db: SQLAlchemy

    def get_apps_with_page(
        self, req: GetAppsWithPageReq
    ) -> tuple[list[Any], Paginator]:
        """获取应用分页列表数据"""
        # 临时写一个account_id,后续接入登录态后替换
        account_id = "46db30d1-3199-4e79-a0cd-abf12fa6858f"
        paginator = Paginator(db=self.db, req=req)
        filters = [App.account_id == account_id]
        if req.search_word.data:
            filters.append(App.name.ilike(f"%{req.search_word.data}%"))
        if req.status.data:
            filters.append(App.status == req.status.data)
        apps = paginator.paginate(
            self.db.session.query(App).filter(*filters).order_by(desc("created_at"))
        )
        return apps, paginator

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
