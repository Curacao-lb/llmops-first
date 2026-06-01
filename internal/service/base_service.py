from dataclasses import dataclass
from typing import Any, Optional

from injector import inject

from internal.exception import FailException
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class BaseService:
    """基础服务，封装数据库的增删改查通用操作"""

    db: SQLAlchemy

    def create(self, model: Any, **kwargs) -> Any:
        """根据传递的模型类与关键字参数创建一条记录"""
        with self.db.auto_commit():
            model_instance = model(**kwargs)
            self.db.session.add(model_instance)
        return model_instance

    def delete(self, model_instance: Any) -> Any:
        """删除传递的模型实例"""
        with self.db.auto_commit():
            self.db.session.delete(model_instance)
        return model_instance

    def update(self, model_instance: Any, **kwargs) -> Any:
        """根据传递的关键字参数更新模型实例的字段"""
        with self.db.auto_commit():
            for field, value in kwargs.items():
                if hasattr(model_instance, field):
                    setattr(model_instance, field, value)
                else:
                    raise FailException("更新数据失败")
        return model_instance

    def get(self, model: Any, primary_key: Any) -> Optional[Any]:
        """根据主键获取一条记录"""
        return self.db.session.query(model).get(primary_key)
