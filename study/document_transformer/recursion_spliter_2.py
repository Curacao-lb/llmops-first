from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

from pathlib import Path

file_path = Path(__file__).with_name("recursion_spliter.py")

loader = UnstructuredFileLoader(str(file_path))

documents = loader.load()

# 创建可以分割Python代码的分割器
text_spliter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON, chunk_size=10, chunk_overlap=2, add_start_index=True
)

chunks = text_spliter.split_documents(documents=documents)


# for chunk in chunks:
#     print(f"块大小：{len(chunk.page_content)},元数据：{chunk.metadata}")

# print(len(chunks))  # 82

print(chunks[2].page_content)
