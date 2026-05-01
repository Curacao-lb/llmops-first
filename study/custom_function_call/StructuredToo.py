from langchain_core.tools import StructuredTool


def multiply(a: int, b: int) -> int:
    """传递的两个值相乘"""
    return a * b


async def amultiply(a: int, b: int) -> int:
    """传递的两个值相乘"""
    return a * b


calculator = StructuredTool.from_function(
    func=multiply,
    coroutine=amultiply,
    name="multiply_tool",
    description="传递的两个值相乘",
    return_direct=True,
)

print("名称:", calculator.name)  # 名称: multiply_tool
print("描述:", calculator.description)  # 描述: 传递的两个值相乘
print(
    "参数:", calculator.args
)  # 参数: {'a': {'title': 'A', 'type': 'integer'}, 'b': {'title': 'B', 'type': 'integer'}}
print("直接返回:", calculator.return_direct)  # 直接返回: True

# 调用工具
print(calculator.invoke({"a": 2, "b": 8}))  # 16
