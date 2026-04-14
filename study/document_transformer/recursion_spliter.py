from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pathlib import Path

file_path = Path(__file__).with_name("test.md")


# 1.加载对应的文档
loader = UnstructuredMarkdownLoader(str(file_path))
documents = loader.load()

text_spliter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50, add_start_index=True
)

chunks = text_spliter.split_documents(documents=documents)

for chunk in chunks:
    print(f"块大小：{len(chunk.page_content)},元数据：{chunk.metadata}")

print(len(chunks))  # 111 分割为了111块
