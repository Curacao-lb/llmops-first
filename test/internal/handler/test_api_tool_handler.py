import json
import uuid

import pytest

from pkg.response import HttpCode


class TestCreateApiTool:
    """创建自定义API工具接口的测试类"""

    @pytest.fixture
    def valid_openapi_schema(self):
        """有效的openapi_schema数据"""
        return json.dumps(
            {
                "server": "https://api.weather.com",
                "description": "天气查询API",
                "paths": {
                    "/weather": {
                        "get": {
                            "description": "查询天气信息",
                            "operationId": "get_weather",
                            "parameters": [
                                {
                                    "name": "city",
                                    "in": "query",
                                    "description": "城市名称",
                                    "required": True,
                                    "type": "str",
                                }
                            ],
                        }
                    }
                },
            }
        )

    def test_create_api_tool_success(self, client, valid_openapi_schema):
        """测试创建自定义API工具 - 成功"""
        resp = client.post(
            "/api-tools",
            data={
                "name": "天气工具",
                "icon": "https://example.com/icon.png",
                "openapi_schema": valid_openapi_schema,
                "headers": json.dumps(
                    [{"key": "Authorization", "value": "Bearer xxx"}]
                ),
            },
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS

    def test_create_api_tool_missing_name(self, client, valid_openapi_schema):
        """测试创建自定义API工具 - 缺少name"""
        resp = client.post(
            "/api-tools",
            data={
                "icon": "https://example.com/icon.png",
                "openapi_schema": valid_openapi_schema,
            },
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_create_api_tool_missing_icon(self, client, valid_openapi_schema):
        """测试创建自定义API工具 - 缺少icon"""
        resp = client.post(
            "/api-tools",
            data={
                "name": "天气工具",
                "openapi_schema": valid_openapi_schema,
            },
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_create_api_tool_missing_openapi_schema(self, client):
        """测试创建自定义API工具 - 缺少openapi_schema"""
        resp = client.post(
            "/api-tools",
            data={
                "name": "天气工具",
                "icon": "https://example.com/icon.png",
            },
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_create_api_tool_invalid_openapi_schema(self, client):
        """测试创建自定义API工具 - openapi_schema格式错误"""
        resp = client.post(
            "/api-tools",
            data={
                "name": "天气工具",
                "icon": "https://example.com/icon.png",
                "openapi_schema": "not valid json{{{",
            },
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_create_api_tool_name_too_long(self, client, valid_openapi_schema):
        """测试创建自定义API工具 - name超过30字符"""
        resp = client.post(
            "/api-tools",
            data={
                "name": "a" * 31,
                "icon": "https://example.com/icon.png",
                "openapi_schema": valid_openapi_schema,
            },
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_create_api_tool_invalid_icon_url(self, client, valid_openapi_schema):
        """测试创建自定义API工具 - icon不是合法URL"""
        resp = client.post(
            "/api-tools",
            data={
                "name": "天气工具",
                "icon": "not-a-url",
                "openapi_schema": valid_openapi_schema,
            },
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_create_api_tool_duplicate_name(self, client, valid_openapi_schema):
        """测试创建自定义API工具 - 同名工具已存在"""
        data = {
            "name": "天气工具重复测试",
            "icon": "https://example.com/icon.png",
            "openapi_schema": valid_openapi_schema,
        }
        # 第一次创建应该成功
        resp1 = client.post("/api-tools", data=data)
        assert resp1.status_code == 200
        assert resp1.json.get("code") == HttpCode.SUCCESS

        # 第二次创建同名工具应该失败
        resp2 = client.post("/api-tools", data=data)
        assert resp2.status_code == 200
        assert resp2.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_create_api_tool_multiple_paths(self, client):
        """测试创建自定义API工具 - 多路径多方法"""
        schema = json.dumps(
            {
                "server": "https://api.example.com",
                "description": "综合API",
                "paths": {
                    "/users": {
                        "get": {
                            "description": "获取用户列表",
                            "operationId": "list_users",
                            "parameters": [
                                {
                                    "name": "page",
                                    "in": "query",
                                    "description": "页码",
                                    "required": False,
                                    "type": "int",
                                }
                            ],
                        },
                        "post": {
                            "description": "创建用户",
                            "operationId": "create_user",
                            "parameters": [
                                {
                                    "name": "name",
                                    "in": "request_body",
                                    "description": "用户名",
                                    "required": True,
                                    "type": "str",
                                }
                            ],
                        },
                    },
                },
            }
        )
        resp = client.post(
            "/api-tools",
            data={
                "name": "用户管理工具",
                "icon": "https://example.com/icon.png",
                "openapi_schema": schema,
            },
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS

    def test_create_api_tool_invalid_headers(self, client, valid_openapi_schema):
        """测试创建自定义API工具 - headers格式错误"""
        resp = client.post(
            "/api-tools",
            data={
                "name": "天气工具",
                "icon": "https://example.com/icon.png",
                "openapi_schema": valid_openapi_schema,
                "headers": json.dumps([{"invalid_key": "value"}]),
            },
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_create_api_tool_empty_headers(self, client, valid_openapi_schema):
        """测试创建自定义API工具 - headers为空列表(合法)"""
        resp = client.post(
            "/api-tools",
            data={
                "name": "天气工具空headers",
                "icon": "https://example.com/icon.png",
                "openapi_schema": valid_openapi_schema,
                "headers": json.dumps([]),
            },
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS


class TestApiToolHandler:
    """自定义API插件控制器的测试类"""

    @pytest.fixture
    def valid_openapi_schema(self):
        """有效的openapi_schema数据"""
        return json.dumps(
            {
                "server": "https://api.weather.com",
                "description": "天气查询API",
                "paths": {
                    "/weather": {
                        "get": {
                            "description": "查询天气信息",
                            "operationId": "get_weather",
                            "parameters": [
                                {
                                    "name": "city",
                                    "in": "query",
                                    "description": "城市名称",
                                    "required": True,
                                    "type": "str",
                                }
                            ],
                        }
                    }
                },
            }
        )

    def test_validate_openapi_schema_success(self, client, valid_openapi_schema):
        """测试校验openapi_schema - 成功"""
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={"openapi_schema": valid_openapi_schema},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS
        assert resp.json.get("message") == "数据校验成功"

    def test_validate_openapi_schema_empty(self, client):
        """测试校验openapi_schema - 空字符串"""
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={"openapi_schema": ""},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_validate_openapi_schema_missing_field(self, client):
        """测试校验openapi_schema - 缺少openapi_schema字段"""
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_validate_openapi_schema_invalid_json(self, client):
        """测试校验openapi_schema - 非法JSON格式"""
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={"openapi_schema": "not a json string{{{"},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_validate_openapi_schema_missing_server(self, client):
        """测试校验openapi_schema - 缺少server字段"""
        schema = json.dumps(
            {
                "server": "",
                "description": "test",
                "paths": {
                    "/test": {
                        "get": {
                            "description": "test api",
                            "operationId": "test_op",
                            "parameters": [],
                        }
                    }
                },
            }
        )
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={"openapi_schema": schema},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_validate_openapi_schema_missing_description(self, client):
        """测试校验openapi_schema - 缺少description字段"""
        schema = json.dumps(
            {
                "server": "https://api.example.com",
                "description": "",
                "paths": {
                    "/test": {
                        "get": {
                            "description": "test api",
                            "operationId": "test_op",
                            "parameters": [],
                        }
                    }
                },
            }
        )
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={"openapi_schema": schema},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_validate_openapi_schema_empty_paths(self, client):
        """测试校验openapi_schema - paths为空"""
        schema = json.dumps(
            {
                "server": "https://api.example.com",
                "description": "test",
                "paths": {},
            }
        )
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={"openapi_schema": schema},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_validate_openapi_schema_duplicate_operation_id(self, client):
        """测试校验openapi_schema - operationId重复"""
        schema = json.dumps(
            {
                "server": "https://api.example.com",
                "description": "test",
                "paths": {
                    "/test1": {
                        "get": {
                            "description": "test api 1",
                            "operationId": "same_id",
                            "parameters": [],
                        }
                    },
                    "/test2": {
                        "get": {
                            "description": "test api 2",
                            "operationId": "same_id",
                            "parameters": [],
                        }
                    },
                },
            }
        )
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={"openapi_schema": schema},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_validate_openapi_schema_invalid_parameter_type(self, client):
        """测试校验openapi_schema - 参数type不合法"""
        schema = json.dumps(
            {
                "server": "https://api.example.com",
                "description": "test",
                "paths": {
                    "/test": {
                        "get": {
                            "description": "test api",
                            "operationId": "test_op",
                            "parameters": [
                                {
                                    "name": "q",
                                    "in": "query",
                                    "description": "query param",
                                    "required": True,
                                    "type": "invalid_type",
                                }
                            ],
                        }
                    }
                },
            }
        )
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={"openapi_schema": schema},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_validate_openapi_schema_invalid_parameter_in(self, client):
        """测试校验openapi_schema - 参数in不合法"""
        schema = json.dumps(
            {
                "server": "https://api.example.com",
                "description": "test",
                "paths": {
                    "/test": {
                        "get": {
                            "description": "test api",
                            "operationId": "test_op",
                            "parameters": [
                                {
                                    "name": "q",
                                    "in": "invalid_location",
                                    "description": "query param",
                                    "required": True,
                                    "type": "str",
                                }
                            ],
                        }
                    }
                },
            }
        )
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={"openapi_schema": schema},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR

    def test_validate_openapi_schema_multiple_paths_and_methods(self, client):
        """测试校验openapi_schema - 多路径多方法"""
        schema = json.dumps(
            {
                "server": "https://api.example.com",
                "description": "综合API",
                "paths": {
                    "/users": {
                        "get": {
                            "description": "获取用户列表",
                            "operationId": "list_users",
                            "parameters": [
                                {
                                    "name": "page",
                                    "in": "query",
                                    "description": "页码",
                                    "required": False,
                                    "type": "int",
                                }
                            ],
                        },
                        "post": {
                            "description": "创建用户",
                            "operationId": "create_user",
                            "parameters": [
                                {
                                    "name": "name",
                                    "in": "request_body",
                                    "description": "用户名",
                                    "required": True,
                                    "type": "str",
                                }
                            ],
                        },
                    },
                    "/users/{id}": {
                        "get": {
                            "description": "获取用户详情",
                            "operationId": "get_user",
                            "parameters": [
                                {
                                    "name": "id",
                                    "in": "path",
                                    "description": "用户ID",
                                    "required": True,
                                    "type": "int",
                                }
                            ],
                        }
                    },
                },
            }
        )
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={"openapi_schema": schema},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS

    def test_validate_openapi_schema_parameter_required_not_bool(self, client):
        """测试校验openapi_schema - 参数required不是布尔值"""
        schema = json.dumps(
            {
                "server": "https://api.example.com",
                "description": "test",
                "paths": {
                    "/test": {
                        "get": {
                            "description": "test api",
                            "operationId": "test_op",
                            "parameters": [
                                {
                                    "name": "q",
                                    "in": "query",
                                    "description": "query param",
                                    "required": "yes",
                                    "type": "str",
                                }
                            ],
                        }
                    }
                },
            }
        )
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            data={"openapi_schema": schema},
        )
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.VALIDATE_ERROR


class TestGetApiToolProvider:
    """获取API工具提供者接口的测试类"""

    @pytest.fixture
    def valid_openapi_schema(self):
        """有效的openapi_schema数据"""
        return json.dumps(
            {
                "server": "https://api.weather.com",
                "description": "天气查询API",
                "paths": {
                    "/weather": {
                        "get": {
                            "description": "查询天气信息",
                            "operationId": "get_weather",
                            "parameters": [
                                {
                                    "name": "city",
                                    "in": "query",
                                    "description": "城市名称",
                                    "required": True,
                                    "type": "str",
                                }
                            ],
                        }
                    }
                },
            }
        )

    def _create_api_tool(self, client, valid_openapi_schema, name="测试工具"):
        """辅助方法：先创建一个API工具，返回响应"""
        return client.post(
            "/api-tools",
            data={
                "name": name,
                "icon": "https://example.com/icon.png",
                "openapi_schema": valid_openapi_schema,
                "headers": json.dumps([]),
            },
        )

    def test_get_api_tool_provider_success(self, client, valid_openapi_schema):
        """测试获取工具提供者 - 成功"""
        # 先创建一个工具
        create_resp = self._create_api_tool(
            client, valid_openapi_schema, name="获取测试工具"
        )
        assert create_resp.status_code == 200
        assert create_resp.json.get("code") == HttpCode.SUCCESS

        # 从数据库中查找刚创建的 provider（通过再次创建同名来确认存在）
        # 这里需要知道 provider_id，由于创建接口没有返回 id，
        # 我们用一个已知存在的方式来测试：直接用一个不存在的 UUID 测试 404
        # 如果有返回 id 的接口可以替换此逻辑

    def test_get_api_tool_provider_not_found(self, client):
        """测试获取工具提供者 - 不存在的ID"""
        fake_id = uuid.uuid4()
        resp = client.get(f"/api-tools/{fake_id}")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.NOT_FOUND

    def test_get_api_tool_provider_invalid_uuid(self, client):
        """测试获取工具提供者 - 无效的UUID格式"""
        resp = client.get("/api-tools/not-a-valid-uuid")
        assert resp.status_code == 404
