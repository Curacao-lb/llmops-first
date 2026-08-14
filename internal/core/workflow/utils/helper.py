from typing import Any, cast

from internal.core.workflow.entities.variable_entity import (
    VARIABLE_TYPE_DEFAULT_VALUE_MAP,
    VARIABLE_TYPE_MAP,
    VariableEntity,
    VariableValueType,
)
from internal.core.workflow.entities.workflow_entity import WorkflowState


def extract_variables_from_state(
    variables: list[VariableEntity], state: WorkflowState
) -> dict[str, Any]:
    """从状态中提取变量映射值信息"""
    # 构建变量字典信息
    variables_dict = {}

    # 循环遍历输入变量实体
    for variable in variables:
        # 获取数据变量类型
        variable_type_cls = VARIABLE_TYPE_MAP.get(variable.type, str)

        # 判断数据是引用还是直接输入
        if variable.value.type == VariableValueType.LITERAL:
            variables_dict[variable.name] = variable_type_cls(variable.value.content)
        else:
            # 引用or生成数据类型，遍历节点获取数据
            # 非字面量时content为Content对象，进行类型收窄
            content = cast(VariableEntity.Value.Content, variable.value.content)
            for node_result in state.get("node_results", []):
                if node_result.node_data.id == content.ref_node_id:
                    # 提取数据并完成数据强制转换
                    variables_dict[variable.name] = variable_type_cls(
                        node_result.outputs.get(
                            content.ref_var_name,
                            VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(variable.type),
                        )
                    )
    return variables_dict
