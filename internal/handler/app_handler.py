import json
import os
import uuid
from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Any

from flask import request
from openai import APIError, APITimeoutError, APIConnectionError
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

from internal.schema.app_schema import (
    CompletionReq,
    GetAppsWithPageReq,
    GetAppsWithPageResp,
)
from pkg.response import (
    compact_generate_response,
    fail_json,
    success_json,
    validate_error_json,
)
from pkg.paginator import PageModel
from internal.exception import CustomException
from injector import inject
from pkg.response import success_message

# LangChain 相关导入
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, trim_messages

# 自定义的中文文件存储
from internal.extension.chinese_file_chat_history import ChineseFileChatMessageHistory

# from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.service import ApiToolService, AppService, ConversationService


@inject
@dataclass
class AppHandler:
    #  应用控制器
    app_service: AppService
    provider_factory: BuiltinProviderManager
    api_tool_service: ApiToolService
    conversation_service: ConversationService

    def __post_init__(self):
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
        # tool_factory = self.provider_factory.get_tool("tavily", "tavily_search")
        # if tool_factory is None:
        #     raise CustomException("tavily_search 工具未加载")

        # tavily = tool_factory()
        # result = tavily.invoke({"query": "2025北京半程马拉松 男子前三名 成绩 以及 女子前三名 成绩"})

        # tavily = self.provider_factory.get_provider("tavily")
        # tavily_search_entity = tavily.get_tool_entity("tavily_search")
        # print("tavily_search_entity:", tavily_search_entity)

        # return {
        #     "ping": "pong"
        #     # , "tavily": result
        # }

        # providers = self.provider_factory.get_provider_entities()

        # return success_json([provider.dict() for provider in providers])
        human_message = "你好，我是ro小bin，你是？"
        ai_message = """你好 ro 小 bin～我是chatgpt呀，很高兴认识你！"""
        old_summary = "人类询问AI关于LLM（大语言模型）和Agent（智能体）的定义及其关系。AI解释道，LLM是基于海量文本数据训练的大型神经网络，能够理解和生成自然语言，具备问答、翻译、写文案等基础能力，但存在局限，如缺乏自主目标、无法主动规划等。常见的LLM例子包括GPT系列等。 \n\nAgent则是以LLM为核心，结合记忆、规划、工具调用和反思模块的智能系统，能够自主设定目标并完成复杂任务。Agent的四大核心组件包括负责思考的LLM大脑、短期和长期记忆模块、自动拆分目标的规划模块，以及能够调用外部工具的能力。相比之下，LLM只能被动回答，而Agent可以在给定目标后自动完成任务。\n\n总结：LLM是理解和生成自然语言的基础模型，具备一定能力但缺乏主动性；Agent是基于LLM的智能体，具备自主目标和复杂任务处理能力。"
        # summary = self.conversation_service.summary(
        #     human_message, ai_message, old_summary
        # )

        # conversation_name = self.conversation_service.generate_conversation_name(
        #     human_message
        # )

        questions = self.conversation_service.generate_suggested_questions(
            human_message
        )

        return success_json({"conversation_name": conversation_name})

        # return success_json({"summary": summary})
        # return self.api_tool_service.api_tool_invoke()

    def create_app(self):
        """调用服务创建新的APP记录"""
        app = self.app_service.create_app()
        return success_message(f"应用已经成功创建了,id为{app.id}")

    def get_apps_with_page(self):
        """获取应用列表信息,该接口支持分页"""
        req = GetAppsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)
        apps, paginator = self.app_service.get_apps_with_page(req)
        resp = GetAppsWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(apps), paginator=paginator))

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
        带记忆功能的聊天接口 - 使用 RunnableWithMessageHistory
        """
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        query = request.json.get("query")
        session_id = request.json.get("session_id", "default_session")

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

        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            timeout=60.0,
        )
        parser = StrOutputParser()

        def trim_history(input_dict, config):
            # RunnableWithMessageHistory 会将当前会话对应的 history
            # 注入到 config["configurable"]["message_history"] 中。
            # 这样链内部就可以通过第二个参数直接拿到 memory 实例。
            memory = config.get("configurable", {}).get("message_history")
            history = memory.messages if memory else input_dict.get("history", [])
            trimmed_history = self.message_trimmer.invoke(history)
            return {"query": input_dict["query"], "history": trimmed_history}

        chain = RunnableLambda(trim_history) | prompt | llm | parser
        with_message_history = RunnableWithMessageHistory(
            chain,
            self.get_session_history,
            input_messages_key="query",
            history_messages_key="history",
        )

        try:
            content = with_message_history.invoke(
                {"query": query},
                config={"configurable": {"session_id": session_id}},
            )

            history = self.get_session_history(session_id)
            messages = history.messages
            trimmed_messages = self.message_trimmer.invoke(messages)

            return success_json(
                {
                    "content": content,
                    "debug_info": {
                        "session_id": session_id,
                        "storage_path": os.path.join(
                            self.memory_storage_path, f"chat_history_{session_id}.json"
                        ),  # 文件路径
                        "total_messages": len(messages),  # 当前总消息数
                        "trimmed_messages": len(trimmed_messages),  # 实际使用的消息数
                        "window_size": 6,  # 窗口大小
                        "storage_type": "file",  # 存储类型
                        "note": "使用 RunnableWithMessageHistory，通过 configurable 传递 memory，并自动修剪历史",
                    },
                }
            )

        except APITimeoutError:
            return fail_json({"message": "请求超时，请稍后重试"})
        except APIConnectionError:
            return fail_json({"message": "无法连接到AI服务，请检查网络或稍后重试"})
        except APIError as e:
            return fail_json({"message": f"AI服务异常: {str(e)}"})

    def stream_debug(self, app_id: uuid.UUID):
        """应用会话调试聊天接口，该接口为流式事件输出"""
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 图在后台线程中运行；请求线程只负责把队列里的事件转成 SSE。
        q = Queue()
        query = req.query.data
        finished = object()

        def emit(event: str, event_type: str, data: Any, message_id: str) -> None:
            """将内部事件统一放进队列，data 保持为 JSON 字符串以兼容前端事件协议。"""
            q.put(
                {
                    "id": message_id,
                    "event": event,
                    "type": event_type,
                    "data": json.dumps(data, ensure_ascii=False, default=str),
                }
            )

        def build_tools() -> list[Any]:
            """创建本次执行可用的内置工具，并为高德工具提供默认配置。"""
            tool_configs = [
                ("tavily", "tavily_search", {}),
                (
                    "gaode",
                    "gaode_weather",
                    {
                        "api_key": os.getenv("GAODE_API_KEY")
                        or os.getenv("AMAP_API_KEY"),
                        "url": os.getenv("GAODE_API_BASE_URL")
                        or "https://restapi.amap.com/v3",
                    },
                ),
                ("dalle", "dalle3", {}),
            ]
            tools = []
            for provider_name, tool_name, kwargs in tool_configs:
                tool_factory = self.provider_factory.get_tool(provider_name, tool_name)
                if tool_factory is None:
                    raise RuntimeError(f"内置工具未加载: {provider_name}/{tool_name}")
                tools.append(tool_factory(**kwargs))
            return tools

        def graph_app() -> None:
            """创建并执行包含工具调用分支的 LangGraph。"""
            message_id = str(uuid.uuid4())
            try:
                tools = build_tools()
                llm = ChatOpenAI(
                    model="gpt-4o-mini", temperature=0.7, timeout=60.0
                ).bind_tools(tools)

                def chatbot(state: MessagesState) -> dict[str, list[Any]]:
                    """流式调用模型，同时累计 chunk 作为图节点的最终输出。"""
                    gathered = None
                    for chunk in llm.stream(state["messages"]):
                        tool_call_chunks = (
                            getattr(chunk, "tool_call_chunks", None) or []
                        )
                        tool_calls = getattr(chunk, "tool_calls", None) or []
                        content = chunk.content

                        # 部分模型会先给一个没有任何内容的初始化 chunk，忽略即可。
                        if not content and not tool_call_chunks and not tool_calls:
                            continue

                        gathered = chunk if gathered is None else gathered + chunk

                        if content:
                            emit(
                                "message",
                                "text",
                                {"content": content},
                                message_id,
                            )
                        if tool_call_chunks or tool_calls:
                            emit(
                                "agent_thought",
                                "tool_call",
                                tool_call_chunks or tool_calls,
                                message_id,
                            )

                    return (
                        {"messages": [gathered]}
                        if gathered is not None
                        else {"messages": []}
                    )

                tool_node = ToolNode(tools)

                def execute_tools(state: MessagesState) -> dict[str, list[Any]]:
                    """执行工具，并将工具观察结果也作为流事件返回给客户端。"""
                    result = tool_node.invoke(state)
                    for tool_message in result.get("messages", []):
                        emit(
                            "agent_thought",
                            "tool_result",
                            {
                                "tool_call_id": getattr(
                                    tool_message, "tool_call_id", None
                                ),
                                "tool_name": getattr(tool_message, "name", None),
                                "content": tool_message.content,
                            },
                            message_id,
                        )
                    return result

                workflow = StateGraph(MessagesState)
                workflow.add_node("chatbot", chatbot)
                workflow.add_node("tools", execute_tools)
                workflow.add_edge(START, "chatbot")
                workflow.add_conditional_edges("chatbot", tools_condition)
                workflow.add_edge("tools", "chatbot")

                workflow.compile().invoke({"messages": [HumanMessage(content=query)]})
                emit("message_end", "end", {"status": "completed"}, message_id)
            except (APITimeoutError, APIConnectionError, APIError) as error:
                emit("error", "llm_error", {"message": str(error)}, message_id)
            except Exception as error:
                emit("error", "server_error", {"message": str(error)}, message_id)
            finally:
                q.put(finished)

        def generate():
            """按 SSE 协议从队列持续输出事件，直至图程序结束。"""
            worker = Thread(target=graph_app, daemon=True)
            worker.start()

            while True:
                event = q.get()
                if event is finished:
                    break
                yield (
                    f"event: {event['event']}\n"
                    f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
                )

        response = compact_generate_response(generate())
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Accel-Buffering"] = "no"
        return response
