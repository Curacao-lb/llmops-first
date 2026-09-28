# LLMOps API

大语言模型运维平台 API 服务

## 项目目录结构

```
llmops-api/
├── app/                    # 应用入口集合
│   └── http/               # HTTP 应用（创建 HTTP 服务）
│
├── config/                 # 应用配置文件
│                           # 包含：数据库连接、缓存连接、大模型 API 配置等
│
├── internal/               # 内部模块目录
│   ├── core/               # 大语言模型核心文件（LangChain 集成、文本嵌入等）
│   ├── exception/          # 通用公共异常
│   ├── extension/          # 框架扩展（授权、数据库扩展等）
│   ├── handler/            # 控制器，接收路由请求并处理
│   ├── middleware/         # 中间件（登录状态校验等）
│   ├── migration/          # 数据库迁移工具（将模型映射到实际数据库表）
│   ├── model/              # 数据库表对应的 ORM 模型类
│   ├── router/             # 路由定义，将请求映射到对应控制器
│   ├── schema/             # 请求/响应数据结构体定义
│   ├── schedule/           # 调度任务/定时任务
│   ├── server/             # 服务器配置（与 app 对应，支持多应用构建）
│   ├── service/            # 业务逻辑层
│   └── task/               # 延时任务/异步任务
│
├── pkg/                    # 扩展包/工具包目录
│
├── storage/                # 存储目录
│   ├── logs/               # 日志文件
│   └── uploads/            # 用户上传文件
│
├── test/                   # 测试代码
│
├── venv/                   # Python 虚拟环境
│
├── .env                    # 环境配置文件（避免硬编码敏感信息）
├── .gitignore              # Git 忽略配置
├── requirements.txt        # Python 第三方依赖
└── README.md               # 项目说明文档
```

## 目录说明

| 目录/文件   | 说明                                               |
| ----------- | -------------------------------------------------- |
| `app/`      | 应用入口，不同类型的应用（HTTP、CLI 等）在此初始化 |
| `config/`   | 集中管理所有配置项，支持多环境配置                 |
| `internal/` | 项目内部代码，不对外暴露                           |
| `pkg/`      | 可复用的工具包，可被其他项目引用                   |
| `storage/`  | 运行时产生的文件（日志、上传文件等）               |
| `test/`     | 单元测试、集成测试代码                             |

## 快速开始

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 生成 requirements.txt（只包含项目实际导入的包）
pipreqs . --force

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入实际配置

# 5. 运行数据库迁移（具体命令见下方「数据库迁移」）

# 6. 启动服务
# python -m app.http
```

## Docker Compose

首次部署时复制 `docker/.env.example` 为 `docker/.env`，设置数据库、Redis 和 JWT 密钥，并按需填写外部服务密钥。账号注册和找回密码还需要项目根目录中的 `private.pem`，并在 `docker/.env` 的 `PRIVATE_KEY_PASSWORD` 中填写该密钥的口令；Compose 会只读挂载私钥到 API 容器。SMTP 用于验证码邮件。PostgreSQL 密码会进入连接 URI，建议用 `openssl rand -hex 32` 生成 URL 安全密码。

### 本地 Demo 邮件

Compose 会自动启动 Mailpit，接收验证码邮件但不会向真实邮箱投递，因此不需要注册邮件服务或配置真实的 SMTP 账号。启动服务后访问 <http://localhost:8025> 查看验证码。默认 SMTP 地址为 `mailpit:1025`，仅在 Docker Compose 内部使用；网页界面只绑定本机回环地址。

如果需要让邮件真正到达用户邮箱，再配置外部 SMTP 服务。Outlook.com 需要 OAuth2；本项目提供 `scripts/configure_outlook_oauth.py` 授权脚本，详细方式见脚本注释和微软的 [SMTP OAuth 文档](https://learn.microsoft.com/en-us/exchange/client-developer/legacy-protocols/how-to-authenticate-an-imap-pop-smtp-application-by-using-oauth)。真实邮箱 SMTP 常见使用 STARTTLS，465 端口通常使用 SMTPS。

从仓库根目录构建并启动全部服务：

```bash
docker compose --env-file docker/.env -f docker/docker-compose.yaml up --build -d
```

API 运行数据库迁移，Celery worker 负责消费异步任务。PostgreSQL 和 Redis 数据保存在 `docker/volumes/`，Weaviate 使用命名卷。

## 数据库迁移

在项目根目录执行。`.flaskenv` 已配置应用入口，激活虚拟环境后可以直接使用 `flask db` 命令。

```bash
# 使用当前项目的虚拟环境（macOS/Linux）
source ../.venv/bin/activate
```

### 新增或修改 Model 后

先确保新模型已在 `internal/model/__init__.py` 中导入，否则迁移工具无法识别它：

```python
from .user import User
```

然后依次执行：

```bash
# 1. 根据模型变更生成迁移文件（不会修改数据库）
flask db migrate -m "add user table"

# 2. 查看 internal/migration/versions/ 下刚生成的文件，确认变更内容

# 3. 将迁移应用到数据库
flask db upgrade
```

`migrate` 与 `upgrade` 适用于新增模型、添加字段、修改字段等所有模型结构变更；只需将说明改成符合本次变更的描述。

### 常用检查命令

```bash
# 查看数据库当前已应用的迁移版本
flask db current

# 查看全部迁移历史
flask db history
```

> 仓库已有迁移目录，日常开发不需要执行 `flask db init`。
