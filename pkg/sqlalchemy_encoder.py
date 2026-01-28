from flask.json.provider import DefaultJSONProvider
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase


class SQLAlchemyJSONProvider(DefaultJSONProvider):
    """
    自定义 JSON 编码器,让 Flask 自动序列化 SQLAlchemy 模型
    """

    def default(self, obj):
        # 处理 SQLAlchemy 模型
        if hasattr(obj, "__table__"):
            result = {}
            for column in obj.__table__.columns:
                value = getattr(obj, column.name)
                if value is None:
                    result[column.name] = None
                elif isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                elif hasattr(value, "hex"):  # UUID
                    result[column.name] = str(value)
                else:
                    result[column.name] = value
            return result

        return super().default(obj)
