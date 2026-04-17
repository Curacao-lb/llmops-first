import os

import dotenv
import weaviate
from langchain_openai import OpenAIEmbeddings
from langchain_weaviate import WeaviateVectorStore
from weaviate.classes.init import AdditionalConfig, Auth, Timeout
from langchain_core.runnables import ConfigurableField

dotenv.load_dotenv()

weaviate_url = os.getenv(
    "WEAVIATE_URL",
    "palqsanrtjoc6uztz9a.c0.asia-southeast1.gcp.weaviate.cloud",
)
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

if not weaviate_api_key:
    raise ValueError("Missing WEAVIATE_API_KEY environment variable")

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    additional_config=AdditionalConfig(timeout=Timeout(init=30, query=60, insert=120)),
    skip_init_checks=True,
)

try:
    # 对于这种短查询，关闭长度预检查可避免 tiktoken 首次联网下载编码文件。
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        check_embedding_ctx_length=False,
    )

    # 1.构建向量数据库
    db = WeaviateVectorStore(
        client=client,
        index_name="DatasetDemo",
        text_key="text",
        embedding=embeddings,
    )

    # 2.转换检索器
    # retriever = db.as_retriever(
    #     search_type="similarity_score_threshold",
    #     search_kwargs={"k": 10, "score_threshold": 0.5},
    # )

    # 2.1尝试修改为使用MMR方法进行检索
    retriever = db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 10, "score_threshold": 0.5},
    ).configurable_fields(
        search_type=ConfigurableField(id="db_serarch_type"),
        search_kwargs=ConfigurableField(id="db_serarch_kwargs"),
    )

    # 3.执行基础相似性搜索
    # similarity_documents = retriever.invoke("肚肚在哪？")
    mmr_documents = retriever.with_config(
        configurable={
            "db_serarch_type": "mmr",
            "db_serarch_kwargs": {
                "k": 4,
            },
        }
    ).invoke("肚肚在哪？")
    print("相似性搜索:", mmr_documents)
    print("内容长度:", len(mmr_documents))
finally:
    client.close()
