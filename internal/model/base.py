from datetime import datetime
from typing import TYPE_CHECKING, Any

from internal.extension.database_extension import db


class BaseModel(db.Model):
    """
    模型基类,提供通用的序列化方法
    所有模型都应该继承这个类
    """

    # 声明为抽象类,不会创建表
    __abstract__ = True

    if TYPE_CHECKING:
        # 仅用于类型检查：声明声明式模型接受关键字参数构造。
        # 运行时该分支不会执行（TYPE_CHECKING 为 False），实际构造仍由 SQLAlchemy
        # 声明式构造器完成，因此不会影响 ORM 行为。这与 SQLAlchemy 2.0
        # DeclarativeBase 的做法一致。
        def __init__(self, **kw: Any) -> None: ...

    def to_dict(self):
        """
        将模型对象转换为字典,用于 JSON 序列化
        自动遍历所有字段,无需手动添加新字段
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # 处理特殊类型
            if value is None:
                result[column.name] = None
            elif isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif hasattr(value, "hex"):  # UUID 类型
                result[column.name] = str(value)
            else:
                result[column.name] = value
        return result
