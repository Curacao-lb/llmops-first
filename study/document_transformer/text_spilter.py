from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import CharacterTextSplitter

from pathlib import Path

file_path = Path(__file__).with_name("test.md")


# 1.加载对应的文档
loader = UnstructuredMarkdownLoader(str(file_path))
documents = loader.load()
print(documents)
print(len(documents))
# 2.创建文本分割器
text_spliter = CharacterTextSplitter(separator="\n\n", chunk_size=500, chunk_overlap=50)
# 3.分割文本
chunks = text_spliter.split_documents(documents)

for chunk in chunks:
    print(f"块大小：{len(chunk.page_content)}")

print(len(chunks))  # 86，也就是被拆分为了86块
