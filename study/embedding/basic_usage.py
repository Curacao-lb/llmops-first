import dotenv
from langchain_openai import OpenAIEmbeddings
import numpy

dotenv.load_dotenv()

# 1.创建文本嵌入模型
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 2.嵌入文本
query_vector = embeddings.embed_query("我叫Robin，我喜欢打篮球")

# print(query_vector)
# print(len(query_vector)) # 1536

# 3.嵌入文档列表/字符串列表
documents_vector = embeddings.embed_documents(
    ["我叫Robin，我喜欢打篮球", "这个喜欢打篮球的人叫Robin", "求知若渴，虚心若愚"]
)

print(len(documents_vector))  # 3


# 计算相似度
def cos_similarity(vec1: list, vec2: list) -> float:
    """计算传入两个向量的余弦相似度"""
    # 1. 计算两个向量的点积
    dot_product = numpy.dot(vec1, vec2)

    # 2. 计算两个向量的长度
    vec1_length = numpy.linalg.norm(vec1)
    vec2_length = numpy.linalg.norm(vec2)

    # 3.计算余弦相似度
    return dot_product / (vec1_length * vec2_length)


# 计算余弦相似度
print(
    "向量1和向量2的相似度：", cos_similarity(documents_vector[0], documents_vector[1])
)  # 向量1和向量2的相似度： 0.8646846062415526

print(
    "向量1和向量3的相似度：", cos_similarity(documents_vector[0], documents_vector[2])
)  # 向量1和向量3的相似度： 0.0868669237226309
