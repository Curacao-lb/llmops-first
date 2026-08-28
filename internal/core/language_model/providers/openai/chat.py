"""OpenAI（及 OpenAI 兼容）聊天模型。

该类同时继承 langchain 的 ChatOpenAI 与项目自定义的 BaseLanguageModel，
因此既拥有 ChatOpenAI 的全部能力，又满足智能体对 features / metadata /
get_pricing 等自定义属性的依赖，可直接作为 BaseAgent.llm 使用。
"""

import tiktoken
from langchain_openai import ChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatOpenAI, BaseLanguageModel):
    """OpenAI 兼容的聊天模型，附带 features 与 pricing 元数据。"""

    def _get_encoding_model(self) -> tuple[str, tiktoken.Encoding]:
        """重写获取编码模型的方法，统一使用 gpt-3.5-turbo 的词表，
        避免自定义/兼容模型名字无法匹配 tiktoken 词表而报错。"""
        model = "gpt-3.5-turbo"
        return model, tiktoken.encoding_for_model(model)
