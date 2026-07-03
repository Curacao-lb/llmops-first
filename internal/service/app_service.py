from pkg.sqlalchemy import SQLAlchemy
from injector import inject
from dataclasses import dataclass
from internal.exception import NotFoundException
from internal.model import Account, App
from internal.schema.app_schema import GetAppsWithPageReq
from pkg.paginator import Paginator
from sqlalchemy import desc
from typing import Any
from uuid import UUID


@inject
@dataclass
class AppService:
    """应用服务逻辑"""

    db: SQLAlchemy

    def get_apps_with_page(
        self, req: GetAppsWithPageReq, account: Account
    ) -> tuple[list[Any], Paginator]:
        """获取应用分页列表数据"""
        paginator = Paginator(db=self.db, req=req)
        filters = [App.account_id == account.id]
        if req.search_word.data:
            filters.append(App.name.ilike(f"%{req.search_word.data}%"))
        if req.status.data:
            filters.append(App.status == req.status.data)
        apps = paginator.paginate(
            self.db.session.query(App).filter(*filters).order_by(desc("created_at"))
        )
        return apps, paginator

    def create_app(self, account: Account) -> App:
        """创建新的应用记录"""
        # 使用 auto_commit 自动提交,无需手动 commit
        with self.db.auto_commit():
            app = App()
            app.account_id = account.id
            app.name = "测试机器人"
            app.icon = ""
            app.description = "这是一个简单的聊天机器人"
            self.db.session.add(app)
        return app

    def get_app(self, app_id: UUID, account: Account) -> App:
        """根据ID获取应用信息"""
        app = (
            self.db.session.query(App)
            .filter(App.id == app_id, App.account_id == account.id)
            .one_or_none()
        )
        if app is None:
            raise NotFoundException("应用不存在")
        return app

    def update_app(self, app_id: UUID, account: Account) -> App:
        """更新应用信息"""
        app = self.get_app(app_id, account)
        with self.db.auto_commit():
            app.name = "robin的机器人"
        return app

    def delete_app(self, app_id: UUID, account: Account) -> bool:
        """删除应用信息"""
        app = (
            self.db.session.query(App)
            .filter(App.id == app_id, App.account_id == account.id)
            .one_or_none()
        )
        if app is None:
            return False
        with self.db.auto_commit():
            self.db.session.delete(app)
        return True
