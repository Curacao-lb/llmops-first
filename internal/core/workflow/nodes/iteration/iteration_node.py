import json
import time
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes.base_node import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state

from .iteration_entity import IterationNodeData


class IterationNode(BaseNode):
    """迭代节点

    注意：本项目暂未实现工作流持久化(internal.model.Workflow)，因此迭代节点
    暂不支持加载并调用已发布的子工作流，self.workflow 恒为 None。待补充工作流
    数据模型后，可在此按 workflow_ids 加载子工作流并循环调用。
    """

    node_data: IterationNodeData
    workflow: Any = None

    def invoke(
        self, state: WorkflowState, config: Optional[RunnableConfig] = None
    ) -> WorkflowState:
        """迭代节点调用函数，循环遍历将子工作流的结果进行输出"""
        # 提取节点输入变量字典映射
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)
        inputs = inputs_dict.get("inputs", [])

        # 异常检测，涵盖子工作流不存在、工作流输入参数不唯一、数据为非列表、长度为0等
        if (
            self.workflow is None
            or len(getattr(self.workflow, "args", {})) != 1
            or not isinstance(inputs, list)
            or len(inputs) == 0
        ):
            return {
                "node_results": [
                    NodeResult(
                        node_data=self.node_data,
                        status=NodeStatus.FAILED,
                        inputs=inputs_dict,
                        outputs={"outputs": []},
                        latency=(time.perf_counter() - start_at),
                    )
                ]
            }

        # 获取子工作流的输入字段结构
        param_key = list(self.workflow.args.keys())[0]

        # 循环遍历输入数据调用迭代子工作流获取结果
        outputs = []
        for item in inputs:
            data = {param_key: item}
            iteration_result = self.workflow.invoke(data)
            outputs.append(json.dumps(iteration_result, ensure_ascii=False))

        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs={"outputs": outputs},
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
