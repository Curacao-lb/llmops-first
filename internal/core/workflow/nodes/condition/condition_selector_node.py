from typing import Any, Optional

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.variable_entity import ConditionType
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes.base_node import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state

from .condition_selector_entity import ClassConfig, ConditionSelectNodeData


def _evaluate_condition(actual: Any, condition_type: str, parameter: str) -> bool:
    """根据条件类型对实际值与参数进行判断，返回是否匹配"""
    # 处理为空/不为空判断
    if condition_type == ConditionType.EMPTY.value:
        return actual is None or actual == ""
    if condition_type == ConditionType.NOT_EMPTY.value:
        return actual is not None and actual != ""

    # 处理字符串前缀/后缀判断
    if condition_type == ConditionType.STARTS_WITH.value:
        return str(actual).startswith(parameter)
    if condition_type == ConditionType.ENDS_WITH.value:
        return str(actual).endswith(parameter)

    # 处理包含/不包含判断
    if condition_type == ConditionType.IN.value:
        return parameter in str(actual)
    if condition_type == ConditionType.NOT_IN.value:
        return parameter not in str(actual)

    # 处理比较判断，优先尝试数值比较，失败则退回字符串比较
    left: Any = actual
    right: Any = parameter
    try:
        left = float(actual)
        right = float(parameter)
    except (TypeError, ValueError):
        left = str(actual)
        right = str(parameter)

    if condition_type == ConditionType.EQ.value:
        return left == right
    if condition_type == ConditionType.NE.value:
        return left != right
    if condition_type == ConditionType.GT.value:
        return left > right
    if condition_type == ConditionType.GE.value:
        return left >= right
    if condition_type == ConditionType.LT.value:
        return left < right
    if condition_type == ConditionType.LE.value:
        return left <= right

    return False


class ConditionSelectorNode(BaseNode):
    """条件分支节点"""

    node_data: ConditionSelectNodeData

    def _match_condition(self, condition: ClassConfig, inputs_dict: dict) -> bool:
        """判断单个条件是否匹配"""
        actual = inputs_dict.get(condition.variable)
        return _evaluate_condition(
            actual, condition.condition_type, condition.parameter
        )

    def invoke(
        self, state: WorkflowState, config: Optional[RunnableConfig] = None
    ) -> str:
        """条件分支节点执行函数，根据条件命中情况返回对应的起点句柄标识"""
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 按照优先级排序
        self.node_data.classes.sort(key=lambda x: x.priority)

        node_flag = None
        # 最后一个分类作为默认(else)分支，只判断前面的分类组
        for class_config_group in self.node_data.classes[:-1]:
            condition_group = class_config_group.condition_group
            if not condition_group:
                continue

            results = [
                self._match_condition(condition, inputs_dict)
                for condition in condition_group
            ]

            # 根据逻辑类型合并判断结果，默认使用and
            if class_config_group.logical_type == "or":
                matched = any(results)
            else:
                matched = all(results)

            if matched:
                node_flag = class_config_group.source_handle_id
                break

        if node_flag is not None:
            return f"cn_source_handle_{node_flag}"

        # 未命中任何条件，返回默认(最后一个)分支
        return f"cn_source_handle_{self.node_data.classes[-1].source_handle_id}"
