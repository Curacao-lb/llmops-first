import json
import uuid
from collections.abc import Generator
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from injector import inject

from internal.core.agent.entities.agent_entity import AgentState
from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.entity.app_entity import AppStatus
from internal.entity.conversation_entity import InvokeFrom, MessageStatus
from internal.exception import ForbiddenException, NotFoundException
from internal.model import Account, Conversation, EndUser, Message
from internal.schema.openapi_schema import OpenAPIChatReq
from pkg.response import Response
from pkg.sqlalchemy import SQLAlchemy

from .agent_service import AgentService
from .app_config_service import AppConfigService
from .app_service import AppService
from .base_service import BaseService
from .conversation_service import ConversationService


@inject
@dataclass
class OpenAPIService(BaseService):
    """开放API服务"""

    db: SQLAlchemy
    app_service: AppService
    app_config_service: AppConfigService
    conversation_service: ConversationService
    agent_service: AgentService

    def chat(self, req: OpenAPIChatReq, account: Account):
        """根据传递的请求+账号信息发起聊天对话，返回数据为块内容或者生成器"""
        # 判断当前应用是否属于当前账号
        app = self.app_service.get_app(uuid.UUID(cast(str, req.app_id.data)), account)

        # 判断当前应用是否已发布
        if app.status != AppStatus.PUBLISHED:
            raise NotFoundException("该应用不存在或未发布，请核实后重试")

        # 判断是否传递了终端用户id，如果传递了则检测终端用户关联的应用
        if req.end_user_id.data:
            end_user = self.get(EndUser, req.end_user_id.data)
            if not end_user or end_user.app_id != app.id:
                raise ForbiddenException("当前账号不存在或不属于该应用，请核实后重试")
        else:
            # 如果不存在则创建一个终端用户
            end_user = self.create(
                EndUser,
                **{"tenant_id": account.id, "app_id": app.id},
            )

        # 检测是否传递了会话id，如果传递了需要检测会话的归属信息
        if req.conversation_id.data:
            conversation = self.get(Conversation, req.conversation_id.data)
            if (
                not conversation
                or conversation.app_id != app.id
                or conversation.invoke_from != InvokeFrom.SERVICE_API
                or conversation.created_by != end_user.id
            ):
                raise ForbiddenException(
                    "该会话不存在，或者不属于该应用/终端用户/调用方式"
                )
        else:
            # 如果不存在则创建会话信息
            conversation = self.create(
                Conversation,
                **{
                    "app_id": app.id,
                    "name": "New Conversation",
                    "invoke_from": InvokeFrom.SERVICE_API,
                    "created_by": end_user.id,
                },
            )

        # 获取校验后的运行时配置
        app_config = self.app_config_service.get_app_config(app)

        # 新建一条消息记录
        message = self.create(
            Message,
            **{
                "app_id": app.id,
                "conversation_id": conversation.id,
                "invoke_from": InvokeFrom.SERVICE_API,
                "created_by": end_user.id,
                "query": req.query.data,
                "image_urls": req.image_urls.data,
                "status": MessageStatus.NORMAL,
            },
        )

        agent, history, llm = self.agent_service.create_agent(
            app_config, app, InvokeFrom.SERVICE_API, conversation
        )

        # 定义智能体状态基础数据
        agent_state: AgentState = {
            "messages": [
                llm.convert_to_human_message(
                    cast(str, req.query.data),
                    req.image_urls.data,
                    app_config["multimodal"]["enable"],
                )
            ],
            "task_id": uuid.uuid4(),
            "iteration_count": 0,
            "history": history,
            "long_term_memory": conversation.summary,
        }

        # 提前将需要的ORM属性取成普通变量，避免在惰性执行的生成器中访问已脱离Session的ORM对象
        account_id = cast(UUID, account.id)
        app_id = cast(UUID, app.id)
        end_user_id = cast(UUID, end_user.id)
        conversation_id = cast(UUID, conversation.id)
        message_id = cast(UUID, message.id)

        # 根据stream类型差异执行不同的代码
        if req.stream.data is True:
            agent_thoughts_dict = {}

            def handle_stream() -> Generator:
                """流式事件处理器，在Python只要在函数内部使用了yield关键字，那么这个函数的返回值类型肯定是生成器"""
                for agent_thought in agent.stream(agent_state):
                    # 提取thought以及answer
                    event_id = str(agent_thought.id)

                    # 将数据填充到agent_thought，便于存储到数据库服务中
                    if agent_thought.event != QueueEvent.PING:
                        # 除了agent_message数据为叠加，其他均为覆盖
                        if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                            if event_id not in agent_thoughts_dict:
                                # 初始化智能体消息事件
                                agent_thoughts_dict[event_id] = agent_thought
                            else:
                                # 叠加智能体消息
                                agent_thoughts_dict[event_id] = agent_thoughts_dict[
                                    event_id
                                ].model_copy(
                                    update={
                                        "thought": agent_thoughts_dict[event_id].thought
                                        + agent_thought.thought,
                                        "answer": agent_thoughts_dict[event_id].answer
                                        + agent_thought.answer,
                                        "latency": agent_thought.latency,
                                    }
                                )
                        else:
                            # 处理其他类型事件的消息
                            agent_thoughts_dict[event_id] = agent_thought
                    data = {
                        **agent_thought.model_dump(
                            include={
                                "event",
                                "thought",
                                "observation",
                                "tool",
                                "tool_input",
                                "answer",
                                "latency",
                            }
                        ),
                        "id": event_id,
                        "end_user_id": str(end_user_id),
                        "conversation_id": str(conversation_id),
                        "message_id": str(message_id),
                        "task_id": str(agent_thought.task_id),
                    }
                    yield f"event: {agent_thought.event}\ndata:{json.dumps(data)}\n\n"

                # 将消息以及推理过程添加到数据库
                self.conversation_service.save_agent_thoughts(
                    account_id=account_id,
                    app_id=app_id,
                    app_config=app_config,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    agent_thoughts=list(agent_thoughts_dict.values()),
                )

            return handle_stream()

        # 块内容输出
        agent_result = agent.invoke(agent_state)

        # 将消息以及推理过程添加到数据库
        self.conversation_service.save_agent_thoughts(
            account_id=cast(UUID, account.id),
            app_id=cast(UUID, app.id),
            app_config=app_config,
            conversation_id=cast(UUID, conversation.id),
            message_id=cast(UUID, message.id),
            agent_thoughts=cast(list[AgentThought], agent_result.agent_thoughts),
        )

        return Response(
            data={
                "id": str(message.id),
                "end_user_id": str(end_user.id),
                "conversation_id": str(conversation.id),
                "query": req.query.data,
                "image_urls": req.image_urls.data,
                "answer": agent_result.answer,
                "total_token_count": 0,
                "latency": agent_result.latency,
                "agent_thoughts": [
                    {
                        "id": str(agent_thought.id),
                        "event": agent_thought.event,
                        "thought": agent_thought.thought,
                        "observation": agent_thought.observation,
                        "tool": agent_thought.tool,
                        "tool_input": agent_thought.tool_input,
                        "latency": agent_thought.latency,
                        "created_at": 0,
                    }
                    for agent_thought in agent_result.agent_thoughts
                ],
            }
        )
