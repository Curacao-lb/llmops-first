from pkg.response import HttpCode
import pytest


class TestBuiltinToolHandler:
    """内置工具控制器的测试类"""

    def test_get_builtin_tools(self, client):
        """测试获取所有内置工具列表"""
        resp = client.get("/builtin-tools")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS
        data = resp.json.get("data")
        assert isinstance(data, list)
        assert len(data) > 0
        # 验证每个提供商都包含必要字段
        for provider in data:
            assert "name" in provider
            assert "label" in provider
            assert "description" in provider
            assert "tools" in provider
            assert isinstance(provider["tools"], list)

    def test_get_provider_tool_success(self, client):
        """测试获取指定提供商的指定工具 - 成功"""
        resp = client.get("/builtin-tools/duckduckgo/tools/duckduckgo_search")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS
        data = resp.json.get("data")
        assert data["name"] == "duckduckgo_search"
        assert "provider" in data
        assert data["provider"]["name"] == "duckduckgo"
        assert "inputs" in data

    @pytest.mark.parametrize(
        "provider_name, tool_name",
        [
            ("not_exist_provider", "duckduckgo_search"),
            ("duckduckgo", "not_exist_tool"),
            ("not_exist_provider", "not_exist_tool"),
        ],
    )
    def test_get_provider_tool_not_found(self, provider_name, tool_name, client):
        """测试获取不存在的提供商或工具 - 404"""
        resp = client.get(f"/builtin-tools/{provider_name}/tools/{tool_name}")
        assert resp.status_code == 200
        assert resp.json.get("code") != HttpCode.SUCCESS

    def test_get_provider_icon_success(self, client):
        """测试获取提供商icon - 成功"""
        resp = client.get("/builtin-tools/duckduckgo/icon")
        assert resp.status_code == 200
        # icon接口返回的是文件流，content_type应该是图片类型
        assert any(
            mime in resp.content_type
            for mime in ["image/svg+xml", "image/png", "application/octet-stream"]
        )
        assert len(resp.data) > 0

    def test_get_provider_icon_not_found(self, client):
        """测试获取不存在的提供商icon - 404"""
        resp = client.get("/builtin-tools/not_exist_provider/icon")
        # 不存在的提供商应该返回错误
        assert resp.status_code != 200 or resp.json.get("code") != HttpCode.SUCCESS

    def test_get_categories(self, client):
        """测试获取所有分类列表"""
        resp = client.get("/builtin-tools/categories")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS
        data = resp.json.get("data")
        assert isinstance(data, list)
        assert len(data) > 0
        # 验证每个分类都包含必要字段
        for category in data:
            assert "category" in category
            assert "name" in category
            assert "icon" in category
            # icon应该是svg内容
            assert "<svg" in category["icon"] or "svg" in category["icon"]

    def test_get_categories_contains_expected(self, client):
        """测试分类列表包含预期的分类"""
        resp = client.get("/builtin-tools/categories")
        data = resp.json.get("data")
        category_keys = [item["category"] for item in data]
        # 验证包含yaml中定义的分类
        assert "search" in category_keys
        assert "image" in category_keys
        assert "weather" in category_keys
        assert "tool" in category_keys
        assert "other" in category_keys
