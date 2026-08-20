from uuid import UUID

from pydantic import BaseModel

from internal.core.workflow.entities.node_entity import NodeType


class BaseEdgeData(BaseModel):
    """基础边数据"""

    id: UUID  # 边记录id
    source: UUID  # 边起点对应的节点id
    source_type: NodeType  # 边起点类型
    target: UUID  # 边目标对应的节点id
    target_type: NodeType  # 边目标类型
    # 起点句柄id，存在数据时则代表节点存在多个连接句柄(如意图识别/条件分支)
    source_handle_id: UUID | None = None
