import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    Float,
    Index,
    PrimaryKeyConstraint,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from internal.extension.database_extension import db


class Workflow(db.Model):
    """工作流模型"""

    __tablename__ = "workflow"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_workflow_id"),
        Index("workflow_account_id_idx", "account_id"),
        Index("workflow_tool_call_name_idx", "tool_call_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, nullable=False, server_default=text("uuid_generate_v4()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)  # 创建账号id
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 工作流名字
    tool_call_name: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 工作流工具调用名字
    icon: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 工作流图标
    description: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text")
    )  # 应用描述
    graph: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 运行时配置
    draft_graph: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 草稿图配置
    is_debug_passed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )  # 是否调试通过
    status: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 工作流状态
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )  # 发布时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )


class WorkflowResult(db.Model):
    """工作流存储结果模型"""

    __tablename__ = "workflow_result"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_workflow_result_id"),
        Index("workflow_result_app_id_idx", "app_id"),
        Index("workflow_result_account_id_idx", "account_id"),
        Index("workflow_result_workflow_id_idx", "workflow_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, nullable=False, server_default=text("uuid_generate_v4()")
    )  # 结果id
    app_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, nullable=True
    )  # 工作流调用的应用id，如果为空则代表非应用调用
    account_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)  # 创建账号id
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID, nullable=False
    )  # 结果关联的工作流id
    graph: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 运行时配置
    state: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 工作流最终状态
    latency: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0.0")
    )  # 消息的总耗时
    status: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 运行状态
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )
