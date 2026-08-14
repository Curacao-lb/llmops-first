import time

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes.base_node import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state

from .end_entity import EndNodeData


class EndNode(BaseNode):
    """结束节点"""

    node_data: EndNodeData

    def invoke(
        self, state: WorkflowState, config: RunnableConfig | None = None
    ) -> WorkflowState:
        """结束节点执行函数，提取需要输出的变量并作为工作流最终输出"""
        # 提取数据
        start_at = time.perf_counter()
        outputs_dict = extract_variables_from_state(self.node_data.outputs, state)

        # 组装状态并返回
        return {
            "outputs": outputs_dict,
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs={},
                    outputs=outputs_dict,
                    latency=(time.perf_counter() - start_at),
                )
            ],
        }
