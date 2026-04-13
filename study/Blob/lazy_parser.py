from langchain_core.document_loaders.base import BaseBlobParser
from langchain_core.document_loaders import Blob
from langchain_core.documents import Document
from pathlib import Path


from typing import Iterator

file_path = Path(__file__).with_name("miaowu.txt")


class CustomParser(BaseBlobParser):
    """自定义解析器用于将传入的文本二进制数据的每一行解析成document组件。"""

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        line_number = 0
        with blob.as_bytes_io() as f:
            for line in f:
                yield Document(
                    page_content=line,
                    metadata={"source": blob.source, "line_number": line_number},
                )
                line_number += 1


# 1. 加载blob数据
blob = Blob.from_path(str(file_path))
parser = CustomParser()
# 2.解析得到文档数据
documnents = list(parser.lazy_parse(blob))

# 3.输出相应的信息
print(documnents)  # 每一行是个文档
print(len(documnents))  # 11
print(
    documnents[0].metadata
)  # {'source': '/Users/luobin/project/llmops/llmops-api/study/Blob/miaowu.txt', 'line_number': 0}
