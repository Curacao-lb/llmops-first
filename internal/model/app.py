from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    DateTime,
    PrimaryKeyConstraint,
    Index,
    text,
    Integer,
)

from sqlalchemy.dialects.postgresql import JSONB

import uuid
from datetime import datetime
from typing import Optional
from .base import BaseModel
from internal.extension.database_extension import db
from internal.entity.app_entity import AppConfigType


class App(db.Model):
    """
    AI应用基础模型类

    用于存储用户创建的 AI 应用信息,包括应用名称、图标、描述等基本信息
    """

    # 数据库表名
    __tablename__ = "app"

    # 表级别的参数配置: 定义主键约束和索引
    __table_args__ = (
        # 主键约束: 显式定义 id 字段为主键,约束名为 pk_app_id
        # 虽然 Column 中已定义 primary_key=True,但这里显式声明可以自定义约束名称
        PrimaryKeyConstraint("id", name="pk_app_id"),
        # 索引: 为 account_id 字段创建索引,索引名为 idx_app_account_id
        # 作用: 加速按账户 ID 查询应用的操作(如 SELECT * FROM app WHERE account_id = ?)
        # 常见场景: 查询某个用户的所有应用
        Index("app_account_id_idx", "account_id"),
        Index("app_token_idx", "token"),
    )

    # 主键: 应用唯一标识符,使用 UUID 格式,自动生成
    id = Column(
        UUID,
        # primary_key=True,
        nullable=False,
        # 数据库层面的默认值（PostgreSQL）
        server_default=text("uuid_generate_v4()"),
    )

    # 外键: 关联的账户 ID,标识应用的所有者
    account_id = Column(UUID, nullable=False)  # 创建账号id
    app_config_id = Column(UUID, nullable=True)  # 发布配置id，当值为空时代表没有发布
    draft_app_config_id = Column(UUID, nullable=True)  # 关联的草稿配置id
    debug_conversation_id = Column(
        UUID, nullable=True
    )  # 应用调试会话id，为None则代表没有会话信息

    # 应用名称: 最大 255 字符,默认为空字符串
    name = Column(String(255), server_default=("''::character varying"), nullable=False)
    en_name = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 应用英文名字

    # 应用图标: 存储图标 URL 或路径,最大 255 字符
    icon = Column(String(255), server_default=("''::character varying"), nullable=False)

    # 应用描述: 使用 Text 类型支持长文本,默认为空字符串
    description = Column(Text, server_default=("''::text"), nullable=False)

    token = Column(
        String(255), nullable=True, server_default=text("''::character varying")
    )  # 应用凭证信息

    # 更新时间: 记录最后一次修改时间,每次更新时自动更新
    updated_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
        nullable=False,
    )

    # 创建时间: 记录应用创建时间,只在创建时设置一次
    created_at = Column(
        DateTime, server_default=text("CURRENT_TIMESTAMP(0)"), nullable=False
    )

    # 尝试新增一个字段：status
    status = Column(
        String(50), server_default=("''::character varying"), nullable=False
    )

    mode = Column(
        Integer, nullable=False, server_default=text("0")
    )  # 模式 0:单agent模式 1:supervisor模式

    @property
    def draft_app_config(self) -> Optional["AppConfigVersion"]:
        """只读属性，返回当前应用的草稿配置。

        这是一个纯读取属性，不存在时返回 None，且不会产生任何写入或提交副作用。
        若需要「不存在则创建默认草稿配置」的业务行为，请调用
        AppService.get_draft_app_config_in_get_app()。
        """
        return (
            db.session.query(AppConfigVersion)
            .filter(
                AppConfigVersion.app_id == self.id,
                AppConfigVersion.config_type == AppConfigType.DRAFT,
            )
            .one_or_none()
        )


class AppConfig(db.Model):
    """应用配置模型"""

    __tablename__ = "app_config"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_config_id"),
        # Index("app_config_app_id_idx", "app_id"),
    )

    id = Column(
        UUID, nullable=False, server_default=text("uuid_generate_v4()")
    )  # 配置id
    app_id = Column(UUID, nullable=False)  # 关联应用id
    model_config = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 模型配置
    dialog_round = Column(
        Integer, nullable=False, server_default=text("0")
    )  # 鞋带上下文轮数
    preset_prompt = Column(
        Text, nullable=False, server_default=text("''::text")
    )  # 预设prompt
    tools = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联工具列表
    agents = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联的agent列表
    workflows = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联的工作流列表
    retrieval_config = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 检索配置
    long_term_memory = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 长期记忆配置
    opening_statement = Column(
        Text, nullable=False, server_default=text("''::text")
    )  # 开场白文案
    opening_questions = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 开场白建议问题列表
    speech_to_text = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 语音转文本配置
    text_to_speech = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 文本转语音配置
    multimodal = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 开启多模态
    mcp_server = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # mcp配置
    suggested_after_answer = Column(
        JSONB,
        nullable=False,
        server_default=text("'{\"enable\": true}'::jsonb"),
    )  # 回答后生成建议问题
    review_config = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 审核配置
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )

    @property
    def app_dataset_joins(self) -> list["AppDatasetJoin"]:
        """只读属性，获取配置的知识库关联记录"""
        return (
            db.session.query(AppDatasetJoin)
            .filter(AppDatasetJoin.app_id == self.app_id)
            .all()
        )


class AppConfigVersion(db.Model):
    """应用配置版本历史表，用于存储草稿配置+历史发布配置"""

    __tablename__ = "app_config_version"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_config_version_id"),
        Index("app_config_version_app_id_idx", "app_id"),
    )

    id = Column(
        UUID, nullable=False, server_default=text("uuid_generate_v4()")
    )  # 配置id
    app_id = Column(UUID, nullable=False)  # 关联应用id
    model_config = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 模型配置
    dialog_round = Column(
        Integer, nullable=False, server_default=text("0")
    )  # 鞋带上下文轮数
    preset_prompt = Column(
        Text, nullable=False, server_default=text("''::text")
    )  # 人设与回复逻辑
    tools = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联的工具列表
    agents = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联的agent列表
    workflows = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联的工作流列表
    datasets = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联的知识库列表
    retrieval_config = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 检索配置
    long_term_memory = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 长期记忆配置
    opening_statement = Column(
        Text, nullable=False, server_default=text("''::text")
    )  # 开场白文案
    opening_questions = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 开场白建议问题列表
    speech_to_text = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 语音转文本配置
    multimodal = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 开启多模态
    text_to_speech = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 文本转语音配置
    mcp_server = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # mcp配置
    suggested_after_answer = Column(
        JSONB,
        nullable=False,
        server_default=text("'{\"enable\": true}'::jsonb"),
    )  # 回答后生成建议问题
    review_config = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 审核配置
    version = Column(Integer, nullable=False, server_default=text("0"))  # 发布版本号
    config_type = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 配置类型
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )


class AppDatasetJoin(BaseModel):
    """应用知识库关联表模型"""

    __tablename__ = "app_dataset_join"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_dataset_join_id"),
        Index("app_dataset_join_app_id_dataset_id_idx", "app_id", "dataset_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    app_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )
