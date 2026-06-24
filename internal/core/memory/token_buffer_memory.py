from dataclasses import dataclass

from langchain_core.messages import (
    AnyMessage,
    AIMessage,
    HumanMessage,
    trim_messages,
    get_buffer_string,
)
from sqlalchemy import desc

# from internal.core.language_model.entities.model_entity import BaseLanguageModel
from langchain_core.language_models import BaseLanguageModel
from internal.entity.conversation_entity import MessageStatus
from internal.model import Conversation, Message
from pkg.sqlalchemy import SQLAlchemy


@dataclass
class TokenBufferMemory:
    """基于token计数的缓冲记忆组件"""

    conversation: Conversation  # 会话模型
    db: SQLAlchemy  # 数据库实例
    model_instance: BaseLanguageModel  # LLM 大语言模型

    def get_history_prompt_messages(
        self,
        max_token_limit: int = 2000,
        message_limit: int = 10,
        multimodal: bool = False,
    ) -> list[AnyMessage]:
        """根据传递的token限制+消息条数限制获取指定会话模型的历史消息列表"""
        # 判断会话是否存在
        if self.conversation is None:
            return []
        messages = (
            # 查询该会话的消息列表,并且使用时间进行倒序,同时匹配答案不为空、匹配会话id、没有软删除、状态是正常
            self.db.session.query(Message)
            .filter(
                Message.conversation_id == self.conversation.id,
                Message.answer != "",
                Message.is_deleted == False,
                Message.status.in_(
                    [MessageStatus.STOP, MessageStatus.NORMAL, MessageStatus.TIMEOUT]
                ),
            )
            .order_by(desc("created_at"))
            .limit(message_limit)
            # 调用 .all() 时，SQLAlchemy 才会把前面拼好的条件翻译成真正的 SQL 语句
            .all()
        )
        messages = list(reversed(messages))

        # 将 message 转换成 Langchain 消息列表
        prompt_messages = []
        for message in messages:
            prompt_messages.extend(
                [
                    # self.model_instance.convert_to_human_message(
                    #     message.query, message.image_urls, multimodal
                    # ),
                    HumanMessage(content=message.query),
                    AIMessage(content=message.answer),
                ]
            )
        # 调用Langchain集成的trim_messages剪切消息列表
        return trim_messages(
            messages=prompt_messages,
            max_tokens=max_token_limit,
            token_counter=self.model_instance,
            strategy="last",
            start_on="human",
            end_on="ai",
        )

    def get_history_prompt_text(
        self,
        human_prefix: str = "Human",
        ai_prefix: str = "AI",
        max_token_limit: int = 2000,
        message_limit: int = 10,
        multimodal: bool = False,
    ) -> str:
        """根据传递的数据获取指定会话历史消息提示文本（短期记忆的文本形式，用于文本生成模型）"""
        # 1.根据传递的消息获取历史消息文本
        messages = self.get_history_prompt_messages(
            max_token_limit, message_limit, multimodal
        )
        # 2.将消息列表转化成文本
        return get_buffer_string(messages, human_prefix, ai_prefix)
