"""演示并验证 db_session 事务回滚隔离 fixture 的行为。"""

import uuid

import pytest
from sqlalchemy.orm import Session as SASession

from internal.extension.database_extension import db
from internal.model import ApiToolProvider

ACCOUNT_ID = "46db30d1-3199-4e79-a0cd-abf12fa6858f"


def _make_name():
    return f"_rollback_demo_{uuid.uuid4().hex[:8]}"


class TestDbRollbackIsolation:
    """验证 db_session fixture 在测试结束后会回滚所有写操作"""

    # 用类变量在两个测试之间传递上一次创建的名字
    leaked_name = None

    def test_create_is_visible_within_transaction(self, db_session):
        """事务内：新增并 commit 的数据应当能查询到"""
        name = _make_name()
        TestDbRollbackIsolation.leaked_name = name

        provider = ApiToolProvider(
            account_id=ACCOUNT_ID,
            name=name,
            icon="https://example.com/icon.png",
            description="rollback demo",
            openapi_schema="{}",
            headers=[],
        )
        db_session.add(provider)
        db_session.commit()  # 仅提交到 savepoint

        found = db_session.query(ApiToolProvider).filter_by(name=name).one_or_none()
        assert found is not None

    def test_previous_data_was_rolled_back(self, db_session):
        """下一个测试：上一个测试创建的数据不应残留在真实库中"""
        name = TestDbRollbackIsolation.leaked_name
        assert name is not None  # 确保上一个测试确实跑过

        leaked = db_session.query(ApiToolProvider).filter_by(name=name).one_or_none()
        assert leaked is None, "上一个测试的数据应已被回滚，不应残留"


def test_no_leak_to_real_db_after_fixture():
    """fixture 之外用真实 session 再确认一次：上面用例的数据没有落库"""
    name = TestDbRollbackIsolation.leaked_name
    if name is None:
        return
    from app.http.app import app

    with app.app_context():
        leaked = db.session.query(ApiToolProvider).filter_by(name=name).one_or_none()
        db.session.remove()
        assert leaked is None, "回滚后真实数据库不应残留测试数据"


def _real_session():
    """创建一条直接绑定到引擎的标准 Session，绕开被 db_session 替换的 db.session。

    这样无论 db.session 是否处于回滚隔离状态，这个 session 的提交都会真正落到
    数据库，用于制造/清理"种子数据"以及做独立的真实库校验。
    """
    engine = db.engines[None]
    return SASession(bind=engine)


class TestDbRollbackDelete:
    """验证 delete 操作不会污染真实数据库（会随事务回滚而撤销）"""

    @pytest.fixture
    def seeded_provider(self):
        """用独立的真实 session 往库里写入一条已提交的"种子"数据。

        关键点：这里不能用 db.session，因为 db_session fixture 已经把它替换成了
        绑定到回滚事务的隔离 session，commit 只会进 savepoint 最终被回滚。
        改用 _real_session() 直接提交到真实库，才能真正制造一条待删除的数据。
        """
        from app.http.app import app

        name = f"_rollback_delete_{uuid.uuid4().hex[:8]}"
        with app.app_context():
            session = _real_session()
            provider = ApiToolProvider(
                account_id=ACCOUNT_ID,
                name=name,
                icon="https://example.com/icon.png",
                description="delete rollback seed",
                openapi_schema="{}",
                headers=[],
            )
            session.add(provider)
            session.commit()  # 真正提交到数据库
            provider_id = provider.id
            session.close()

        yield {"id": provider_id, "name": name}

        # 收尾：用独立真实 session 把种子数据彻底删除，避免污染数据库
        with app.app_context():
            session = _real_session()
            obj = session.get(ApiToolProvider, provider_id)
            if obj is not None:
                session.delete(obj)
                session.commit()
            session.close()

    def test_delete_is_isolated_and_rolled_back(self, db_session, seeded_provider):
        """在隔离 session 中删除并 commit 后，真实库里这条数据依然存在"""
        name = seeded_provider["name"]

        # 1.隔离事务内能查到种子数据
        target = db_session.query(ApiToolProvider).filter_by(name=name).one_or_none()
        assert target is not None, "种子数据应当存在"

        # 2.在隔离 session 中删除并提交（仅提交到 savepoint）
        db_session.delete(target)
        db_session.commit()

        # 3.隔离事务内确认已删除
        after_delete = (
            db_session.query(ApiToolProvider).filter_by(name=name).one_or_none()
        )
        assert after_delete is None, "隔离事务内删除后应当查不到"

        # 4.用一条独立的真实连接查询：删除没有提交到真实库，数据仍然存在
        #   这说明 delete 被限制在隔离事务里，测试结束 rollback 后会被撤销
        verify = _real_session()
        still_there = verify.query(ApiToolProvider).filter_by(name=name).one_or_none()
        verify.close()
        assert still_there is not None, "delete 未提交到真实库，数据应仍然存在"
