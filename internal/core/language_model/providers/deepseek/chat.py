"""深度求索（DeepSeek）聊天模型。

DeepSeek 提供 OpenAI 兼容的接口，这里继承 langchain 的 BaseChatOpenAI 与
项目自定义的 BaseLanguageModel，将传入的 api_key / base_url 映射到 OpenAI
兼容参数上，同时满足智能体对 features / metadata 等属性的依赖。
"""

import tiktoken
from langchain_openai.chat_models.base import BaseChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(BaseChatOpenAI, BaseLanguageModel):
    """DeepSeek 聊天模型。"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            openai_api_key=kwargs.get("api_key"),
            openai_api_base=kwargs.get("base_url"),
            **kwargs,
        )

    def _get_encoding_model(self) -> tuple[str, tiktoken.Encoding]:
        """DeepSeek 无对应 tiktoken 词表，统一使用 gpt-3.5-turbo 防止报错。"""
        model = "gpt-3.5-turbo"
        return model, tiktoken.encoding_for_model(model)
