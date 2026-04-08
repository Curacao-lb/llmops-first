from langchain_huggingface import HuggingFaceEmbeddings

# 拥有一个hugging Face 本地的文本嵌入模型
embeddings = HuggingFaceEmbeddings()

query_vector = embeddings.embed_query("你好，我是Robin，我喜欢打篮球游泳")

print(query_vector)
print(len(query_vector))  # 768
