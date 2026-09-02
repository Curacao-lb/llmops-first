# tiktoken 离线缓存目录

本目录用于存放 tiktoken 的词表缓存文件，让服务器运行时**无需联网**即可完成
token 计数、长期记忆召回、消息截断等操作。

## 为什么需要它

tiktoken 首次使用某个编码时，会去
`openaipublic.blob.core.windows.net` 下载词表（如 `cl100k_base.tiktoken`）。
境内服务器常常无法访问该地址，导致请求报错：

```
HTTPSConnectionPool(host='openaipublic.blob.core.windows.net', port=443):
Max retries exceeded with url: /encodings/cl100k_base.tiktoken
```

## 如何生成缓存文件

在**能联网**的机器上执行（仓库根目录下）：

```bash
python scripts/download_tiktoken.py
```

脚本会把词表文件下载到本目录（文件名是词表 URL 的 sha1）。
之后把整个 `storage/tiktoken_cache/` 目录随仓库一起部署到服务器即可。

> 应用启动时（见 `pkg/tiktoken_cache.py`）会自动把环境变量
> `TIKTOKEN_CACHE_DIR` 指向本目录，无需手动配置。
> 若想使用其它目录，显式设置 `TIKTOKEN_CACHE_DIR` 环境变量即可覆盖。
