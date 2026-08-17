import json
import logging
import os
import time

import requests
from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.variable_entity import (
    VARIABLE_TYPE_DEFAULT_VALUE_MAP,
)
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes.base_node import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from internal.exception import FailException

from .code_entity import CodeNodeData


class CodeNode(BaseNode):
    """Python代码运行节点"""

    node_data: CodeNodeData

    def invoke(
        self, state: WorkflowState, config: RunnableConfig | None = None
    ) -> WorkflowState:
        """Python代码运行节点，执行的代码函数名必须为main，并且参数名为params"""
        # 从状态中提取输入数据
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 通过云函数服务执行代码
        data = {
            "code": self.node_data.code,
            "func_name": "main",
            "args": [inputs_dict],
        }
        function_call_url = os.getenv("FUNCTION_CALL_URL")
        if not function_call_url:
            raise FailException("未配置云函数调用地址FUNCTION_CALL_URL")
        response = requests.post(url=function_call_url, json=data)

        if response.status_code != 200:
            logging.error("云函数返回异常: %(reason)s", {"reason": response.reason})
            raise FailException("云函数返回异常")

        result = json.loads(response.text)["result"]

        # 检测函数的返回值是否为字典
        if not isinstance(result, dict):
            logging.error(
                "main函数的返回值必须是一个字典: %(result)s", {"result": result}
            )
            raise FailException("main函数的返回值必须是一个字典")

        # 提取输出数据(非严格校验)
        outputs_dict = {}
        for output in self.node_data.outputs:
            outputs_dict[output.name] = result.get(
                output.name,
                VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(output.type),
            )

        # 构建状态数据并返回
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs_dict,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
