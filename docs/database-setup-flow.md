# 数据库表创建流程详解

本文档详细说明了项目中数据库表的创建流程，帮助理解 Flask-SQLAlchemy + 依赖注入的完整架构。

---

## 📊 流程图

```
启动应用 (run.py)
    ↓
加载环境变量 (.env)
    ↓
创建配置对象 (Config)
    ↓
创建依赖注入容器 (Injector)
    ↓
配置 SQLAlchemy 绑定 (ExtensionModule)
    ↓
创建 Flask 应用 (Http)
    ↓
初始化数据库 (db.init_app)
    ↓
创建所有表 (db.create_all)
    ↓
应用启动成功
```

---

## 🔍 详细步骤解析

### 步骤 1: 定义数据库实例

**文件:** `internal/extension/database_extension.py`

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # 创建全局 db 实例,但还未绑定到 Flask 应用
```

**作用:** 创建一个全局的 SQLAlchemy 对象，供整个项目使用

**状态:** db 实例已创建，但还不知道要连接哪个数据库

---

### 步骤 2: 定义数据模型

**文件:** `internal/model/app.py`

```python
from internal.extension.database_extentsion import db
from sqlalchemy import Column, UUID, String, Text, DateTime

class App(db.Model):
    """AI应用基础模型类"""

    __tablename__ = "app"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_id"),
        Index("idx_app_account_id", "account_id"),
    )

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False)
    icon = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
```

**作用:** 定义数据表结构，继承 `db.Model`，SQLAlchemy 会根据这个类生成 SQL

**关键点:**

- `__tablename__`: 指定数据库表名
- `__table_args__`: 定义主键约束和索引
- 每个 `Column` 对应数据库的一列

---

### 步骤 3: 配置依赖注入模块

**文件:** `app/http/module.py`

```python
from flask_sqlalchemy import SQLAlchemy
from injector import Binder, Module
from internal.extension.database_extentsion import db

class ExtensionModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)  # 将 db 实例绑定到 SQLAlchemy 类型
```

**作用:** 告诉依赖注入容器："当有人需要 SQLAlchemy 类型时，给他 db 实例"

**依赖注入的好处:**

- 松耦合：不需要到处 import db
- 易测试：可以注入 mock 对象
- 统一管理：所有依赖关系在一处配置

---

### 步骤 4: 加载环境变量和配置

**文件:** `app/http/app.py`

```python
import dotenv
dotenv.load_dotenv()  # 加载 .env 文件

from config import Config
conf = Config()  # 创建配置对象,读取数据库连接字符串等
```

**文件:** `.env`

```bash
# 数据库连接 URI
SQLALCHEMY_DATABASE_URI=postgresql://root:123456@localhost:5432/llmops?client_encoding=utf8

# 连接池大小
SQLALCHEMY_POOL_SIZE=30

# 连接回收时间(秒)
SQLALCHEMY_POOL_RECYCLE=3600

# SQL 语句回显
SQLALCHEMY_ECHO=True
```

**文件:** `config/config.py`

```python
class Config:
    def __init__(self):
        self.SQLALCHEMY_DATABASE_URI = _get_env("SQLALCHEMY_DATABASE_URI")
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": int(_get_env("SQLALCHEMY_POOL_SIZE")),
            "pool_recycle": int(_get_env("SQLALCHEMY_POOL_RECYCLE")),
        }
        self.SQLALCHEMY_ECHO = _get_bool_env("SQLALCHEMY_ECHO")
```

**作用:** 从 `.env` 读取数据库连接信息，配置连接池等参数

---

### 步骤 5: 创建依赖注入容器

**文件:** `app/http/app.py`

```python
from injector import Injector
from .module import ExtensionModule

injector = Injector([ExtensionModule])  # 创建容器,加载配置
```

**作用:** 创建依赖注入容器，现在容器知道 `SQLAlchemy` → `db`

**容器的作用:**

- 管理所有依赖关系
- 自动创建和注入对象
- 避免手动 new 对象

---

### 步骤 6: 创建 Flask 应用并传入 db

**文件:** `app/http/app.py`

```python
app = Http(
    __name__,
    conf=conf,                        # 传入配置
    db=injector.get(SQLAlchemy),      # 从容器获取 db 实例
    router=injector.get(Router)       # 从容器获取路由
)
```

**作用:** 创建 Flask 应用，并将 db 实例传递给它

**关键点:**

- `injector.get(SQLAlchemy)` 会返回之前绑定的 `db` 实例
- 所有依赖都通过容器获取，不是手动创建

---

### 步骤 7: 初始化数据库扩展

**文件:** `internal/server/http.py`

```python
class Http(Flask):
    def __init__(self, *args, conf: "Config", db: SQLAlchemy, router: Router, **kwargs):
        # 1. 调用父类构造函数
        super(Http, self).__init__(*args, **kwargs)

        # 2. 加载配置到 Flask
        self.config.from_object(conf)

        # 3. 🔥 关键步骤: 将 db 绑定到当前 Flask 应用
        db.init_app(self)

        # 4. 🔥 创建所有表
        db.create_all()

        # 5. 注册异常处理器
        self.register_error_handler(Exception, self._register_error_handlers)

        # 6. 注册路由
        router.register_router(self)
```

**作用:**

- `db.init_app(self)`: 将 db 与 Flask 应用绑定，db 现在可以访问 Flask 的配置
- `db.create_all()`: 根据所有 `db.Model` 子类生成 SQL 并创建表

**db.init_app() 做了什么?**

1. 读取 Flask 配置中的数据库连接字符串
2. 创建数据库引擎 (Engine)
3. 配置连接池
4. 将 db 与 Flask 应用关联

**db.create_all() 做了什么?**

1. 扫描所有继承 `db.Model` 的类
2. 根据类定义生成 CREATE TABLE SQL
3. 检查表是否已存在
4. 如果不存在，执行 SQL 创建表和索引

---

### 步骤 8: 执行 SQL 创建表

当 `db.create_all()` 执行时，SQLAlchemy 自动生成并执行以下 SQL:

```sql
-- 1. 检查表是否存在
SELECT pg_catalog.pg_class.relname
FROM pg_catalog.pg_class
WHERE pg_catalog.pg_class.relname = 'app';

-- 2. 如果不存在,创建表
CREATE TABLE app (
    id UUID NOT NULL,
    account_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    icon VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    CONSTRAINT pk_app_id PRIMARY KEY (id)
);

-- 3. 创建索引
CREATE INDEX idx_app_account_id ON app (account_id);
```

**日志输出示例:**

```
2026-01-26 21:12:24,800 INFO sqlalchemy.engine.Engine select pg_catalog.version()
2026-01-26 21:12:24,802 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-01-26 21:12:24,804 INFO sqlalchemy.engine.Engine SELECT pg_catalog.pg_class.relname ...
2026-01-26 21:12:24,806 INFO sqlalchemy.engine.Engine CREATE TABLE app (...)
2026-01-26 21:12:24,829 INFO sqlalchemy.engine.Engine CREATE INDEX idx_app_account_id ...
2026-01-26 21:12:24,831 INFO sqlalchemy.engine.Engine COMMIT
```

---

## 📁 完整的文件调用链

```
run.py
  └─> app/http/app.py
       ├─> dotenv.load_dotenv()           # 加载 .env
       ├─> Config()                        # 读取配置
       │    └─> config/config.py
       │         └─> 读取环境变量
       │
       ├─> Injector([ExtensionModule])    # 创建容器
       │    └─> app/http/module.py
       │         └─> binder.bind(SQLAlchemy, to=db)
       │              └─> internal/extension/database_extension.py
       │                   └─> db = SQLAlchemy()
       │
       └─> Http(__name__, conf, db, router)
            └─> internal/server/http.py
                 ├─> self.config.from_object(conf)
                 ├─> db.init_app(self)      # 绑定 Flask 应用
                 └─> db.create_all()        # 创建表
                      └─> 扫描所有 db.Model 子类
                           └─> internal/model/app.py (App 类)
                                ├─> 生成 CREATE TABLE SQL
                                └─> 生成 CREATE INDEX SQL
```

---

## 📋 关键概念总结

| 步骤               | 文件                    | 作用                 | 关键方法               |
| ------------------ | ----------------------- | -------------------- | ---------------------- |
| 1. 创建 db 实例    | `database_extension.py` | 全局 SQLAlchemy 对象 | `SQLAlchemy()`         |
| 2. 定义模型        | `model/app.py`          | 定义表结构           | `class App(db.Model)`  |
| 3. 配置依赖注入    | `module.py`             | 绑定 db 到容器       | `binder.bind()`        |
| 4. 加载配置        | `app.py` + `.env`       | 读取数据库连接信息   | `dotenv.load_dotenv()` |
| 5. 创建容器        | `app.py`                | 管理依赖关系         | `Injector()`           |
| 6. 创建 Flask 应用 | `app.py`                | 传入 db 和配置       | `Http()`               |
| 7. 初始化 db       | `http.py`               | 绑定应用             | `db.init_app()`        |
| 8. 创建表          | `http.py`               | 执行 SQL             | `db.create_all()`      |

---

## 🎯 为什么要这样设计?

### 优点

✅ **松耦合**

- db 通过依赖注入传递，不是硬编码
- 各个模块职责清晰，互不依赖

✅ **易测试**

- 可以注入 mock 的 db 对象
- 单元测试不需要真实数据库

✅ **配置分离**

- 数据库配置在 `.env`，不写死在代码中
- 不同环境使用不同的 `.env` 文件

✅ **自动化**

- `db.create_all()` 自动根据模型创建表
- 不需要手写 SQL 脚本

✅ **可维护性**

- 修改表结构只需修改 Model 类
- 依赖关系一目了然

### 核心思想

1. **先定义"是什么"** (模型) → `model/app.py`
2. **再配置"怎么连"** (配置) → `.env` + `config.py`
3. **最后"创建表"** (自动化) → `db.create_all()`

---

## 🔧 常见问题

### Q1: 为什么要用依赖注入?

**A:** 避免到处 `from xxx import db`，统一管理依赖关系，方便测试和替换实现。

### Q2: db.init_app() 和 db.create_all() 的区别?

**A:**

- `db.init_app()`: 将 db 绑定到 Flask 应用，读取配置
- `db.create_all()`: 根据模型创建数据库表

### Q3: 如何添加新的数据表?

**A:**

1. 在 `internal/model/` 下创建新的模型类
2. 继承 `db.Model`
3. 定义字段和约束
4. 重启应用，`db.create_all()` 会自动创建新表

### Q4: 生产环境也用 db.create_all() 吗?

**A:** 不推荐。生产环境应该使用数据库迁移工具 (如 Alembic/Flask-Migrate)，可以版本控制和回滚。

---

## 📚 相关文档

- [Flask-SQLAlchemy 官方文档](https://flask-sqlalchemy.palletsprojects.com/)
- [SQLAlchemy 官方文档](https://www.sqlalchemy.org/)
- [Injector 依赖注入文档](https://injector.readthedocs.io/)

---

**最后更新:** 2026-01-26
