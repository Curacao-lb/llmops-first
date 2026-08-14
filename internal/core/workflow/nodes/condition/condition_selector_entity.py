from pydantic import BaseModel, Field, field_validator

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity


class ClassConfig(BaseModel):
    """单个条件配置"""

    variable: str = Field(default="")  # 参与判断的变量名
    parameter: str = Field(default="")  # 判断的参数值
    condition_type: str = Field(default="")  # 条件判断类型


class ClassConfigGroup(BaseModel):
    """条件分组配置"""

    condition_group: list[ClassConfig] = Field(default_factory=list)
    logical_type: str = Field(default="")  # 组内逻辑关系(and/or)
    priority: int = Field(default=0)  # 优先级
    node_id: str = Field(default="")  # 该分类连接的节点id
    node_type: str = Field(default="")  # 该分类连接的节点类型
    source_handle_id: str = Field(default="")  # 起点句柄id


class ConditionSelectNodeData(BaseNodeData):
    """条件分支节点数据"""

    inputs: list[VariableEntity] = Field(default_factory=list)  # 输入变量信息
    outputs: list[VariableEntity] = Field(default_factory=lambda: [])
    classes: list[ClassConfigGroup] = Field(default_factory=list)

    @field_validator("outputs")
    def validate_outputs(cls, value: list[VariableEntity]):
        """重写覆盖outputs的输出，让其变成一个只读变量"""
        return []
