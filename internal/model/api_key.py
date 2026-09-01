import uuid
from datetime import datetime
from typing import cast

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    Index,
    PrimaryKeyConstraint,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from internal.extension.database_extension import db

from .account import Account


class ApiKey(db.Model):
    """API秘钥模型"""

    __tablename__ = "api_key"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_key_id"),
        Index("api_key_account_id_idx", "account_id"),
        Index("api_key_api_key_idx", "api_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, nullable=False, server_default=text("uuid_generate_v4()")
    )  # 记录id
    account_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)  # 关联账号id
    api_key: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 加密后的api秘钥
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )  # 是否激活，为true时可以使用
    remark: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 备注信息
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )

    @property
    def account(self) -> "Account":
        """只读属性，返回该秘钥归属的账号信息"""
        return cast(Account, db.session.query(Account).get(self.account_id))
