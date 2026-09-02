from dataclasses import dataclass

import tiktoken
from injector import inject
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from redis import Redis


@inject
@dataclass
class EmbeddingsService:
    _store: RedisStore
    _embeddings: Embeddings
    _cache_backed_embeddings: CacheBackedEmbeddings

    def __init__(self, redis: Redis):
        self._store = RedisStore(client=redis)
        # self._embeddings = HuggingFaceEmbeddings(
        #     model_name="Alibaba-NLP/gte-multilingual-base",
        #     cache_folder=os.path.join(os.getcwd(), "internal", "core", "embeddings"),
        #     model_kwargs={
        #         "trust_remote_code": True,
        #     }
        # )
        self._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self._cache_backed_embeddings = CacheBackedEmbeddings.from_bytes_store(
            self._embeddings,
            self._store,
            namespace="embeddings",
        )

    @classmethod
    def calculate_token_count(cls, query: str) -> int:
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5")
            return len(encoding.encode(query))
        except Exception:
            # 兜底：当 tiktoken 词表缺失且无法联网下载时，退化为字符数近似估算，
            # 避免因 token 计数失败而阻塞索引 / 召回等流程。
            return len(query)

    @property
    def store(self) -> RedisStore:
        return self._store

    @property
    def embeddings(self) -> Embeddings:
        return self._embeddings

    @property
    def cache_backed_embeddings(self) -> CacheBackedEmbeddings:
        return self._cache_backed_embeddings
