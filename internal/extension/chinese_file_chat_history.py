"""
自定义的文件聊天历史存储类
支持中文字符的正常显示（不转义为 Unicode）
"""

import json
from pathlib import Path
from typing import List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict,
)


class ChineseFileChatMessageHistory(BaseChatMessageHistory):
    r"""
    文件聊天历史存储类（支持中文）

    功能:
        - 将对话历史保存到 JSON 文件
        - 中文字符正常显示（不转义为 \uXXXX）
        - 自动创建目录
        - 自动加载历史

    与 FileChatMessageHistory 的区别:
        - 使用 ensure_ascii=False 保存 JSON
        - 使用 indent=2 格式化 JSON（更易读）
        - 中文字符直接显示

    示例:
        history = ChineseFileChatMessageHistory("user_001.json")
        history.add_user_message("你好")
        history.add_ai_message("你好！")

        # 文件内容:
        # [
        #   {"type": "human", "data": {"content": "你好"}},
        #   {"type": "ai", "data": {"content": "你好！"}}
        # ]
    """

    def __init__(self, file_path: str):
        """
        初始化文件聊天历史

        参数:
            file_path: JSON 文件路径
        """
        self.file_path = Path(file_path)

        # 确保父目录存在
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # 如果文件不存在，创建空文件
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    @property
    def messages(self) -> List[BaseMessage]:
        """
        获取所有消息

        返回:
            消息列表
        """
        try:
            # 读取 JSON 文件
            items = json.loads(self.file_path.read_text(encoding="utf-8"))
            # 将字典转换为消息对象
            return messages_from_dict(items)
        except (json.JSONDecodeError, FileNotFoundError):
            # 如果文件损坏或不存在，返回空列表
            return []

    def add_message(self, message: BaseMessage) -> None:
        """
        添加一条消息

        参数:
            message: 要添加的消息对象
        """
        # 获取现有消息
        messages = self.messages
        # 添加新消息
        messages.append(message)
        # 保存到文件
        self._save_messages(messages)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """
        批量添加消息

        参数:
            messages: 要添加的消息列表
        """
        # 获取现有消息
        existing_messages = self.messages
        # 添加新消息
        existing_messages.extend(messages)
        # 保存到文件
        self._save_messages(existing_messages)

    def clear(self) -> None:
        """清空所有消息"""
        self._save_messages([])

    def _save_messages(self, messages: List[BaseMessage]) -> None:
        """
        保存消息到文件（内部方法）

        参数:
            messages: 要保存的消息列表
        """
        # 将消息对象转换为字典
        items = [message_to_dict(m) for m in messages]

        # 保存到文件
        # ensure_ascii=False: 中文字符不转义
        # indent=2: 格式化 JSON，更易读
        self.file_path.write_text(
            json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
        )
