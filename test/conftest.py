import pytest

from app.http.app import app


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
