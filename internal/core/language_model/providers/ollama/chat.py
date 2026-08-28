"""Ollama 本地离线聊天模型。

基于 langchain_ollama 的 ChatOllama 实现，并继承项目自定义的
BaseLanguageModel 以满足智能体对 features / metadata 等属性的依赖。
当未显式传入 base_url 时，回退到环境变量 OLLAMA_URL。

注意：使用该提供商需要额外安装依赖 langchain-ollama。
"""

import os

from langchain_ollama import ChatOllama

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatOllama, BaseLanguageModel):
    """Ollama 聊天模型。"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            base_url=kwargs.get("base_url") or os.getenv("OLLAMA_URL"),
            **kwargs,
        )
