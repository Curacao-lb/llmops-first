from pkg.sqlalchemy import SQLAlchemy
from injector import inject
from dataclasses import dataclass
from internal.exception import NotFoundException, UnauthorizedException
from internal.model import Account, App, AppConfigVersion
from internal.schema.app_schema import GetAppsWithPageReq
from pkg.paginator import Paginator
from sqlalchemy import desc
from typing import Any
from uuid import UUID
from internal.schema.app_schema import CreateAppReq
import uuid
from internal.entity.app_entity import AppStatus, AppConfigType, DEFAULT_APP_CONFIG
from .base_service import BaseService


@inject
@dataclass
class AppService(BaseService):
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

    def create_app(self, req: CreateAppReq, account: Account) -> App:
        # 1. 开启数据库自动提交上下文
        with self.db.auto_commit():
            # 2.创建应用记录，并刷新数据，从而可以拿到应用id
            app = App(
                id=uuid.uuid4(),
                account_id=account.id,
                name=req.name.data,
                en_name=req.en_name.data,
                icon=req.icon.data,
                description=req.description.data,
                status=AppStatus.DRAFT,
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 3.添加草稿记录
            app_config_version = AppConfigVersion(
                id=uuid.uuid4(),
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG,
            )
            self.db.session.add(app_config_version)
            self.db.session.flush()

            # 4.为应用添加草稿配置id
            app.draft_app_config_id = app_config_version.id

        # 5.返回创建的应用记录
        return app

    def get_app(self, app_id: uuid.UUID, account: Account) -> App:
        """根据传递的id获取应用的基础信息"""
        # 1.查询数据库获取应用基础信息
        app = self.get(App, app_id)
        # 2.判断应用是否存在
        if not app:
            raise NotFoundException("应用不存在")
        # 3.判断当前账号是否有权限访问该应用
        if app.account_id != account.id:
            raise UnauthorizedException("当前账号无权限")
        return app

    def get_draft_app_config(self, app: App) -> AppConfigVersion:
        """获取指定应用的草稿配置，不存在时创建一份默认草稿配置。

        与只读属性 App.draft_app_config 不同，这里承担「取不到就创建」的业务行为，
        所有写入都收敛在一个受控事务里，并同步回写 app.draft_app_config_id，
        避免草稿配置存在两个不一致的真相源。
        """
        # 1.先通过只读属性尝试获取已有草稿配置
        draft_app_config = app.draft_app_config
        if draft_app_config is not None:
            return draft_app_config

        # 2.不存在则在单个事务里创建默认草稿配置并回写关联id
        with self.db.auto_commit():
            draft_app_config = AppConfigVersion(
                id=uuid.uuid4(),
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG,
            )
            self.db.session.add(draft_app_config)
            self.db.session.flush()
            app.draft_app_config_id = draft_app_config.id

        return draft_app_config

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
