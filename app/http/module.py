from pkg.sqlalchemy import SQLAlchemy
from injector import Binder, Module
from internal.extension.database_extension import db
from internal.extension.migrate_extension import migrate
from flask_migrate import Migrate
from flask_login import LoginManager
from internal.extension.login_extension import login_manager


class ExtensionModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
        binder.bind(LoginManager, to=login_manager)
