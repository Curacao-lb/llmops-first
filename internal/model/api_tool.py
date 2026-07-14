from sqlalchemy import (
    UUID,
    Column,
    DateTime,
    PrimaryKeyConstraint,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db

from .base import BaseModel


class ApiToolProvider(BaseModel):
    """接口工具提供者模型"""

    __tablename__ = "api_tool_provider"

    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_tool_provider_id"),
        # Index("idx_api_tool_provider_account_id_name", "account_id", "name"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    name = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    icon = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    description = Column(Text, nullable=False, server_default=text("''::text"))
    openapi_schema = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    headers = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )

    @property
    def tools(self) -> list["ApiTool"]:
        return db.session.query(ApiTool).filter_by(provider_id=self.id).all()


class ApiTool(BaseModel):
    """API工具表模型"""

    __tablename__ = "api_tool"

    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_tool_id"),
        # Index("idx_api_tool_account_id", "account_id"),
        # Index("idx_api_tool_provider_id_name", "provider_id", "name"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    provider_id = Column(UUID, nullable=False)
    name = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    description = Column(Text, nullable=False, server_default=text("''::text"))
    url = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    method = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    parameters = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )

    @property
    def provider(self) -> "ApiToolProvider":
        """只读属性，返回当前工具关联/归属的工具提供者信息"""
        return db.session.query(ApiToolProvider).get(self.provider_id)
