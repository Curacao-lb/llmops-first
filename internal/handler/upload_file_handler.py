from dataclasses import dataclass

from flask_login import current_user, login_required
from injector import inject

from internal.schema.upload_file_schema import UploadImageReq
from internal.service import CosService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class UploadFileHandler:
    """上传文件处理器"""

    cos_service: CosService

    @login_required
    def upload_image(self):
        """上传图片文件"""

        req = UploadImageReq()
        if not req.validate():
            return validate_error_json(req.errors)

        upload_file = self.cos_service.upload_file(
            req.file.data, account=current_user, only_image=True
        )
        image_url = self.cos_service.get_file_url(upload_file.key)
        return success_json({"image_url": image_url})
