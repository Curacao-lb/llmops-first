from contextlib import contextmanager
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy


class SQLAlchemy(_SQLAlchemy):
    """
    重写 SQLAlchemy 核心类,实现数据库自动提交

    使用方式:
        with db.auto_commit():
            app = App()
            app.name = "测试"
            db.session.add(app)
        # 自动提交,无需手动调用 commit()
        # 如果发生异常,自动回滚
    """

    @contextmanager
    def auto_commit(self):
        """
        自动提交的上下文管理器

        - 正常执行: yield 后自动 commit
        - 发生异常: 自动 rollback 并抛出异常
        """
        try:
            yield
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
