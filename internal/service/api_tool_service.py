from dataclasses import dataclass
from internal.exception import ValidateException, NotFoundException
from internal.core.tools.api_tools.entites import OpenAPISchema, ToolEntity
from internal.core.tools.api_tools.providers import ApiProviderManager
from internal.model import ApiTool, ApiToolProvider, Account
from internal.schema.api_tool_schema import (
    CreateApiToolReq,
    GetApiToolProvidersWithPageReq,
    UpdateApiToolProviderReq,
)
from pkg.paginator import Paginator
from typing import Any
from sqlalchemy import desc

from uuid import UUID

from injector import inject
import json

from .base_service import BaseService


@inject
@dataclass
class ApiToolService(BaseService):
    """自定义API插件服务"""

    api_provider_manager: ApiProviderManager

    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str) -> OpenAPISchema:
        """解析传递的openapi_schema字符串,如果出错则抛出错误"""

        try:
            data = json.loads(openapi_schema_str.strip())
        except (json.JSONDecodeError, AttributeError) as exc:
            raise ValidateException("格式错误") from exc

        if not isinstance(data, dict):
            raise ValidateException("格式错误")

        return OpenAPISchema(**data)

    def create_api_tool_provider(self, req: CreateApiToolReq, account: Account) -> None:
        """根据传递的请求创建自定义API工具"""

        # 1.检验并提取openapi_schema对应的数据
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 2.查询当前登录的账号是否已经创建了同名的工具提供者,如果是则抛出错误
        api_tool_provider = (
            self.db.session.query(ApiToolProvider)
            .filter_by(account_id=account.id, name=req.name.data)
            .one_or_none()
        )

        if api_tool_provider:
            raise ValidateException(f"该工具{req.name.data}已存在")

        # 3.首先创建工具提供者，并获取工具提供者的id信息，然后再创建工具信息
        api_tool_provider = self.create(
            ApiToolProvider,
            account_id=account.id,
            name=req.name.data,
            icon=req.icon.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
            headers=req.headers.data,
        )

        # 4.创建api工具并关联 api_tool_provider
        for (
            path,
            path_item,
        ) in openapi_schema.paths.items():  # pylint: disable=no-member
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account.id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def get_api_tool_provider(
        self, provider_id: UUID, account: Account
    ) -> ApiToolProvider:
        """根据传递的provider_id获取API工具提供者信息"""

        # 1.查询数据库获取对应的数据
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        # 2.检验数据是否为空，并且判读是否属于当前账号
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise NotFoundException("该工具提供者不存在")
        return api_tool_provider

    def get_api_tool_providers_with_page(
        self, req: GetApiToolProvidersWithPageReq, account: Account
    ) -> tuple[list[Any], Paginator]:
        """获取自定义API工具服务提供者分页列表数据"""

        paginator = Paginator(db=self.db, req=req)
        filters = [ApiToolProvider.account_id == account.id]
        if req.search_word.data:
            filters.append(ApiToolProvider.name.ilike(f"%{req.search_word.data}%"))
        api_tool_providers = paginator.paginate(
            self.db.session.query(ApiToolProvider)
            .filter(*filters)
            .order_by(desc("created_at"))
        )
        return api_tool_providers, paginator

    def get_api_tool(
        self, provider_id: UUID, tool_name: str, account: Account
    ) -> ApiTool:
        """根据传递的provider_id+tool_name获取对应工具的参数详情信息"""

        api_tool = (
            self.db.session.query(ApiTool)
            .filter_by(
                provider_id=provider_id,
                name=tool_name,
            )
            .one_or_none()
        )
        if api_tool is None or api_tool.account_id != account.id:
            raise NotFoundException("该工具不存在")
        return api_tool

    def delete_api_tool_provider(self, provider_id: UUID, account: Account) -> None:
        """根据传递的provider_id删除对应的API工具提供者"""

        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise NotFoundException("工具提供者不存在")

        with self.db.auto_commit():
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account.id,
            ).delete()
            self.db.session.delete(api_tool_provider)

    def update_api_tool_provider(
        self, provider_id: UUID, req: UpdateApiToolProviderReq, account: Account
    ):
        """根据传递的provider_id+req更新对应的API工具提供者信息"""
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise ValidateException("该工具提供者不存在")
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)
        check_api_tool_provider = (
            self.db.session.query(ApiToolProvider)
            .filter(
                ApiToolProvider.account_id == account.id,
                ApiToolProvider.name == req.name.data,
                ApiToolProvider.id != api_tool_provider.id,
            )
            .one_or_none()
        )
        if check_api_tool_provider:
            raise ValidateException(f"该工具提供者{req.name.data}已存在")
        with self.db.auto_commit():
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == api_tool_provider.id,
                ApiTool.account_id == account.id,
            ).delete()

        self.update(
            api_tool_provider,
            name=req.name.data,
            icon=req.icon.data,
            headers=req.headers.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
        )

        for (
            path,
            path_item,
        ) in openapi_schema.paths.items():  # pylint: disable=no-member
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account.id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def api_tool_invoke(self):
        provider_id = "cf2d6d2d-7e8f-4b15-b966-880116172dc0"
        tool_name = "get_weather"

        api_tool = (
            self.db.session.query(ApiTool)
            .filter(ApiTool.provider_id == provider_id, ApiTool.name == tool_name)
            .one_or_none()
        )
        if api_tool is None:
            raise NotFoundException("该工具不存在")

        api_tool_provider = api_tool.provider

        tool = self.api_provider_manager.get_tool(
            ToolEntity(
                id=provider_id,
                name=tool_name,
                url=api_tool.url,
                method=api_tool.method,
                description=api_tool.description,
                headers=api_tool_provider.headers,
                parameters=api_tool.parameters,
            )
        )

        return tool.invoke({"city": "武汉"})
