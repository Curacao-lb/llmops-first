from langchain_core.prompts import PromptTemplate

# 通过魔术方法，让类和方法和字符串进行拼接
# 通过重写__add__方法
prompt = (
    PromptTemplate.from_template("请讲一个{subject}的冷笑话")
    + "让我开心"
    + "\n使用{language}语言"
)


"""
input_variables=['language', 'subject'] input_types={} partial_variables={} template='请讲一个{subject}的冷笑话让我开心\n使用{language}语言'
"""
print(prompt)

"""
  请讲一个程序员的冷笑话让我开心
  使用中文语言
"""
print(prompt.invoke({"subject": "程序员", "language": "中文"}).to_string())
