# Phase 1 代码变更详解

本文档面向只会 Python 但不熟悉 FastAPI 和 fastapi-users 的开发者，详细解释 Phase 1 实现的每一行关键代码。

---

## 目录

1. [整体架构概述](#1-整体架构概述)
2. [配置管理 (config.py)](#2-配置管理-configpy)
3. [数据库连接 (database.py)](#3-数据库连接-databasepy)
4. [数据模型 (models.py)](#4-数据模型-modelspy)
5. [请求/响应模式 (schemas.py)](#5-请求响应模式-schemaspy)
6. [用户认证核心 (auth/users.py)](#6-用户认证核心-authuserspy)
7. [邮件发送 (auth/email.py)](#7-邮件发送-authemailpy)
8. [主应用入口 (main.py)](#8-主应用入口-mainpy)
9. [单元测试 (tests/test_auth.py)](#9-单元测试-teststest_authpy)
10. [完整流程图解](#10-完整流程图解)

---

## 1. 整体架构概述

### 什么是 FastAPI？

FastAPI 是一个现代的 Python Web 框架，用于构建 API（应用程序接口）。想象一下：

- 你的手机 App 需要登录功能
- App 发送用户名密码到服务器
- 服务器验证后返回一个"通行证"（Token）
- App 拿着这个通行证访问其他功能

FastAPI 就是帮你快速搭建这个"服务器"的工具。

### 什么是 fastapi-users？

`fastapi-users` 是一个专门处理"用户认证"的库，它帮你实现：
- 用户注册（创建账号）
- 用户登录（验证身份）
- 邮箱验证（确认邮箱真实）
- 密码重置（忘记密码）

**关键概念**：你不需要自己写这些复杂的逻辑，`fastapi-users` 提供了"模板"，你只需要"填空"。

### 文件关系图

```
.env                    <- 敏感配置（密码、密钥）
    |
    v 读取
config.py               <- 配置类，集中管理所有设置
    |
    v 被导入
database.py             <- 数据库连接
    |
    v 被导入
models.py               <- 数据表定义（User, UserData, Token）
    |
    v 被导入
schemas.py              <- 请求/响应的数据格式
    |
    v 被导入
auth/users.py           <- fastapi-users 配置
auth/email.py           <- 邮件发送
    |
    v 被导入
main.py                 <- 应用入口，组装所有部件
```

---

## 2. 配置管理 (config.py)

### 为什么需要配置文件？

假设你的代码里直接写死了密码：
```python
password = "my_secret_123"  # 危险！提交到 GitHub 所有人都能看到
```

正确做法是把敏感信息放在 `.env` 文件中（不提交到 Git），然后用代码读取。

### 代码逐行解析

```python
# config.py

import os                    # Python 标准库，用于读取环境变量
import dataclasses           # Python 3.7+ 的数据类装饰器
from pathlib import Path     # 路径处理
from dotenv import load_dotenv  # 第三方库，读取 .env 文件
```

**知识点**：`dataclasses` 是什么？

普通的类需要你手写 `__init__`：
```python
class Config:
    def __init__(self, database_url, secret_key):
        self.database_url = database_url
        self.secret_key = secret_key
```

用 `@dataclasses.dataclass` 装饰器，Python 自动帮你生成：
```python
@dataclasses.dataclass
class Config:
    database_url: str   # 只需声明字段名和类型
    secret_key: str
    # __init__ 自动生成！
```

### Config 类详解

```python
@dataclasses.dataclass
class Config:
    """应用配置，从环境变量加载"""

    # 数据库连接字符串
    database_url: str = dataclasses.field()

    # JWT 密钥（用于生成和验证 Token）
    secret_key: str = dataclasses.field()

    # SMTP 邮件配置
    smtp_host: str = dataclasses.field()      # 邮件服务器地址
    smtp_port: int = dataclasses.field()      # 端口号
    smtp_tls: bool = dataclasses.field()      # 是否加密
    smtp_user: str = dataclasses.field()      # 发件人账号
    smtp_password: str = dataclasses.field()  # 发件人密码
    smtp_from: str = dataclasses.field()      # 发件人邮箱
    smtp_from_name: str = dataclasses.field() # 发件人显示名称

    # 应用配置
    frontend_url: str = dataclasses.field()              # 前端地址
    verification_token_lifetime: int = dataclasses.field()  # 验证链接有效期（秒）
    access_token_lifetime: int = dataclasses.field()        # 登录 Token 有效期（秒）
```

### from_env 方法详解

```python
@classmethod
def from_env(cls) -> "Config":
    """从环境变量加载配置"""

    # 找到 .env 文件的路径
    # __file__ 是当前文件的路径（config.py）
    # .parent 是上一级目录（learn_fastapi_auth/）
    # .parent 再上一级（项目根目录）
    env_path = Path(__file__).parent.parent / ".env"

    # 读取 .env 文件，把里面的变量加载到环境变量
    load_dotenv(env_path)

    # 创建 Config 实例
    return cls(
        # os.environ["KEY"] 读取环境变量，不存在则报错
        database_url=os.environ["DATABASE_URL"],
        secret_key=os.environ["SECRET_KEY"],

        # os.environ.get("KEY", "默认值") 读取环境变量，不存在则用默认值
        smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.environ.get("SMTP_PORT", "587")),

        # 字符串转布尔值
        smtp_tls=os.environ.get("SMTP_TLS", "True").lower() == "true",
        # ...
    )
```

**关键概念**：`@classmethod` 是什么？

普通方法需要先创建实例才能调用：
```python
config = Config(...)  # 先创建
config.some_method()  # 再调用
```

类方法可以直接通过类调用：
```python
config = Config.from_env()  # 直接调用，内部创建实例
```

### 单例模式

```python
config = Config.from_env()
"""全局唯一的配置实例"""
```

这行代码在模块被导入时执行，创建一个全局配置对象。之后所有文件 `from config import config` 都会得到同一个实例。

---

## 3. 数据库连接 (database.py)

### 什么是 ORM？

ORM（Object-Relational Mapping，对象关系映射）让你用 Python 类操作数据库，而不是写 SQL：

```python
# 不用 ORM（写 SQL）
cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", [email, pwd])

# 用 ORM（写 Python）
user = User(email=email, password=pwd)
session.add(user)
session.commit()
```

### 什么是异步（Async）？

假设你去餐厅点餐：
- **同步**：点完菜后一直站在柜台等，直到菜做好
- **异步**：点完菜拿个号，去座位上玩手机，菜好了叫你

在 Web 应用中：
- **同步**：处理请求 A 时，请求 B、C 必须排队等待
- **异步**：处理请求 A 等待数据库时，可以同时处理请求 B、C

### 代码逐行解析

```python
# database.py

from typing import AsyncGenerator  # 类型提示

# SQLAlchemy 的异步组件
from sqlalchemy.ext.asyncio import (
    AsyncSession,           # 异步数据库会话
    async_sessionmaker,     # 异步会话工厂
    create_async_engine,    # 创建异步数据库引擎
)
from sqlalchemy.orm import DeclarativeBase  # ORM 基类

from learn_fastapi_auth.config import config  # 导入配置
```

### 创建 Base 类

```python
class Base(DeclarativeBase):
    """所有数据模型的基类"""
    pass
```

**为什么需要 Base？**

所有数据表模型都要继承这个类，SQLAlchemy 通过它来：
1. 收集所有表的定义
2. 自动创建数据库表
3. 管理表之间的关系

### 创建数据库引擎

```python
# 创建异步数据库引擎
engine = create_async_engine(config.database_url, echo=False)
```

参数解释：
- `config.database_url`：数据库连接字符串，如 `sqlite+aiosqlite:///./data.db`
  - `sqlite`：使用 SQLite 数据库
  - `aiosqlite`：使用异步 SQLite 驱动
  - `./data.db`：数据库文件路径
- `echo=False`：不打印 SQL 语句（调试时可设为 True）

### 创建会话工厂

```python
# 创建异步会话工厂
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
```

**什么是会话（Session）？**

会话是你和数据库"对话"的通道：
```python
async with async_session_maker() as session:
    # 在这个 with 块里，你可以：
    # - 查询数据
    # - 添加数据
    # - 修改数据
    # - 删除数据
    pass
# 退出 with 块，会话自动关闭
```

`expire_on_commit=False`：提交后对象仍然可用（默认会"过期"需要重新查询）。

### 创建数据库表

```python
async def create_db_and_tables():
    """创建所有数据库表"""
    async with engine.begin() as conn:
        # Base.metadata.create_all 会创建所有继承 Base 的模型对应的表
        await conn.run_sync(Base.metadata.create_all)
```

**逐行解析**：
1. `async with engine.begin()`：开始一个数据库事务
2. `conn.run_sync(...)`：异步环境中运行同步函数（create_all 是同步的）
3. `Base.metadata.create_all`：根据所有模型定义创建表

### 依赖注入函数

```python
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖函数"""
    async with async_session_maker() as session:
        yield session
```

**什么是依赖注入？**

FastAPI 的"依赖注入"让你声明一个函数需要什么，框架自动提供：

```python
@app.get("/users")
async def get_users(session: AsyncSession = Depends(get_async_session)):
    # FastAPI 看到 Depends(get_async_session)
    # 自动调用 get_async_session() 获取 session
    # 并传递给这个函数
    pass
```

**为什么用 yield 而不是 return？**

```python
# 使用 yield 的好处：
async def get_async_session():
    async with async_session_maker() as session:
        yield session  # 把 session 交给调用者使用
    # 调用者用完后，代码继续执行到这里
    # async with 自动关闭 session
```

这确保了：
1. 函数执行时创建 session
2. 调用者使用 session
3. 调用者用完后自动清理

---

## 4. 数据模型 (models.py)

### 什么是数据模型？

数据模型定义了数据库表的结构，就像 Excel 表格的列定义：

| 列名 | 类型 | 说明 |
|------|------|------|
| id | UUID | 唯一标识 |
| email | 字符串 | 邮箱地址 |
| hashed_password | 字符串 | 加密后的密码 |

### 代码逐行解析

```python
# models.py

from datetime import datetime
from typing import Optional
import uuid

# fastapi-users 提供的用户表基类
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID

# SQLAlchemy 的字段类型
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learn_fastapi_auth.database import Base
```

### User 模型详解

```python
class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    用户模型，由 fastapi-users 管理

    继承自 SQLAlchemyBaseUserTableUUID，自动获得以下字段：
    - id: UUID 主键
    - email: 邮箱（唯一）
    - hashed_password: 密码哈希
    - is_active: 账户是否激活
    - is_superuser: 是否超级用户
    - is_verified: 邮箱是否验证
    """

    __tablename__ = "users"  # 数据库表名
```

**为什么继承两个类？**

```python
class User(SQLAlchemyBaseUserTableUUID, Base):
```

1. `SQLAlchemyBaseUserTableUUID`：提供用户认证需要的字段（email、password 等）
2. `Base`：让 SQLAlchemy 知道这是一个数据模型

**什么是 UUID？**

UUID（通用唯一标识符）是一个 36 位的字符串，如：
```
4fc02f23-224e-42d7-8eda-00ece2a63c78
```

优点：
- 全球唯一，不会重复
- 不暴露用户数量（不像自增 ID：1, 2, 3...）

### 字段定义详解

```python
# 额外添加的字段（fastapi-users 基类没有的）
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),      # 时间戳类型，带时区
    server_default=func.now()     # 默认值：数据库当前时间
)

updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    onupdate=func.now()           # 每次更新时自动更新时间
)
```

**Mapped[datetime] 是什么？**

这是 SQLAlchemy 2.0 的类型提示语法：
- `Mapped[datetime]`：告诉 Python 这个字段是 datetime 类型
- IDE 可以提供自动补全和类型检查

**server_default vs default**

```python
# server_default：数据库服务器生成默认值
server_default=func.now()  # INSERT 时数据库填入当前时间

# default：Python 代码生成默认值
default=datetime.now       # Python 代码执行时填入时间
```

推荐使用 `server_default`，因为时间由数据库统一管理，避免时区问题。

### 关系定义详解

```python
# 用户和用户数据的关系（一对一）
user_data: Mapped[Optional["UserData"]] = relationship(
    back_populates="user",           # 反向引用的属性名
    cascade="all, delete-orphan",    # 级联删除
    uselist=False                    # 一对一关系（不是列表）
)

# 用户和 Token 的关系（一对多）
tokens: Mapped[list["Token"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan"
    # uselist 默认为 True，即返回列表
)
```

**什么是关系（Relationship）？**

```python
# 有了关系定义，你可以这样访问关联数据：
user = await session.get(User, user_id)
print(user.user_data.text_value)  # 直接访问用户数据
print(user.tokens)                # 获取用户所有 Token
```

**cascade="all, delete-orphan" 是什么？**

级联操作：删除用户时，自动删除关联的 user_data 和 tokens。

### UserData 模型详解

```python
class UserData(Base):
    """用户专属数据存储，每个用户一条记录"""

    __tablename__ = "user_data"

    # user_id 既是主键，又是外键
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),  # 外键，关联 users 表
        primary_key=True                              # 主键
    )

    text_value: Mapped[str] = mapped_column(Text, default="")  # 用户的文本数据

    # ... created_at, updated_at 同上

    # 反向关系
    user: Mapped["User"] = relationship(back_populates="user_data")
```

**为什么 user_id 既是主键又是外键？**

这种设计确保：
1. 每个用户最多只有一条 UserData（主键唯一）
2. UserData 必须关联到一个存在的用户（外键约束）
3. 删除用户时自动删除 UserData（CASCADE）

### Token 模型详解

```python
class Token(Base):
    """JWT Token 存储，用于验证和撤销"""

    __tablename__ = "tokens"

    token: Mapped[str] = mapped_column(String(500), primary_key=True)  # Token 字符串
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(...)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # 过期时间

    user: Mapped["User"] = relationship(back_populates="tokens")
```

**为什么要存储 Token？**

JWT Token 本身是自包含的（包含用户 ID 和过期时间），但存储在数据库有额外好处：
1. 可以主动撤销（用户登出时删除）
2. 可以查询用户有多少活跃会话
3. 可以实现"踢出所有设备"功能

---

## 5. 请求/响应模式 (schemas.py)

### 什么是 Schema？

Schema（模式）定义了 API 请求和响应的数据格式：

```python
# 请求：用户注册时发送的数据
{"email": "test@example.com", "password": "123456"}

# 响应：服务器返回的数据
{"id": "xxx", "email": "test@example.com", "is_active": true}
```

Schema 确保：
1. 请求数据格式正确（缺少字段会报错）
2. 响应数据格式一致
3. 自动生成 API 文档

### 代码逐行解析

```python
# schemas.py

from datetime import datetime
from typing import Optional
import uuid

from fastapi_users import schemas  # fastapi-users 提供的基础 Schema
from pydantic import BaseModel, Field  # Pydantic 数据验证库
```

### 用户 Schema

```python
class UserRead(schemas.BaseUser[uuid.UUID]):
    """读取用户数据时返回的格式"""
    # 继承 BaseUser 获得：id, email, is_active, is_superuser, is_verified
    # 额外添加：
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserCreate(schemas.BaseUserCreate):
    """创建用户时提交的格式"""
    # 继承 BaseUserCreate 获得：email, password
    pass  # 不需要额外字段


class UserUpdate(schemas.BaseUserUpdate):
    """更新用户时提交的格式"""
    # 继承 BaseUserUpdate 获得：password, email, is_active, is_superuser, is_verified
    pass
```

**为什么 Read、Create、Update 分开？**

不同操作需要不同字段：
- **Create**：需要 email + password
- **Read**：返回 id, email, is_active 等（不返回密码！）
- **Update**：可选更新 email, password 等

### UserData Schema

```python
class UserDataRead(BaseModel):
    """读取用户数据"""
    user_id: uuid.UUID
    text_value: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}  # 允许从 ORM 对象创建
```

**model_config = {"from_attributes": True} 是什么？**

默认情况下，Pydantic 只能从字典创建对象：
```python
UserDataRead(**{"user_id": "...", "text_value": "..."})  # OK
UserDataRead.model_validate(orm_object)  # 报错！
```

设置 `from_attributes = True` 后，可以从 ORM 对象创建：
```python
user_data = await session.get(UserData, user_id)  # ORM 对象
return UserDataRead.model_validate(user_data)      # OK!
```

### UserDataUpdate Schema

```python
class UserDataUpdate(BaseModel):
    """更新用户数据"""
    text_value: str = Field(..., description="用户的文本内容")
```

**Field(...) 是什么？**

- `...` 表示这个字段是必填的
- `description` 会显示在 API 文档中

---

## 6. 用户认证核心 (auth/users.py)

这是整个认证系统最复杂的文件，让我们逐步拆解。

### 导入部分

```python
# auth/users.py

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,  # 认证后端
    BearerTransport,        # Bearer Token 传输方式
    JWTStrategy,            # JWT 策略
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learn_fastapi_auth.config import config
from learn_fastapi_auth.database import get_async_session
from learn_fastapi_auth.models import Token, User, UserData
```

### 获取用户数据库

```python
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """获取用户数据库实例"""
    yield SQLAlchemyUserDatabase(session, User)
```

`SQLAlchemyUserDatabase` 是 fastapi-users 提供的适配器，它知道如何：
- 查询用户
- 创建用户
- 更新用户
- 删除用户

### UserManager 详解

```python
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """
    用户管理器，包含自定义的注册和验证逻辑
    """

    # 用于生成密码重置 Token 的密钥
    reset_password_token_secret = config.secret_key
    # 用于生成邮箱验证 Token 的密钥
    verification_token_secret = config.secret_key
```

**什么是 UserManager？**

UserManager 是 fastapi-users 的核心组件，负责：
- 处理用户注册
- 处理用户登录
- 处理密码重置
- 处理邮箱验证

**UUIDIDMixin 是什么？**

告诉 fastapi-users 我们使用 UUID 作为用户 ID（而不是整数）。

### 生命周期钩子

```python
async def on_after_register(
    self, user: User, request: Optional[Request] = None
) -> None:
    """用户注册成功后调用"""
    print(f"User {user.id} has registered.")
    # 自动发送验证邮件
    await self.request_verify(user, request)
```

**流程**：
1. 用户提交注册表单
2. fastapi-users 创建用户记录
3. 自动调用 `on_after_register`
4. 我们在这里发送验证邮件

```python
async def on_after_request_verify(
    self, user: User, token: str, request: Optional[Request] = None
) -> None:
    """请求邮箱验证后调用"""
    from learn_fastapi_auth.auth.email import send_verification_email

    await send_verification_email(user.email, token)
    print(f"Verification requested for user {user.id}. Token: {token}")
```

**流程**：
1. `on_after_register` 调用 `self.request_verify`
2. fastapi-users 生成验证 Token
3. 调用 `on_after_request_verify`
4. 我们在这里发送邮件

```python
async def on_after_verify(
    self, user: User, request: Optional[Request] = None
) -> None:
    """用户验证邮箱后调用"""
    print(f"User {user.id} has been verified.")

    # 为验证后的用户创建 UserData 记录
    session: AsyncSession = self.user_db.session

    # 检查是否已存在
    result = await session.execute(
        select(UserData).where(UserData.user_id == user.id)
    )
    existing_data = result.scalar_one_or_none()

    if not existing_data:
        user_data = UserData(user_id=user.id, text_value="")
        session.add(user_data)
        await session.commit()
        print(f"Created UserData for user {user.id}")
```

**流程**：
1. 用户点击验证链接
2. fastapi-users 验证 Token，更新 `is_verified = True`
3. 调用 `on_after_verify`
4. 我们在这里创建用户的数据记录

### 认证后端配置

```python
# 传输方式：Bearer Token
bearer_transport = BearerTransport(tokenUrl="api/auth/login")
```

Bearer Token 是最常见的 API 认证方式：
```
GET /api/user-data HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```python
def get_jwt_strategy() -> JWTStrategy:
    """获取 JWT 策略"""
    return JWTStrategy(
        secret=config.secret_key,              # 签名密钥
        lifetime_seconds=config.access_token_lifetime,  # Token 有效期
    )
```

**什么是 JWT？**

JWT（JSON Web Token）是一种自包含的 Token 格式：
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.      # 头部（算法）
eyJzdWIiOiI0ZmMwMmYyMyIsImV4cCI6MTc2NTE1Mjc3MH0.  # 载荷（用户ID、过期时间）
uURc4hU6Ivqav3O5g_7i4ArpYOLcIdm8UYcun48HLzE       # 签名（防篡改）
```

服务器可以通过签名验证 Token 是否被篡改，无需查询数据库。

```python
# 组合传输方式和策略，创建认证后端
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
```

### FastAPIUsers 实例

```python
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
```

这个实例提供了预构建的路由器，只需一行代码就能添加注册、登录等功能。

### 当前用户依赖

```python
# 获取当前登录的活跃用户
current_active_user = fastapi_users.current_user(active=True)

# 获取当前登录且已验证邮箱的用户
current_verified_user = fastapi_users.current_user(active=True, verified=True)
```

使用方式：
```python
@app.get("/api/user-data")
async def get_user_data(user: User = Depends(current_verified_user)):
    # 如果用户未登录或未验证邮箱，FastAPI 自动返回 401/403 错误
    # 只有通过验证的用户才能执行到这里
    return {"user_id": user.id}
```

---

## 7. 邮件发送 (auth/email.py)

### 邮件发送原理

发送邮件需要通过 SMTP（简单邮件传输协议）服务器：

```
你的应用 --> Gmail SMTP 服务器 --> 收件人邮箱
```

### 代码逐行解析

```python
# auth/email.py

import ssl                        # 安全连接
from email.mime.multipart import MIMEMultipart  # 多部分邮件
from email.mime.text import MIMEText            # 文本内容

import aiosmtplib                 # 异步 SMTP 客户端

from learn_fastapi_auth.config import config
```

### 生成邮件内容

```python
def get_verification_email_html(verification_url: str) -> str:
    """生成 HTML 格式的验证邮件"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <style>
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h2>验证您的邮箱地址</h2>
    <p>请点击下方按钮验证您的邮箱地址：</p>
    <a href="{verification_url}" class="button">验证邮箱</a>
    <p>此链接将在 15 分钟后过期。</p>
</body>
</html>"""
```

**为什么用 `{{` 和 `}}`？**

在 f-string 中，`{变量}` 会被替换。如果你想显示字面量的 `{`，需要写成 `{{`：
```python
f"CSS: .button {{ color: red; }}"  # 输出：CSS: .button { color: red; }
```

### 发送邮件

```python
async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str,
) -> bool:
    """发送邮件"""

    # 创建多部分邮件（同时包含纯文本和 HTML）
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{config.smtp_from_name} <{config.smtp_from}>"
    message["To"] = to_email

    # 添加纯文本部分（给不支持 HTML 的邮件客户端）
    part1 = MIMEText(text_content, "plain", "utf-8")
    # 添加 HTML 部分
    part2 = MIMEText(html_content, "html", "utf-8")
    message.attach(part1)
    message.attach(part2)

    try:
        # 创建 SSL 上下文（加密连接）
        context = ssl.create_default_context()

        # 发送邮件
        await aiosmtplib.send(
            message,
            hostname=config.smtp_host,      # smtp.gmail.com
            port=config.smtp_port,          # 587
            username=config.smtp_user,      # 你的 Gmail
            password=config.smtp_password,  # Gmail 应用专用密码
            start_tls=config.smtp_tls,      # 启用 TLS 加密
            tls_context=context,
        )
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False
```

**为什么用 aiosmtplib 而不是 smtplib？**

- `smtplib`：Python 标准库，同步发送
- `aiosmtplib`：异步发送，不阻塞其他请求

### 发送验证邮件

```python
async def send_verification_email(email: str, token: str) -> bool:
    """发送验证邮件"""

    # 构造验证链接
    verification_url = f"{config.frontend_url}/auth/verify-email?token={token}"

    return await send_email(
        to_email=email,
        subject="验证您的邮箱地址",
        html_content=get_verification_email_html(verification_url),
        text_content=get_verification_email_text(verification_url),
    )
```

---

## 8. 主应用入口 (main.py)

### 应用生命周期

```python
# main.py

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    await create_db_and_tables()  # 创建数据库表
    yield
    # 关闭时执行（这里没有清理逻辑）
```

**什么是 asynccontextmanager？**

它让你定义"启动前"和"关闭后"的逻辑：
```python
@asynccontextmanager
async def lifespan(app):
    print("应用启动前")
    yield
    print("应用关闭后")
```

### 创建 FastAPI 应用

```python
app = FastAPI(
    title="FastAPI User Authentication",
    description="A SaaS authentication service with email verification",
    version="1.0.0",
    lifespan=lifespan,  # 绑定生命周期管理器
)
```

### 注册 fastapi-users 路由

```python
# 注册路由
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/auth",  # 路由前缀
    tags=["auth"],       # API 文档分组
)
```

这一行代码添加了 `POST /api/auth/register` 端点！

**fastapi_users.get_register_router 做了什么？**

内部大致是：
```python
def get_register_router(UserRead, UserCreate):
    router = APIRouter()

    @router.post("/register", response_model=UserRead)
    async def register(user_create: UserCreate):
        # 1. 验证邮箱格式
        # 2. 检查邮箱是否已存在
        # 3. 哈希密码
        # 4. 创建用户记录
        # 5. 调用 on_after_register
        # 6. 返回用户信息
        pass

    return router
```

你不需要自己写这些代码，fastapi-users 全部帮你实现好了！

### 自定义路由

```python
@app.get("/api/user-data", response_model=UserDataRead, tags=["user-data"])
async def get_user_data(
    user: User = Depends(current_verified_user),  # 依赖注入：获取当前用户
    session: AsyncSession = Depends(get_async_session),  # 依赖注入：获取数据库会话
):
    """获取当前用户的数据"""

    # 查询用户数据
    result = await session.execute(
        select(UserData).where(UserData.user_id == user.id)
    )
    user_data = result.scalar_one_or_none()

    if not user_data:
        # 如果不存在，创建一条空记录
        user_data = UserData(user_id=user.id, text_value="")
        session.add(user_data)
        await session.commit()
        await session.refresh(user_data)

    return user_data  # FastAPI 自动转换为 JSON
```

**Depends() 的魔法**

```python
user: User = Depends(current_verified_user)
```

这一行做了很多事：
1. 从请求头获取 `Authorization: Bearer <token>`
2. 验证 Token 签名
3. 检查 Token 是否过期
4. 从数据库获取用户
5. 检查用户是否激活且已验证邮箱
6. 如果任何步骤失败，返回 401/403 错误
7. 成功则把 User 对象传给函数

### 运行入口

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

`uvicorn` 是 ASGI 服务器，负责：
- 监听 8000 端口
- 接收 HTTP 请求
- 调用 FastAPI 应用处理
- 返回响应

---

## 9. 单元测试 (tests/test_auth.py)

### 测试设置

```python
# tests/test_auth.py

# 使用内存数据库进行测试（不影响真实数据）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
```

**什么是 Fixture？**

Fixture 是 pytest 的"准备工作"机制：
```python
@pytest.fixture
def database():
    # 测试前：创建数据库
    db = create_database()
    yield db
    # 测试后：清理数据库
    db.drop()
```

### 依赖注入覆盖

```python
@pytest_asyncio.fixture
async def client(test_engine):
    """创建测试客户端"""
    from main import app

    # 创建测试用的会话工厂
    async_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_async_session():
        async with async_session_maker() as session:
            yield session

    # 关键：用测试会话替换真实会话
    app.dependency_overrides[get_async_session] = override_get_async_session

    # 创建测试客户端
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    # 清理
    app.dependency_overrides.clear()
```

**dependency_overrides 是什么？**

它让你在测试时替换依赖：
```python
# 生产环境：使用真实数据库
app.dependency_overrides = {}

# 测试环境：使用内存数据库
app.dependency_overrides[get_async_session] = override_get_async_session
```

### 测试用例示例

```python
class TestUserRegistration:
    """测试用户注册"""

    @patch("learn_fastapi_auth.auth.users.UserManager.on_after_request_verify")
    async def test_register_user_success(
        self, mock_verify: AsyncMock, client: AsyncClient
    ):
        """测试成功注册"""
        # Mock 邮件发送（测试时不真的发邮件）
        mock_verify.return_value = None

        # 发送注册请求
        user_data = {
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPass123!",
        }
        response = await client.post("/api/auth/register", json=user_data)

        # 验证响应
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert data["is_active"] is True
        assert data["is_verified"] is False
```

**@patch 是什么？**

Mock（模拟）让你替换真实的函数调用：
```python
@patch("module.send_email")  # 替换 send_email 函数
def test_something(mock_send_email):
    mock_send_email.return_value = True  # 假装发送成功
    # 测试代码...
    # 实际不会发送邮件
```

---

## 10. 完整流程图解

### 用户注册流程

```
用户                    FastAPI                   数据库               邮件服务器
  |                        |                         |                      |
  |  POST /api/auth/register                         |                      |
  |  {email, password}     |                         |                      |
  |----------------------->|                         |                      |
  |                        |                         |                      |
  |                        |  验证邮箱格式            |                      |
  |                        |  检查邮箱是否已存在       |                      |
  |                        |------------------------>|                      |
  |                        |       查询结果           |                      |
  |                        |<------------------------|                      |
  |                        |                         |                      |
  |                        |  哈希密码                |                      |
  |                        |  创建用户记录            |                      |
  |                        |------------------------>|                      |
  |                        |        OK               |                      |
  |                        |<------------------------|                      |
  |                        |                         |                      |
  |                        |  on_after_register()    |                      |
  |                        |  生成验证 Token          |                      |
  |                        |  on_after_request_verify()                     |
  |                        |------------------------------------------------>|
  |                        |                         |      发送验证邮件     |
  |                        |                         |                      |
  |  返回用户信息          |                         |                      |
  |  {id, email, is_verified: false}                 |                      |
  |<-----------------------|                         |                      |
```

### 用户登录流程

```
用户                    FastAPI                   数据库
  |                        |                         |
  |  POST /api/auth/login  |                         |
  |  {username, password}  |                         |
  |----------------------->|                         |
  |                        |                         |
  |                        |  查询用户                |
  |                        |------------------------>|
  |                        |       用户记录           |
  |                        |<------------------------|
  |                        |                         |
  |                        |  验证密码哈希            |
  |                        |  检查 is_active          |
  |                        |  生成 JWT Token          |
  |                        |                         |
  |  返回 Token            |                         |
  |  {access_token, token_type: "bearer"}            |
  |<-----------------------|                         |
```

### 访问受保护资源流程

```
用户                    FastAPI                   数据库
  |                        |                         |
  |  GET /api/user-data    |                         |
  |  Authorization: Bearer <token>                   |
  |----------------------->|                         |
  |                        |                         |
  |                        |  验证 JWT 签名           |
  |                        |  检查 Token 过期时间      |
  |                        |  从 Token 获取 user_id   |
  |                        |                         |
  |                        |  查询用户                |
  |                        |------------------------>|
  |                        |       用户记录           |
  |                        |<------------------------|
  |                        |                         |
  |                        |  检查 is_active          |
  |                        |  检查 is_verified        |
  |                        |                         |
  |                        |  查询 UserData           |
  |                        |------------------------>|
  |                        |       用户数据           |
  |                        |<------------------------|
  |                        |                         |
  |  返回用户数据          |                         |
  |  {user_id, text_value, ...}                      |
  |<-----------------------|                         |
```

---

## 总结

通过这份文档，你应该理解了：

1. **配置管理**：用 `.env` 文件存储敏感信息，用 `dataclass` 创建配置类
2. **数据库连接**：用 SQLAlchemy 异步引擎连接数据库
3. **数据模型**：用 ORM 定义数据表结构和关系
4. **Schema**：用 Pydantic 定义 API 请求/响应格式
5. **认证核心**：用 fastapi-users 处理注册、登录、验证
6. **邮件发送**：用 aiosmtplib 异步发送邮件
7. **主应用**：用 FastAPI 组装所有组件
8. **单元测试**：用 pytest 测试 API 功能

核心思想：**不要重复造轮子**。fastapi-users 已经实现了复杂的认证逻辑，我们只需要：
1. 定义自己的数据模型
2. 配置 fastapi-users
3. 添加自定义的业务逻辑（如发送验证邮件、创建 UserData）

---

**文档版本**: v1.0
**最后更新**: 2024-12-07
**作者**: Claude Code Assistant
