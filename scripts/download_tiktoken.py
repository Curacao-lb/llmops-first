#!/usr/bin/env python
"""在能联网的机器上预先下载 tiktoken 词表，生成离线缓存文件。

用途：
    境内服务器运行时常常无法访问 openaipublic.blob.core.windows.net，
    导致 tiktoken 首次加载词表失败。本脚本在能联网的环境下把项目所需的
    词表提前下载到 ``storage/tiktoken_cache/``，随仓库部署到服务器后，
    运行时即可离线加载（见 ``pkg/tiktoken_cache.py``）。

使用：
    # 在仓库根目录、能联网的机器上执行
    python scripts/download_tiktoken.py

    # 如需通过代理下载
    HTTPS_PROXY=http://your-proxy:port python scripts/download_tiktoken.py

说明：
    本项目的模型（gpt-3.5 / gpt-3.5-turbo 及各兼容模型）统一使用
    cl100k_base 词表，因此默认只下载它。如需其它词表，追加到
    ENCODINGS 列表即可。
"""

import os
import sys
from pathlib import Path

# 保证能 import 到项目内的 pkg 包
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# 先设置缓存目录，再导入 tiktoken，确保下载写入本地目录
from pkg import tiktoken_cache  # noqa: E402  (import 副作用：设置 TIKTOKEN_CACHE_DIR)

import tiktoken  # noqa: E402

# 本项目实际用到的编码
ENCODINGS = ["cl100k_base"]


def main() -> int:
    cache_dir = os.environ["TIKTOKEN_CACHE_DIR"]
    print(f"缓存目录: {cache_dir}")

    for name in ENCODINGS:
        print(f"正在下载词表: {name} ...")
        enc = tiktoken.get_encoding(name)
        # 触发一次编码，确认词表可用
        _ = enc.encode("hello world")
        print(f"  ✓ {name} 就绪")

    files = sorted(p.name for p in tiktoken_cache.CACHE_DIR.glob("*") if p.is_file())
    print("\n已生成缓存文件:")
    for f in files:
        print(f"  - {f}")
    print(
        "\n完成。请把整个 storage/tiktoken_cache/ 目录随仓库部署到服务器，"
        "运行时将自动离线加载。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
