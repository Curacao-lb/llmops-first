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

# 5. 运行数据库迁移
# python -m internal.migration.migrate

# 6. 启动服务
# python -m app.http
```
