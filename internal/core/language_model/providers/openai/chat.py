"""OpenAI（及 OpenAI 兼容）聊天模型。

该类同时继承 langchain 的 ChatOpenAI 与项目自定义的 BaseLanguageModel，
因此既拥有 ChatOpenAI 的全部能力，又满足智能体对 features / metadata /
get_pricing 等自定义属性的依赖，可直接作为 BaseAgent.llm 使用。
"""

from langchain_openai import ChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatOpenAI, BaseLanguageModel):
    """OpenAI 兼容的聊天模型，附带 features 与 pricing 元数据。"""
