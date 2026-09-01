import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    DateTime,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class UploadFile(BaseModel):
    """上传文件模型"""

    __tablename__ = "upload_file"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_upload_file_id"),
        Index("upload_file_account_id_idx", "account_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, nullable=False, server_default=text("uuid_generate_v4()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    key: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    size: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    extension: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    mime_type: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    hash: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        onupdate=datetime.now,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )
