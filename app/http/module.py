from pkg.sqlalchemy import SQLAlchemy
from injector import Binder, Module
from internal.extension.database_extentsion import db
from internal.extension.migrate_extension import migrate
from flask_migrate import Migrate


class ExtensionModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
