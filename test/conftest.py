import pytest
from sqlalchemy.orm import Session as SASession, scoped_session, sessionmaker

from app.http.app import app
from internal.extension.database_extension import db


@pytest.fixture
def client():
    """
    创建 Flask 测试客户端的 fixture

    fixture 是 pytest 的核心概念,可以理解为"测试前的准备工作"
    任何测试函数只要在参数中声明 client,pytest 就会自动调用这个函数并注入返回值

    使用示例:
        def test_ping(client):  # pytest 自动注入 client
            response = client.get('/ping')
            assert response.status_code == 200
    """
    # 将 Flask 应用设置为测试模式
    # 测试模式下: 异常会直接抛出,不会被捕获,提供更详细的错误信息
    app.config["TESTING"] = True

    # app.test_client() 创建一个 Flask 测试客户端,用于模拟 HTTP 请求
    # with 语句确保资源正确管理(自动清理)
    # yield 将测试客户端返回给测试函数
    # yield 而不是 return 的好处: 测试运行前执行 yield 之前的代码(setup),测试运行后执行 yield 之后的代码(teardown)
    with app.test_client() as client:
        yield client


@pytest.fixture
def db_session():
    """
    数据库事务回滚 fixture，实现测试数据与真实数据库的隔离。

    原理（基于 SQLAlchemy 官方 "Joining a Session into an External Transaction" 方案）:
        1. 从引擎拿一条独立连接 connection，并在其上手动开启一个外层事务 transaction。
        2. 把 db.session 临时替换成一个绑定到这条连接的 Session。
        3. join_transaction_mode="create_savepoint": Session 内部每次 commit
           只提交到 SAVEPOINT，不会真正提交外层事务，所以业务代码里的
           db.session.commit() / auto_commit() 都能照常工作。
        4. 测试结束后 transaction.rollback() 把外层事务整体回滚，
           本次测试期间的所有增删改查全部撤销，真实数据不受影响。

    为什么不用 db.session.configure(bind=connection):
        flask_sqlalchemy 3.x 自定义了 Session.get_bind，会忽略 session 级别的 bind，
        始终路由到默认引擎，导致写操作直接落到真实库。因此这里改用标准
        SQLAlchemy 的 Session 工厂并绑定到外部连接，绕开该路由逻辑。

    使用示例:
        def test_create(db_session):
            db_session.add(SomeModel(...))
            db_session.commit()          # 仅提交到 savepoint
            assert db_session.query(SomeModel).count() == 1
        # 测试结束自动回滚，数据库恢复原状
    """
    with app.app_context():
        # 1.获取默认引擎并建立一条独立连接，在连接上开启外层事务
        engine = db.engines[None]
        connection = engine.connect()
        transaction = connection.begin()

        # 2.保存原始 session，替换为绑定到外部连接的临时 session
        original_session = db.session
        factory = sessionmaker(
            bind=connection,
            class_=SASession,
            join_transaction_mode="create_savepoint",
        )
        db.session = scoped_session(factory)

        try:
            # 3.把临时 session 提供给测试使用
            yield db.session
        finally:
            # 4.清理临时 session 并整体回滚外层事务，恢复原始 session
            db.session.remove()
            db.session = original_session
            transaction.rollback()
            connection.close()
