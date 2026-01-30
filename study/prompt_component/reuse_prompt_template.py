from langchain_core.prompts import PromptTemplate

# 描述模板
instruction_prompt = PromptTemplate.from_template("你正在模拟{person}")

# 示例模板
example_prompt = PromptTemplate.from_template(
    """下面是一个交互例子，

Q: {example_q}
A: {example_a}"""
)

# 开始模板
start_prompt = PromptTemplate.from_template(
    """现在你是一个真实的人，请回答用户的问题：

Q: {input}
A:"""
)

# 1.x 版本写法: 使用 + 拼接模板
# 各个子模板会自动合并,变量也会自动合并
full_prompt = instruction_prompt + "\n\n" + example_prompt + "\n\n" + start_prompt

# 调用示例
result = full_prompt.invoke(
    {
        "person": "爱因斯坦",
        "example_q": "什么是相对论?",
        "example_a": "相对论是描述时空和引力的物理理论。",
        "input": "你最伟大的发现是什么?",
    }
)

print(result.to_string())
