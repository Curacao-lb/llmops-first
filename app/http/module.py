from flask_sqlalchemy import SQLAlchemy
from injector import Binder, Module
from internal.extension.database_extentsion import db


class ExtensionModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
