import uuid
from datetime import datetime
from typing import cast

from sqlalchemy import (
    UUID,
    DateTime,
    PrimaryKeyConstraint,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from internal.extension.database_extension import db

from .base import BaseModel


class ApiToolProvider(BaseModel):
    """接口工具提供者模型"""

    __tablename__ = "api_tool_provider"

    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_tool_provider_id"),
        # Index("idx_api_tool_provider_account_id_name", "account_id", "name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, nullable=False, server_default=text("uuid_generate_v4()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    icon: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text")
    )
    openapi_schema: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    headers: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at: Mapped[datetime] = mapped_column(
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

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, nullable=False, server_default=text("uuid_generate_v4()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    provider_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text")
    )
    url: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    method: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    parameters: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )

    @property
    def provider(self) -> "ApiToolProvider":
        """只读属性，返回当前工具关联/归属的工具提供者信息"""
        return cast(
            "ApiToolProvider", db.session.query(ApiToolProvider).get(self.provider_id)
        )
