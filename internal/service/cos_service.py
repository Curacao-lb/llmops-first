import hashlib
import os
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from flask import has_request_context, request
from injector import inject
from qcloud_cos import CosS3Client, CosConfig
from werkzeug.datastructures import FileStorage

from internal.entity.upload_file_entity import (
    ALLOW_IMAGE_EXTENSION,
    ALL_DOCUMENT_EXTENSION,
)
from internal.exception import FailException
from internal.model import UploadFile, Account
from .upload_file_service import UploadFileService


@inject
@dataclass
class CosService:
    upload_file_service: UploadFileService

    def upload_file(
        self, file: FileStorage, account: Account, only_image: bool = False
    ) -> UploadFile:

        filename = file.filename
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in (ALLOW_IMAGE_EXTENSION + ALL_DOCUMENT_EXTENSION):
            raise FailException(f"该.{extension}扩展的文件不允许上传")
        elif only_image and extension not in ALLOW_IMAGE_EXTENSION:
            raise FailException(f"该.{extension}扩展的文件不允许上传,请上传正确的图片")

        random_filename = str(uuid.uuid4()) + "." + extension
        now = datetime.now()
        upload_filename = f"{now.year}/{now.month:02d}/{now.day:02d}/{random_filename}"
        file_content = file.stream.read()
        if not file_content:
            raise FailException("上传文件不能为空")
        if self.is_local_provider():
            self.save_local_file(upload_filename, file_content)
        else:
            client = self.get_client()
            bucket = self.get_bucket()
            try:
                client.put_object(bucket, file_content, upload_filename)
            except Exception as exc:
                raise FailException("上传文件失败，请稍后重试") from exc
        return self.upload_file_service.create_upload_file(
            account_id=account.id,
            name=filename,
            key=upload_filename,
            size=len(file_content),
            extension=extension,
            mime_type=file.mimetype,
            hash=hashlib.sha3_256(file_content).hexdigest(),
        )

    def download_file(self, key: str, target_file_path: str):
        if self.is_local_provider():
            source_file_path = self.get_local_file_path(key)
            if not os.path.exists(source_file_path):
                raise FailException("文件不存在或已被删除")
            shutil.copyfile(source_file_path, target_file_path)
            return

        client = self.get_client()
        bucket = self.get_bucket()
        client.download_file(bucket, key, target_file_path)

    @classmethod
    def get_file_url(cls, key: str) -> str:
        if cls.is_local_provider():
            base_url = os.getenv("LOCAL_UPLOAD_BASE_URL")
            if not base_url and has_request_context():
                base_url = request.host_url.rstrip("/")
            if not base_url:
                base_url = "http://localhost:8000"
            return f"{base_url}/uploaded-files/{key}"

        cos_domain = os.getenv("COS_DOMAIN")
        if not cos_domain:
            bucket = cls.get_bucket()
            schema = os.getenv("COS_SCHEMA", "https")
            region = cls.get_region()
            cos_domain = f"{schema}://{bucket}.cos.{region}.myqcloud.com"
        return f"{cos_domain}/{key}"

    @classmethod
    def get_client(cls) -> CosS3Client:
        region = cls.get_region()
        secret_id = cls.get_required_env("COS_SECRET_ID")
        secret_key = cls.get_required_env("COS_SECRET_KEY")
        conf = CosConfig(
            Region=region,
            SecretId=secret_id,
            SecretKey=secret_key,
            Token=None,
            Scheme=os.getenv("COS_SCHEMA", "https"),
        )
        return CosS3Client(conf)

    @classmethod
    def get_bucket(cls) -> str:
        return cls.get_required_env("COS_BUCKET")

    @classmethod
    def get_region(cls) -> str:
        return cls.get_required_env("COS_REGION")

    @classmethod
    def get_required_env(cls, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise FailException(f"{key}环境变量未配置")
        return value

    @classmethod
    def is_local_provider(cls) -> bool:
        return os.getenv("UPLOAD_PROVIDER", "local").lower() == "local"

    @classmethod
    def get_local_upload_dir(cls) -> str:
        upload_dir = os.getenv("LOCAL_UPLOAD_DIR")
        if upload_dir:
            return upload_dir
        return str(Path(__file__).resolve().parents[2] / "storage" / "uploads")

    @classmethod
    def get_local_file_path(cls, key: str) -> str:
        upload_dir = os.path.abspath(cls.get_local_upload_dir())
        file_path = os.path.abspath(os.path.join(upload_dir, key))
        if os.path.commonpath([upload_dir, file_path]) != upload_dir:
            raise FailException("文件路径不合法")
        return file_path

    @classmethod
    def save_local_file(cls, key: str, file_content: bytes) -> None:
        file_path = cls.get_local_file_path(key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_content)
