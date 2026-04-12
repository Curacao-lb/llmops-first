from pathlib import Path

from langchain_community.document_loaders import UnstructuredMarkdownLoader

file_path = Path(__file__).with_name("test.md")


# 1.构建加载器
loader = UnstructuredMarkdownLoader(str(file_path))
# 2.加载数据
docs = loader.load()

print(docs)
print(len(docs))  # 1
print(
    docs[0].metadata
)  # {'source': '/Users/luobin/project/llmops/llmops-api/study/document/test.md'}
