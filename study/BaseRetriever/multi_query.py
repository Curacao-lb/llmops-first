import os

import dotenv
import weaviate
from langchain_classic.retrievers import MultiQueryRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_weaviate import WeaviateVectorStore
from weaviate.classes.init import AdditionalConfig, Auth, Timeout

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

    # 2.先构建一个基础检索器，MultiQueryRetriever 会在它外面再包一层
    base_retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 4},
    )

    # 3.MultiQueryRetriever 需要一个 LLM 来生成多个查询变体
    llm = ChatOpenAI(
        model="gpt-3.5-turbo-16k",
        temperature=0,
    )

    # 4.创建多查询检索器
    multi_query_retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
        include_original=True,
    )

    # 4.执行多查询检索
    documents = multi_query_retriever.invoke("肚肚在哪？")
    print("MultiQuery 搜索:", documents)
    """
    MultiQuery 搜索: [Document(metadata={'page': 1.0}, page_content='肚肚是一只很喜欢睡觉的猫咪'), Document(metadata={'page': 5.0}, page_content='我最喜欢的食物是意大利面,尤其是番茄酱的那种。'), Document(metadata={'page': 9.0}, page_content='他们一起计划了一次周末的野餐,希望天气能好,'), Document(metadata={'page': 6.0}, page_content='昨晚我做了一个奇怪的梦,梦见自己在太空飞行,'), Document(metadata={'page': 4.0}, page_content='学习新技能是每个人都应该追求的日标。')]
    """
    print("内容长度:", len(documents))  # 5
finally:
    client.close()
