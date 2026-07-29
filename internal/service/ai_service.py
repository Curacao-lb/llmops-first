import json
from collections.abc import Generator
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.entity.ai_entity import (
    OPTIMIZE_PROMPT_TEMPLATE,
    SUPERVISOR_DEFAULT_PROMPT_TEMPLATE,
)
from internal.exception import ForbiddenException
from internal.model import Account, App, AppConfigVersion, Message
from pkg.sqlalchemy import SQLAlchemy

from .base_service import BaseService
from .conversation_service import ConversationService


@inject
@dataclass
class AIService(BaseService):
    """AI 服务"""

    db: SQLAlchemy
    conversation_service: ConversationService

    def auto_generate_prompt(self, app_id: UUID) -> str:
        app: App = self.get(App, app_id)
        config: AppConfigVersion = app.draft_app_config

        work_agents = []
        if config.agents:
            for id in config.agents:
                agent: App = self.get(App, id)
                work_agents.append(f"- {agent.name}: {agent.description}")

        prompt = SUPERVISOR_DEFAULT_PROMPT_TEMPLATE.format(
            agents="\n".join(work_agents)
        )
        prompt_template = ChatPromptTemplate.from_messages(
            [("system", OPTIMIZE_PROMPT_TEMPLATE), ("human", "{prompt}")]
        )

        llm = ChatOpenAI(model="o4-mini", temperature=0.5)
        optimize_chain = prompt_template | llm | StrOutputParser()
        return optimize_chain.invoke({"prompt": prompt})
        # return prompt

    def generate_suggested_questions_from_message_id(
        self, message_id: UUID, account: Account
    ) -> list[str]:
        """根据传递的消息id+账号生成建议问题列表"""

        # 1. 查询消息并校验权限消息
        message = self.get(Message, message_id)
        if not message or message.created_by != account.id:
            raise ForbiddenException("该消息不存在或无权限")

        # 2.构建对话历史列表
        histories = f"Human: {message.query}\nAI: {message.answer}"

        # 3.调用服务生成建议服务
        return self.conversation_service.generate_suggested_questions(histories)

    @classmethod
    def optimize_prompt(cls, prompt: str) -> Generator[str]:
        """根据传递的prompt进行优化生成"""
        # 构建优化prompt的提示词模板
        prompt_template = ChatPromptTemplate.from_messages(
            [("system", OPTIMIZE_PROMPT_TEMPLATE), ("human", "{prompt}")]
        )

        # 构建LLM
        llm = ChatOpenAI(model="o4-mini", temperature=0.5)

        # 组装优化链
        optimize_chain = prompt_template | llm | StrOutputParser()

        # 调用链并流式事件返回
        for optimize_prompt in optimize_chain.stream({"prompt": prompt}):
            # 组装响应数据
            data = {"optimize_prompt": optimize_prompt}
            yield f"event: optimize_prompt\ndata: {json.dumps(data)}\n\n"
