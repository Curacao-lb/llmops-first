from pkg.response import HttpCode
import pytest


class TestAppHandler:
    """app控制器的测试类"""

    @pytest.mark.parametrize("query", [None, "你好，你是谁？"])
    def test_completion(self, query, client):
        resp = client.post("/app/completion", json={"query": query})
        if query is None:
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.status_code == 200
            assert resp.json.get("code") == HttpCode.SUCCESS
