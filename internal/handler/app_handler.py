from flask import request
from openai import APIError, APITimeoutError, APIConnectionError

from internal.schema.app_schema import CompletionReq
from pkg.response import success_json, validate_error_json, fail_json
from internal.exception import CustomException
from internal.service import AppService
from injector import inject
from dataclasses import dataclass
from pkg.response import success_message
import uuid

# LangChain 相关导入
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import trim_messages
import os

# 自定义的中文文件存储
from internal.extension.chinese_file_chat_history import ChineseFileChatMessageHistory


@inject
@dataclass
class AppHandler:
    #  应用控制器
    app_service: AppService

    def __init__(self, app_service: AppService):
        """初始化 AppHandler"""
        self.app_service = app_service

        # ============ 文件存储配置 ============
        # 设置对话历史的存储目录
        # 每个 session_id 会对应一个 JSON 文件
        self.memory_storage_path = (
            "/Users/luobin/project/llmops/llmops-api/storage/memory"
        )

        # 确保存储目录存在（如果不存在则创建）
        os.makedirs(self.memory_storage_path, exist_ok=True)

        # ============ 消息修剪器配置 ============
        # 用于限制历史消息数量，避免 token 过多
        # 这是 LangChain v1.0 替代 ConversationBufferWindowMemory 的方式
        self.message_trimmer = trim_messages(
            max_tokens=6,  # 最多保留6条消息（3轮对话：3个用户消息 + 3个AI消息）
            strategy="last",  # 保留最后（最新）的消息
            token_counter=lambda msgs: len(msgs),  # 按消息数量计数（简化版）
            include_system=False,  # 不包含系统消息（系统消息在 prompt 中单独定义）
            allow_partial=False,  # 不允许部分消息（确保消息完整性）
            start_on="human",  # 确保从用户消息开始（保持对话逻辑完整）
        )

    def ping(self):
        # raise CustomException("数据未找到")
        return {"ping": "pong"}

    def create_app(self):
        """调用服务创建新的APP记录"""
        app = self.app_service.create_app()
        return success_message(f"应用已经成功创建了,id为{app.id}")

    def get_app(self, id: uuid.UUID):
        app = self.app_service.get_app(id)
        return success_json(
            f"应用已经成功查询了,id为{app.id}"
        )  # 直接传模型对象,Flask 会自动序列化

    def update_app(self, id: uuid.UUID):
        app = self.app_service.update_app(id)
        return success_json(f"应用已经成功更新了,id为{app.id}，名字为{app.name}")

    def delete_app(self, id: uuid.UUID):
        result = self.app_service.delete_app(id)
        if result:
            return success_message(f"应用已经成功删除了, id为{id}")
        else:
            return fail_json({"message": "应用不存在或删除失败"})

    def debug(self, app_id: uuid.UUID):
        """
        聊天接口 - 使用 LangChain 实现

        流程: prompt → llm → parser
        """
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 1. 提取用户输入
        query = request.json.get("query")

        # 2. 构建 Prompt 模板
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是OpenAI开发的聊天机器人，请根据用户的输入回复对应的信息",
                ),
                ("human", "{query}"),
            ]
        )

        # 3. 创建 LLM 实例 (会自动读取 OPENAI_API_KEY 和 OPENAI_API_BASE 环境变量)
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            timeout=60.0,  # 超时时间
        )

        # 4. 创建输出解析器 (将 AIMessage 转为纯字符串)
        parser = StrOutputParser()

        # 5. 使用 LCEL 构建链: prompt | llm | parser
        chain = prompt | llm | parser

        try:
            # 6. 执行链，获取结果
            content = chain.invoke({"query": query})
            return success_json({"content": content})

        except APITimeoutError:
            return fail_json({"message": "请求超时，请稍后重试"})
        except APIConnectionError:
            return fail_json({"message": "无法连接到AI服务，请检查网络或稍后重试"})
        except APIError as e:
            return fail_json({"message": f"AI服务异常: {str(e)}"})

    def get_session_history(self, session_id: str) -> ChineseFileChatMessageHistory:
        """
        会话历史管理器（文件存储版本）

        功能: 获取或创建指定会话的历史记录（存储在文件中）

        参数:
            session_id: 会话唯一标识符（如用户ID、会话ID等）

        返回:
            ChineseFileChatMessageHistory: 该会话的消息历史对象（文件存储，支持中文）

        工作原理:
            1. 根据 session_id 生成文件路径
            2. 创建 ChineseFileChatMessageHistory 对象
            3. 对话历史自动保存到 JSON 文件
            4. 下次请求时自动从文件加载

        文件存储:
            - 存储路径: /Users/luobin/project/llmops/llmops-api/storage/memory/
            - 文件命名: {session_id}.json
            - 格式: JSON（自动序列化/反序列化）
            - 持久化: 服务重启后数据不会丢失

        示例:
            session_id = "user_001"
            → 文件路径: /Users/.../storage/memory/user_001.json
            → 文件内容: [{"type": "human", "content": "你好"}, ...]
        """
        # 构建文件路径: 存储目录 + chat_history_{session_id}.json
        file_path = os.path.join(
            self.memory_storage_path, f"chat_history_{session_id}.json"
        )

        # 创建并返回文件存储的历史对象（支持中文）
        # ChineseFileChatMessageHistory 会自动处理文件的读写
        # 并且中文字符会正常显示，不会转义为 \uXXXX
        return ChineseFileChatMessageHistory(file_path)

    def memory_debug(self, app_id: uuid.UUID):
        """
        带记忆功能的聊天接口 - 使用窗口缓冲记忆

        功能: 实现多轮对话，保留最近3轮对话历史

        记忆策略:
            - 使用窗口缓冲记忆（Window Buffer Memory）
            - 只保留最近6条消息（3轮对话）
            - 超过6条时，自动删除最早的消息
            - 类似于人的短期记忆：只记得最近的对话

        流程:
            1. 获取用户输入和会话ID
            2. 从存储中加载该会话的历史记录
            3. 使用 trimmer 修剪历史（只保留最近6条）
            4. 构建完整的 prompt（系统提示 + 历史 + 当前问题）
            5. 调用 LLM 生成回复
            6. 保存本轮对话到历史记录
            7. 返回结果
        """
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # ============ 1. 提取请求参数 ============
        query = request.json.get("query")  # 用户输入
        session_id = request.json.get(
            "session_id", "default_session"
        )  # 会话ID（默认值）

        # ============ 2. 构建 Prompt 模板（包含历史占位符） ============
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是OpenAI开发的聊天机器人，请根据对应的上下文回复用户问题",
                ),
                # MessagesPlaceholder: 历史消息的占位符
                # 运行时会被实际的历史消息列表替换
                MessagesPlaceholder("history"),
                ("human", "{query}"),  # 当前用户输入
            ]
        )

        # ============ 3. 创建 LLM 实例 ============
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            timeout=60.0,
        )

        # ============ 4. 创建输出解析器 ============
        parser = StrOutputParser()

        # ============ 5. 加载并处理历史消息 ============
        # 5.1 获取该会话的历史记录对象（文件存储）
        # 文件路径: /Users/.../storage/memory/{session_id}.json
        history = self.get_session_history(session_id)

        # 5.2 获取所有历史消息（从文件自动加载）
        messages = history.messages

        # 5.3 使用 trimmer 修剪消息（只保留最近6条）
        # 这是 v1.0 替代 ConversationBufferWindowMemory 的核心逻辑
        trimmed_messages = self.message_trimmer.invoke(messages)

        # ============ 6. 构建链并执行 ============
        # LCEL 链: prompt | llm | parser
        chain = prompt | llm | parser

        try:
            # 6.1 执行链，传入当前问题和修剪后的历史
            content = chain.invoke(
                {"query": query, "history": trimmed_messages}  # 只传入最近6条消息
            )

            # ============ 7. 保存本轮对话到历史 ============
            # 7.1 保存用户消息（自动写入文件）
            history.add_user_message(query)

            # 7.2 保存AI回复（自动写入文件）
            history.add_ai_message(content)

            # ============ 8. 返回结果（包含调试信息） ============
            return success_json(
                {
                    "content": content,
                    "debug_info": {
                        "session_id": session_id,
                        "storage_path": os.path.join(
                            self.memory_storage_path, f"chat_history_{session_id}.json"
                        ),  # 文件路径
                        "total_messages": len(history.messages),  # 当前总消息数
                        "trimmed_messages": len(trimmed_messages),  # 实际使用的消息数
                        "window_size": 6,  # 窗口大小
                        "storage_type": "file",  # 存储类型
                        "note": "对话历史已保存到文件，服务重启后不会丢失",
                    },
                }
            )

        except APITimeoutError:
            return fail_json({"message": "请求超时，请稍后重试"})
        except APIConnectionError:
            return fail_json({"message": "无法连接到AI服务，请检查网络或稍后重试"})
        except APIError as e:
            return fail_json({"message": f"AI服务异常: {str(e)}"})
