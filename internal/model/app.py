from sqlalchemy import Column, UUID, String, Text, DateTime, PrimaryKeyConstraint, Index
import uuid
from datetime import datetime
from .base import BaseModel


class App(BaseModel):
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
        Index("idx_app_account_id", "account_id"),
    )

    # 主键: 应用唯一标识符,使用 UUID 格式,自动生成
    id = Column(UUID, primary_key=True, default=uuid.uuid4, nullable=False)

    # 外键: 关联的账户 ID,标识应用的所有者
    account_id = Column(UUID, nullable=False)

    # 应用名称: 最大 255 字符,默认为空字符串
    name = Column(String(255), default="", nullable=False)

    # 应用图标: 存储图标 URL 或路径,最大 255 字符
    icon = Column(String(255), default="", nullable=False)

    # 应用描述: 使用 Text 类型支持长文本,默认为空字符串
    description = Column(Text, default="", nullable=False)

    # 更新时间: 记录最后一次修改时间,每次更新时自动更新
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # 创建时间: 记录应用创建时间,只在创建时设置一次
    created_at = Column(DateTime, default=datetime.now, nullable=False)
