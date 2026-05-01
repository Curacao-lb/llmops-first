from langchain_core.tools import tool


@tool
def multiply(a: int, b: int) -> int:
    """传递的两个值相乘"""
    return a * b


# 打印下该工具的相关信息
print("名称:", multiply.name)  # 名称: multiply
print("描述:", multiply.description)  # 描述: 传递的两个值相乘
print(
    "参数:", multiply.args
)  # 参数: {'a': {'title': 'A', 'type': 'integer'}, 'b': {'title': 'B', 'type': 'integer'}}
print("直接返回:", multiply.return_direct)  # 直接返回: False

# 调用工具
print(multiply.invoke({"a": 2, "b": 8}))  # 16
