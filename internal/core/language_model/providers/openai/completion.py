"""OpenAI 文本补全（completion）模型。

该类同时继承 langchain 的 OpenAI 与项目自定义的 BaseLanguageModel，
用于 model_type 为 completion 的场景。
"""

from langchain_openai import OpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Completion(OpenAI, BaseLanguageModel):
    """OpenAI 兼容的文本补全模型，附带 features 与 pricing 元数据。"""
