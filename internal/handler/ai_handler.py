from dataclasses import dataclass

from flask_login import current_user, login_required
from injector import inject

from internal.schema.ai_schema import (
    AutoGeneratePromptReq,
    GenerateSuggestedQuestionsReq,
    OptimizePromptReq,
)
from internal.service import AIService
from pkg.response import compact_generate_response, success_json, validate_error_json


@inject
@dataclass
class AIHandler:
    """AI 辅助模块处理器"""

    ai_service: AIService

    @login_required
    def optimize_prompt(self):
        """根据传递的预设prompt进行优化"""
        req = OptimizePromptReq()
        if not req.validate():
            return validate_error_json(req.errors)
        resp = self.ai_service.optimize_prompt(str(req.prompt.data))
        return compact_generate_response(resp)

    @login_required
    def generate_suggested_questions(self):
        """根据传递的消息ID生成建议问题列表"""
        req = GenerateSuggestedQuestionsReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 调用服务生成建议问题列表
        suggested_questions = (
            self.ai_service.generate_suggested_questions_from_message_id(
                req.message_id.data, account=current_user
            )
        )
        return success_json(suggested_questions)

    @login_required
    def auto_generate_prompt(self):
        req = AutoGeneratePromptReq()
        if not req.validate():
            return validate_error_json(req.errors)
        return success_json(self.ai_service.auto_generate_prompt(req.app_id.data))
