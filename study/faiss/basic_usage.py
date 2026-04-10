import os
import dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Fix OpenMP library conflict on macOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

dotenv.load_dotenv()

embedding = OpenAIEmbeddings(model="text-embedding-3-small")

metadatas: list = [
    {"page": 1},
    {"page": 2},
    {"page": 3},
    {"page": 4},
    {"page": 5},
    {"page": 6},
    {"page": 7},
    {"page": 8},
    {"page": 9},
    {"page": 10},
]

db = FAISS.from_texts(
    [
        "肚肚是一只很喜欢睡觉的猫咪",
        "我喜欢在夜晚听音乐,这让我感到放松,",
        "猫咪在窗台上打盹,看起来非常可爱,",
        "学习新技能是每个人都应该追求的日标。",
        "我最喜欢的食物是意大利面,尤其是番茄酱的那种。",
        "昨晚我做了一个奇怪的梦,梦见自己在太空飞行,",
        "我的手机突然关机了,让我有些焦虑,",
        "阅读是我每天都会做的事情,我觉得很充实,",
        "他们一起计划了一次周末的野餐,希望天气能好,",
        "我的狗喜欢追逐球,看起来非常开心。",
    ],
    embedding,
    metadatas=metadatas,
    relevance_score_fn=lambda x: 1.0 / (1.0 + x),
)


# print(db.index.ntotal)  # 10
# 即返回了10条数据

# print(db.similarity_search_with_score("我养了一只猫，叫肚肚"))
# print(db.similarity_search_with_relevance_scores("我养了一只猫，叫肚肚"))
# 在相似性搜索的时候传递filter参数
# print(
#     db.similarity_search_with_relevance_scores(
#         "我养了一只猫，叫肚肚", filter=lambda x: x["page"] > 5
#     )
# )  # 找到的数据的page都大于5

# print(db.index_to_docstore_id)  # 打印每一项的唯一值

print("删除前数量:", db.index.ntotal)
# 获取向量数据库的索引id列表信息
db.delete([db.index_to_docstore_id[0]])
print("删除后数量:", db.index.ntotal)

# 删除前数量: 10
# 删除后数量: 9
