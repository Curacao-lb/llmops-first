import time

from jinja2 import Template
from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes.base_node import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state

from .llm_entity import LLMNodeData


class LLMNode(BaseNode):
    """大语言模型节点"""

    node_data: LLMNodeData

    def invoke(
        self, state: WorkflowState, config: RunnableConfig | None = None
    ) -> WorkflowState:
        """大语言模型节点执行函数，根据输入变量渲染提示词并调用LLM生成结果"""
        # 提取节点中的输入数据
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 使用jinja2格式化模板信息
        template = Template(self.node_data.prompt)
        prompt_value = template.render(**inputs_dict)

        # 通过依赖注入加载大语言模型实例
        from app.http.module import injector
        from internal.service import AgentService

        agent_service = injector.get(AgentService)
        llm = agent_service.load_language_model(self.node_data.language_model_config)

        # 使用stream来代替invoke，避免接口长时间未响应超时
        content = ""
        for chunk in llm.stream(prompt_value):
            # 修复第三方api中转导致usage数据为None
            if chunk.usage_metadata is not None:
                chunk.usage_metadata["input_tokens"] = (
                    chunk.usage_metadata["input_tokens"] or 0
                )
                chunk.usage_metadata["output_tokens"] = (
                    chunk.usage_metadata["output_tokens"] or 0
                )
                chunk.usage_metadata["total_tokens"] = (
                    chunk.usage_metadata["total_tokens"] or 0
                )
            content += str(chunk.content)

        # 提取并构建输出数据结构
        outputs = {}
        if self.node_data.outputs:
            outputs[self.node_data.outputs[0].name] = content
        else:
            outputs["output"] = content

        # 构建响应状态并返回
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
