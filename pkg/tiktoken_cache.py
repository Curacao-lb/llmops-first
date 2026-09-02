"""tiktoken 离线缓存引导模块。

背景：
    tiktoken 首次使用某个编码（如 cl100k_base）时，会去
    openaipublic.blob.core.windows.net 下载词表文件。境内服务器
    经常无法访问该地址（SSL 握手被中断 / 超时），导致 token 计数、
    长期记忆召回、消息截断等环节抛异常，整个请求失败。

解决方案：
    把词表文件提前下载好放入仓库内固定目录，并通过环境变量
    ``TIKTOKEN_CACHE_DIR`` 让 tiktoken 直接读取本地缓存，运行时不再联网。

使用方式：
    在**任何** ``import tiktoken`` 之前先 ``import pkg.tiktoken_cache``（或调用
    ``pkg.tiktoken_cache.setup()``）。本模块在被导入时会自动完成配置。

    缓存文件通过 ``scripts/download_tiktoken.py`` 在能联网的机器上生成，
    然后随仓库一起部署到服务器即可。
"""

import os
from pathlib import Path

# 仓库内固定的缓存目录：<repo>/storage/tiktoken_cache
# 该文件位于 <repo>/pkg/tiktoken_cache.py，向上两级即仓库根目录。
CACHE_DIR = Path(__file__).resolve().parents[1] / "storage" / "tiktoken_cache"


def setup() -> str:
    """将 tiktoken 缓存目录指向仓库内的本地目录。

    - 若用户已显式设置 ``TIKTOKEN_CACHE_DIR``，则尊重其配置，不覆盖。
    - 否则指向仓库内的 ``storage/tiktoken_cache`` 并确保目录存在。

    返回最终生效的缓存目录路径。
    """
    existing = os.environ.get("TIKTOKEN_CACHE_DIR")
    if existing:
        return existing

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["TIKTOKEN_CACHE_DIR"] = str(CACHE_DIR)
    return str(CACHE_DIR)


# 导入即生效，保证在 tiktoken 被加载前完成配置。
setup()
