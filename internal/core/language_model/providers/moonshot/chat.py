"""月之暗面（Moonshot）聊天模型。

Moonshot 提供 OpenAI 兼容的接口，这里继承 langchain 的 BaseChatOpenAI 与
项目自定义的 BaseLanguageModel。当未显式传入 api_key / base_url 时，
回退到环境变量 MOONSHOT_API_KEY / MOONSHOT_API_BASE_URL。
"""

import os

import tiktoken
from langchain_openai.chat_models.base import BaseChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(BaseChatOpenAI, BaseLanguageModel):
    """月之暗面聊天模型。"""

    def __init__(self, *args, **kwargs):
        # 将 api_key / base_url 映射到 OpenAI 兼容参数，未显式传入时回退到环境变量。
        kwargs["api_key"] = kwargs.get("api_key") or os.getenv("MOONSHOT_API_KEY")
        kwargs["base_url"] = kwargs.get("base_url") or os.getenv(
            "MOONSHOT_API_BASE_URL"
        )
        super().__init__(*args, **kwargs)

    def _get_encoding_model(self) -> tuple[str, tiktoken.Encoding]:
        """Moonshot 无对应 tiktoken 词表，统一使用 gpt-3.5-turbo 防止报错。"""
        model = "gpt-3.5-turbo"
        return model, tiktoken.encoding_for_model(model)
