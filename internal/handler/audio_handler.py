from dataclasses import dataclass
from typing import cast
from uuid import UUID

from flask_login import current_user, login_required
from injector import inject

from internal.model import Account
from internal.schema.audio_schema import AudioToTextReq, MessageToAudioReq
from internal.service import AudioService
from pkg.response import compact_generate_response, success_json, validate_error_json


@inject
@dataclass
class AudioHandler:
    """语音处理器"""

    audio_service: AudioService

    @login_required
    def audio_to_text(self):
        """将语音转换成文本"""
        req = AudioToTextReq()
        if not req.validate():
            return validate_error_json(req.errors)

        text = self.audio_service.audio_to_text(
            req.file.data,
            UUID(cast(str, req.app_id.data)),
            cast(Account, current_user),
            req.web_app_token.data,
        )

        return success_json({"text": text})

    @login_required
    def message_to_audio(self):
        """将消息转换成流式输出音频"""
        req = MessageToAudioReq()
        if not req.validate():
            return validate_error_json(req.errors)

        response = self.audio_service.message_to_audio(
            UUID(cast(str, req.message_id.data)),
            cast(Account, current_user),
        )

        return compact_generate_response(response)
