"""通义千问（Tongyi/Qwen）聊天模型。

基于 langchain_community 的 ChatTongyi 实现，并继承项目自定义的
BaseLanguageModel 以满足智能体对 features / metadata 等属性的依赖。
当未显式传入 api_key 时，回退到环境变量 DASHSCOPE_API_KEY。
"""

import os

from langchain_community.chat_models.tongyi import ChatTongyi

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatTongyi, BaseLanguageModel):
    """通义千问聊天模型。"""

    def __init__(self, *args, **kwargs):
        # 将 api_key 映射到 ChatTongyi 的 dashscope_api_key 字段，未显式传入时回退到环境变量。
        kwargs["dashscope_api_key"] = kwargs.pop("api_key", None) or os.getenv(
            "DASHSCOPE_API_KEY"
        )
        super().__init__(*args, **kwargs)
