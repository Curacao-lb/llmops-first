import json

import pytest

from pkg.response import HttpCode


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
