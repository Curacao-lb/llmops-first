import asyncio
import json
import logging
import time
import uuid
from typing import Any, cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    AnyMessage,
    HumanMessage,
    RemoveMessage,
    SystemMessage,
    ToolMessage,
    messages_to_dict,
)
from langchain_core.runnables import RunnableConfig
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from internal.core.agent.entities.agent_entity import (
    AGENT_SYSTEM_PROMPT_TEMPLATE,
    DATASET_RETRIEVAL_TOOL_NAME,
    MAX_ITERATION_RESPONSE,
    AgentState,
)
from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.exception import FailException

from .base_agent import BaseAgent


class FunctionCallAgent(BaseAgent):
    """基于函数调用/工具调用的智能体"""

    def run(
        self,
        query: str,  # 用户提问的原始问题
        history: list[AnyMessage] | None = None,  # 短期记忆
        long_term_memory: str = "",  # 长期记忆
    ):
        """运行智能体应用，并使用yield关键字返回对应数据"""
        # 1.预处理传递的数据
        if history is None:
            history = []

        # 2.调用智能体获取数据
        return self.invoke(
            {
                "messages": [HumanMessage(content=query)],
                "history": history,
                "long_term_memory": long_term_memory,
                "task_id": uuid.uuid4(),
                "iteration_count": 0,
            }
        )

    def invoke(
        self,
        input: AgentState,  # pylint: disable=redefined-builtin
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ):
        """调用已编译的智能体图。"""
        return self._agent.invoke(input, config=config, **kwargs)

    def _build_agent(self) -> CompiledStateGraph:
        """构建智能体图结构程序。"""
        return self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        """构建 langgraph 图结构编译程序"""
        # 1.创建图
        graph = StateGraph(AgentState)

        # 2.添加节点
        graph.add_node("long_term_memory_recall", self._long_term_memory_recall_node)
        graph.add_node("llm", self._llm_node)
        graph.add_node("tools", self._tools_node)

        # 3.添加边，并设置起点和终点
        graph.set_entry_point("long_term_memory_recall")
        graph.add_edge("long_term_memory_recall", "llm")
        graph.add_conditional_edges("llm", self._tools_condition)
        graph.add_edge("tools", "llm")

        # 4.编译应用并返回
        agent = graph.compile()

        return agent

    # def _build_agent(self) -> CompiledStateGraph:
    #     graph = StateGraph(AgentState)
    #     # 添加节点
    #     graph.add_node("preset_operation", self._preset_operation_node)
    #     graph.add_node("long_term_memory_recall", self._long_term_memory_recall_node)
    #     graph.add_node("llm", self._llm_node)
    #     graph.add_node("tools", self._tools_node)

    #     graph.set_entry_point("preset_operation")
    #     graph.add_conditional_edges(
    #         "preset_operation", self._preset_operation_condition
    #     )
    #     graph.add_edge("long_term_memory_recall", "llm")
    #     graph.add_conditional_edges("llm", self._tools_condition)
    #     graph.add_edge("tools", "llm")

    #     agent = graph.compile()
    #     return agent

    # def _preset_operation_node(self, state: AgentState) -> AgentState:
    #     """预设操作，涵盖：输入审核、数据预处理、条件边等"""
    #     # 获取审核配置与用户输入query
    #     review_config = self.agent_config.review_config
    #     query = state["messages"][-1].content

    #     # 检测是否开启审核配置
    #     if review_config["enable"] and review_config["inputs_config"]["enable"]:
    #         contains_keyword = any(
    #             keyword in query for keyword in review_config["keywords"]
    #         )
    #         # 如果包含敏感词则执行后续步骤
    #         if contains_keyword:
    #             preset_response = review_config["inputs_config"]["preset_response"]
    #             self.agent_queue_manager.publish(
    #                 state["task_id"],
    #                 AgentThought(
    #                     id=uuid.uuid4(),
    #                     task_id=state["task_id"],
    #                     event=QueueEvent.AGENT_MESSAGE,
    #                     thought=preset_response,
    #                     message=messages_to_dict(state["messages"]),
    #                     answer=preset_response,
    #                     latency=0,
    #                 ),
    #             )
    #             self.agent_queue_manager.publish(
    #                 state["task_id"],
    #                 AgentThought(
    #                     id=uuid.uuid4(),
    #                     task_id=state["task_id"],
    #                     event=QueueEvent.AGENT_END,
    #                 ),
    #             )
    #             return {
    #                 "messages": [AIMessage(preset_response)],
    #                 "task_id": state["task_id"],
    #                 "iteration_count": state["iteration_count"],
    #                 "history": state["history"],
    #                 "long_term_memory": state["long_term_memory"],
    #             }

    #     return {
    #         "messages": [],
    #         "task_id": state["task_id"],
    #         "iteration_count": state["iteration_count"],
    #         "history": state["history"],
    #         "long_term_memory": state["long_term_memory"],
    #     }

    def _long_term_memory_recall_node(self, state: AgentState) -> dict[str, Any]:
        """长期记忆召回节点"""
        long_term_memory = ""
        # 1.根据传递的智能体配置 判断是否需要找回长期记忆
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state["long_term_memory"]
            self.agent_queue_manager.publish(
                state["task_id"],
                AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.LONG_TERM_MEMORY_RECALL,
                    observation=long_term_memory,
                ),
            )

        # 2.构建预设消息列表，并将 preset_prompt + long_term_memory 填充到系统消息中
        preset_messages: list[AnyMessage] = [
            SystemMessage(
                AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                    preset_prompt=self.agent_config.preset_prompt,
                    long_term_memory=long_term_memory,
                    tool_description="",
                )
            )
        ]

        # 3.将短期历史消息添加到消息列表中
        history = state["history"]
        if isinstance(history, list) and len(history) > 0:
            # 4.校验历史消息是不是偶数的，也就是[人类消息, AI消息 ...]
            if len(history) % 2 != 0:
                # self.agent_queue_manager.publish_error(
                #     state["task_id"], "智能体历史消息列表格式错误"
                # )
                # logging.exception(
                #     "智能体历史消息列表格式错误, len(history)=%(len_history)d, history=%(history)s",
                #     {
                #         "len_history": len(history),
                #         "history": json.dumps(messages_to_dict(history)),
                #     },
                # )
                raise FailException("智能体历史消息列表格式错误")
            # 5.拼接历史消息
            preset_messages.extend(history)
        # 6.拼接当前用户的提问信息
        human_message = state["messages"][-1]
        # 消息进入state后会由langgraph的add_messages为其分配id，此处必然存在
        assert human_message.id is not None
        preset_messages.append(HumanMessage(human_message.content))

        return {
            # 7.处理预设消息，将预设消息添加到用户消息前，先去删除用户的原始消息，然后补充一个新的代替
            "messages": [RemoveMessage(id=human_message.id), *preset_messages],
            # "task_id": state["task_id"],
            # "iteration_count": state["iteration_count"],
            # "history": state["history"],
            # "long_term_memory": state["long_term_memory"],
        }

    def _llm_node(self, state: AgentState) -> dict[str, Any]:
        """大语言模型节点"""
        # 检测当前Agent迭代次数是否符合需求
        if state["iteration_count"] > self.agent_config.max_iteration_count:
            self.agent_queue_manager.publish(
                state["task_id"],
                AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_MESSAGE,
                    thought=MAX_ITERATION_RESPONSE,
                    message=messages_to_dict(state["messages"]),
                    answer=MAX_ITERATION_RESPONSE,
                    latency=0,
                ),
            )
            self.agent_queue_manager.publish(
                state["task_id"],
                AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_END,
                ),
            )
            return {
                "messages": [AIMessage(MAX_ITERATION_RESPONSE)],
                "task_id": state["task_id"],
                "iteration_count": state["iteration_count"],
                "history": state["history"],
                "long_term_memory": state["long_term_memory"],
            }

        # 1.从智能体配置中提取大语言模型
        llm = self.agent_config.llm

        # 2.检测大语言模型是否为聊天模型(支持bind_tools)，并且工具列表不为空时才绑定工具
        if isinstance(llm, BaseChatModel) and len(self.agent_config.tools) > 0:
            llm = llm.bind_tools(self.agent_config.tools)

        # 流式调用LLM输出对应内容
        gathered: AIMessageChunk | None = None
        event_id = uuid.uuid4()
        start_at = time.perf_counter()
        # generation_type = ""
        try:
            for raw_chunk in llm.stream(state["messages"]):
                chunk = cast(AIMessageChunk, raw_chunk)
                # 修复第三方api中转导致数据为None
                if chunk.usage_metadata is not None:
                    chunk.usage_metadata["input_tokens"] = (
                        0
                        if chunk.usage_metadata["input_tokens"] is None
                        else chunk.usage_metadata["input_tokens"]
                    )
                    chunk.usage_metadata["output_tokens"] = (
                        0
                        if chunk.usage_metadata["output_tokens"] is None
                        else chunk.usage_metadata["output_tokens"]
                    )
                    chunk.usage_metadata["total_tokens"] = (
                        0
                        if chunk.usage_metadata["total_tokens"] is None
                        else chunk.usage_metadata["total_tokens"]
                    )
                gathered = chunk if gathered is None else gathered + chunk

                if chunk.content:
                    content = (
                        chunk.content
                        if isinstance(chunk.content, str)
                        else json.dumps(chunk.content, ensure_ascii=False)
                    )
                    self.agent_queue_manager.publish(
                        state["task_id"],
                        AgentThought(
                            id=event_id,
                            task_id=state["task_id"],
                            event=QueueEvent.AGENT_MESSAGE,
                            thought=content,
                            answer=content,
                            latency=time.perf_counter() - start_at,
                        ),
                    )

                # # 检测生成类型是工具参数还是文本生成
                # if not generation_type:
                #     if chunk.tool_calls:
                #         generation_type = "thought"
                #     elif chunk.content:
                #         generation_type = "message"

                # # 如果生成的是消息则提交智能体消息事件
                # if generation_type == "message":
                #     # 提取片段内容并检测是否开启输出审核
                #     review_config = self.agent_config.review_config
                #     content = chunk.content
                #     if (
                #         review_config["enable"]
                #         and review_config["outputs_config"]["enable"]
                #     ):
                #         for keyword in review_config["keywords"]:
                #             content = re.sub(
                #                 re.escape(keyword), "**", content, flags=re.IGNORECASE
                #             )

                #     self.agent_queue_manager.publish(
                #         state["task_id"],
                #         AgentThought(
                #             id=id,
                #             task_id=state["task_id"],
                #             event=QueueEvent.AGENT_MESSAGE,
                #             thought=content,
                #             message=messages_to_dict(state["messages"]),
                #             answer=content,
                #             latency=(time.perf_counter() - start_at),
                #         ),
                #     )

        except Exception as e:
            logging.exception(
                "LLM节点发生错误, 错误信息: %(error)s",
                {"error": str(e) or "LLM出现未知错误"},
            )
            # self.agent_queue_manager.publish_error(
            #     state["task_id"], f"LLM节点发生错误, 错误信息: {str(e)}"
            # )
            raise e

        # # 计算输入、输出token数
        # input_token_count = self.llm.get_num_tokens_from_messages(state["messages"])
        # output_token_count = self.llm.get_num_tokens_from_messages([gathered])

        # # 获取输入/输出价格和单位
        # input_price, output_price, unit = self.llm.get_pricing()

        # # 计算总token+总成本
        # total_token_count = input_token_count + output_token_count
        # total_price = (
        #     input_token_count * input_price + output_token_count * output_price
        # ) * unit

        # # 如果类型为推理则添加智能体推理事件
        # if generation_type == "thought":
        #     self.agent_queue_manager.publish(
        #         state["task_id"],
        #         AgentThought(
        #             id=id,
        #             task_id=state["task_id"],
        #             event=QueueEvent.AGENT_THOUGHT,
        #             thought=json.dumps(gathered.tool_calls, ensure_ascii=False),
        #             message=messages_to_dict(state["messages"]),
        #             message_token_count=input_token_count,
        #             message_unit_price=input_price,
        #             message_price_unit=unit,
        #             answer="",
        #             answer_token_count=output_token_count,
        #             answer_unit_price=output_price,
        #             answer_price_unit=unit,
        #             total_token_count=total_token_count,
        #             total_price=total_price,
        #             latency=(time.perf_counter() - start_at),
        #         ),
        #     )
        # elif generation_type == "message":
        #     # 如果LLM直接生成answer则表示已经拿到了最终答案，推送一条空消息用于计算总token+总成本并停止监听
        #     self.agent_queue_manager.publish(
        #         state["task_id"],
        #         AgentThought(
        #             id=id,
        #             task_id=state["task_id"],
        #             event=QueueEvent.AGENT_MESSAGE,
        #             thought="",
        #             message=messages_to_dict(state["messages"]),
        #             message_token_count=input_token_count,
        #             message_unit_price=input_price,
        #             message_price_unit=unit,
        #             answer="",
        #             answer_token_count=output_token_count,
        #             answer_unit_price=output_price,
        #             answer_price_unit=unit,
        #             total_token_count=total_token_count,
        #             total_price=total_price,
        #             latency=(time.perf_counter() - start_at),
        #         ),
        #     )
        #     self.agent_queue_manager.publish(
        #         state["task_id"],
        #         AgentThought(
        #             id=uuid.uuid4(),
        #             task_id=state["task_id"],
        #             event=QueueEvent.AGENT_END,
        #         ),
        #     )

        # return {
        #     "messages": [gathered],
        #     "iteration_count": state["iteration_count"] + 1,
        #     "task_id": state["task_id"],
        #     "history": state["history"],
        #     "long_term_memory": state["long_term_memory"],
        # }

        assert gathered is not None
        if gathered.tool_calls:
            self.agent_queue_manager.publish(
                state["task_id"],
                AgentThought(
                    id=event_id,
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_THOUGHT,
                    thought=json.dumps(gathered.tool_calls, ensure_ascii=False),
                    latency=time.perf_counter() - start_at,
                ),
            )
        else:
            self.agent_queue_manager.publish(
                state["task_id"],
                AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_END,
                    latency=time.perf_counter() - start_at,
                ),
            )

        return {
            "messages": [gathered],
            "iteration_count": state["iteration_count"] + 1,
        }

    def _tools_node(self, state: AgentState) -> AgentState:
        """工具执行节点"""
        # 1.将工具列表转换成字典，便于调用指定的工具
        tools_by_name = {tool.name: tool for tool in self.agent_config.tools}

        # 2.提取消息中的工具调用参数
        last_message = state["messages"][-1]
        tool_calls = (
            last_message.tool_calls if isinstance(last_message, AIMessage) else []
        )

        # 3.循环执行工具组装工具消息
        messages = []
        for tool_call in tool_calls:
            try:
                # 获取工具并调用工具
                tool = tools_by_name[tool_call["name"]]
                try:
                    tool_result = tool.invoke(tool_call["args"])
                except NotImplementedError:
                    tool_result = asyncio.run(tool.ainvoke(tool_call["args"]))
            except Exception as e:
                # 添加错误工具信息
                tool_result = f"工具执行出错: {str(e)}"
                logging.exception("工具执行出错, 错误信息: %(error)s", {"error": str(e)})

            # 将工具消息添加到消息列表中
            messages.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=json.dumps(tool_result, ensure_ascii=False),
                    name=tool_call["name"],
                )
            )

            # 判断执行工具的名字，提交不同事件，涵盖智能体动作以及知识库检索
            event = (
                QueueEvent.AGENT_ACTION
                if tool_call["name"] != DATASET_RETRIEVAL_TOOL_NAME
                else QueueEvent.DATASET_RETRIEVAL
            )
            self.agent_queue_manager.publish(
                state["task_id"],
                AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=event,
                    observation=json.dumps(tool_result, ensure_ascii=False),
                    tool=tool_call["name"],
                    tool_input=tool_call["args"],
                    latency=0,
                ),
            )

        return {
            "messages": messages,
            "iteration_count": state["iteration_count"],
            "task_id": state["task_id"],
            "history": state["history"],
            "long_term_memory": state["long_term_memory"],
        }

    @classmethod
    def _tools_condition(cls, state: AgentState):
        """检测下一个节点是执行tools节点，还是直接结束"""
        messages = state["messages"]
        ai_message = messages[-1]

        # 检测是否存在tool_calls参数，如果存在则执行tools节点，否则结束
        if isinstance(ai_message, AIMessage) and len(ai_message.tool_calls) > 0:
            return "tools"
        return END

    # @classmethod
    # def _preset_operation_condition(
    #     cls, state: AgentState
    # ) -> Literal["long_term_memory_recall", "__end__"]:
    #     """预设操作条件边，用于判断是否触发预设响应"""
    #     # 提取状态的最后一条消息
    #     message = state["messages"][-1]

    #     # 判断消息的类型，如果是AI消息则说明触发了审核机制，直接结束
    #     if message.type == "ai":
    #         return END

    #     return "long_term_memory_recall"
