from __future__ import annotations

import uuid
from abc import abstractmethod
from collections.abc import Iterator
from threading import Thread
from typing import Any, cast

from langchain_core.load import Serializable
from langchain_core.runnables import Runnable
from langgraph.graph.state import CompiledStateGraph, RunnableConfig
from pydantic import PrivateAttr

from internal.core.agent.entities.agent_entity import AgentConfig, AgentState
from internal.core.agent.entities.queue_entity import (
    AgentResult,
    QueueEvent,
)
from internal.core.language_model.entities.model_entity import BaseLanguageModel
from internal.exception import FailException

from .agent_queue_manager import AgentQueueManager


class BaseAgent(Serializable, Runnable):
    """基于Runnable的基础智能体基类"""

    name: str | None = None
    llm: BaseLanguageModel
    agent_config: AgentConfig
    _agent: CompiledStateGraph | None = PrivateAttr(None)
    _agent_queue_manager: AgentQueueManager | None = PrivateAttr(None)
    collaborative_agent: dict[str, Any] | None = None
    description: str | None = None
    zh_name: str | None = None

    class Config:
        # 字段允许接收任意类型，且不需要校验器
        arbitrary_types_allowed = True

    def __init__(
        self,
        llm: BaseLanguageModel,
        agent_config: AgentConfig,
        *args,
        **kwargs,
    ):
        # 构造函数，初始化智能体图结构程序
        super().__init__(*args, llm=llm, agent_config=agent_config, **kwargs)
        self._agent = self._build_agent()
        self._agent_queue_manager = AgentQueueManager(
            user_id=agent_config.user_id,
            # task_id=task_id,
            invoke_from=agent_config.invoke_from,
            # redis_client=redis_client,
        )

    @abstractmethod
    def _build_agent(self) -> CompiledStateGraph:
        raise NotImplementedError("_build_agent函数未实现")

    def invoke(
        self,
        input: AgentState,
        config: RunnableConfig | None = None,
        **kwargs: Any | None,
    ) -> AgentResult:
        """块内容响应，一次性生成完整内容后返回"""
        # 1.调用stream方法获取流式事件输出数据
        content = input["messages"][0].content
        query = ""
        image_urls: list[str] = []
        if isinstance(content, str):
            query = content
        elif isinstance(content, list):
            content_list = cast(list[dict[str, Any]], content)
            query = content_list[0]["text"]
            image_urls = [
                chunk["image_url"]["url"]
                for chunk in content_list
                if chunk.get("type") == "image_url"
            ]
        agent_result = AgentResult(query=query, image_urls=image_urls)
        agent_thoughts = {}
        for agent_thought in self.stream(input, config):
            # 2.提取事件id并转换成字符串
            event_id = str(agent_thought.id)

            # 3.除了ping事件，其他事件全部记录
            if agent_thought.event != QueueEvent.PING:
                # 4.单独处理agent_message事件，因为该事件为数据叠加
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    # 5.检测是否已存储了事件
                    if event_id not in agent_thoughts:
                        # 6.初始化智能体消息事件
                        agent_thoughts[event_id] = agent_thought
                    else:
                        # 7.叠加智能体消息事件
                        agent_thoughts[event_id] = agent_thoughts[event_id].model_copy(
                            update={
                                "thought": agent_thoughts[event_id].thought
                                + agent_thought.thought,
                                "answer": agent_thoughts[event_id].answer
                                + agent_thought.answer,
                                # token / 费用字段按覆盖取最新值：流式片段事件均为 0，
                                # 只有流式结束后补发的最终事件才带真实值，若不 copy 进来
                                # 会一直保留第一条的 0，导致落库的 token/费用统计丢失。
                                "message": agent_thought.message,
                                "message_token_count": agent_thought.message_token_count,
                                "message_unit_price": agent_thought.message_unit_price,
                                "message_price_unit": agent_thought.message_price_unit,
                                "answer_token_count": agent_thought.answer_token_count,
                                "answer_unit_price": agent_thought.answer_unit_price,
                                "answer_price_unit": agent_thought.answer_price_unit,
                                "total_token_count": agent_thought.total_token_count,
                                "total_price": agent_thought.total_price,
                                "latency": agent_thought.latency,
                            }
                        )
                    # 8.更新智能体消息答案
                    agent_result.answer += agent_thought.answer
                else:
                    # 9.处理其他类型的智能体事件，类型均为覆盖
                    agent_thoughts[event_id] = agent_thought

                    # 10.单独判断是否为异常消息类型，如果是则修改状态并记录错误
                    if agent_thought.event in [
                        QueueEvent.STOP,
                        QueueEvent.TIMEOUT,
                        QueueEvent.ERROR,
                    ]:
                        agent_result.status = agent_thought.event
                        agent_result.error = (
                            agent_thought.observation
                            if agent_thought.event == QueueEvent.ERROR
                            else ""
                        )

        # 11.将推理字典转换成列表并存储
        agent_result.agent_thoughts = list(agent_thoughts.values())

        # 12.完善message
        agent_result.message = next(
            (
                agent_thought.message
                for agent_thought in agent_thoughts.values()
                if agent_thought.event == QueueEvent.AGENT_MESSAGE
            ),
            [],
        )

        # 13.更新总耗时
        agent_result.latency = sum(
            [agent_thought.latency for agent_thought in agent_thoughts.values()]
        )

        return agent_result

    def stream(
        self,
        input: AgentState,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> Iterator[Any]:
        """在线程中执行Agent图，并通过队列返回流式事件。"""
        """流式输出，每个node节点或者LLM每生成一个token则会返回相应内容"""

        # 1.检测子类是否已构建Agent智能体，如果未构建则抛出错误
        agent = self._agent
        if agent is None:
            raise FailException("智能体未成功构建，请核实后尝试")

        # 2.构建对应的任务id及数据初始化
        input["task_id"] = input.get("task_id", uuid.uuid4())
        input["history"] = input.get("history", [])
        input["iteration_count"] = input.get("iteration_count", 0)
        task_id = input["task_id"]

        # 在启动工作线程之前先创建好队列，避免工作线程(publish)与监听线程(listen)
        # 并发懒创建出两个不同的队列，导致最早发布的事件(如长期记忆召回)丢失
        queue_manager = self._agent_queue_manager
        if queue_manager is None:
            raise FailException("智能体队列管理器未初始化，请核实后尝试")
        queue_manager.queue(task_id)

        def invoke_agent() -> None:
            try:
                agent.invoke(input, config=config, **kwargs)
            except Exception as exc:
                queue_manager.publish_error(task_id, exc)

        # 3.创建子线程并执行
        thread = Thread(target=invoke_agent, daemon=True)
        thread.start()
        # 4.调用队列管理器监听数据并返回迭代器
        yield from queue_manager.listen(task_id)

    @property
    def agent_queue_manager(self) -> AgentQueueManager:
        if self._agent_queue_manager is None:
            raise FailException("智能体队列管理器未初始化，请核实后尝试")
        return self._agent_queue_manager

    # @property
    # def graph(self) -> CompiledStateGraph:
    #     return self._agent
