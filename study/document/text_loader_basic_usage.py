from pathlib import Path

from langchain_community.document_loaders import TextLoader

file_path = Path(__file__).with_name("e-commerce_data.txt")


# 1.构建加载器
loader = TextLoader(str(file_path), encoding="utf-8")
# 2.加载数据
docs = loader.load()

print(docs)
print(len(docs))  # 1
print(
    docs[0].metadata
)  # {'source': '/Users/luobin/project/llmops/llmops-api/study/document/e-commerce_data.txt'}
