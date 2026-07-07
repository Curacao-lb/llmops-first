from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired, FileSize

from internal.entity.upload_file_entity import ALLOW_IMAGE_EXTENSION


class UploadImageReq(FlaskForm):
    """上传图片请求"""

    file = FileField(
        "file",
        validators=[
            FileRequired("上传图片不能为空"),
            FileSize(max_size=15 * 1024 * 1024, message="上传图片最大不能超过15MB"),
            FileAllowed(
                ALLOW_IMAGE_EXTENSION,
                message=f"仅允许上传{'/'.join(ALLOW_IMAGE_EXTENSION)}格式文件",
            ),
        ],
    )
