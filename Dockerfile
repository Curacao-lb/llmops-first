# 构建阶段：与本地虚拟环境统一使用 Python 3.13.5
FROM python:3.13.5-slim-bookworm AS builder

# 默认使用官方 PyPI；国内构建时可通过 --build-arg PIP_INDEX_URL=... 覆盖
ARG PIP_INDEX_URL=https://pypi.org/simple

# 将requirements.txt拷贝到根目录下
COPY requirements.txt .

# 仅在构建阶段安装编译工具，用于 crcmod 等源码包
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# 构建缓存并使用pip安装严格版本的requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/pkg --retries 10 --timeout 120 --resume-retries 10 -r requirements.txt

# 二阶段生产环境构建
FROM python:3.13.5-slim-bookworm AS production

# 生产镜像只安装文档解析需要的运行时依赖，不包含编译工具。
# 使用发行版仓库安装，避免依赖仓库中不存在的架构专用 .deb 文件。
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 pandoc \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app/api

# 定义环境变量
ENV FLASK_APP=app/http/app.py
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV NLTK_DATA=/app/api/internal/core/unstructured/nltk_data
ENV HF_ENDPOINT=https://hf-mirror.com

# 设置容器时区为中国标准时间，避免时区错误
ENV TZ=Asia/Shanghai

# 拷贝第三方依赖包+源码文件
COPY --from=builder /pkg /usr/local
COPY . /app/api

# 拷贝运行脚本并设置权限
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 暴露5001端口
EXPOSE 5001

# 运行脚本并启动项目
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
