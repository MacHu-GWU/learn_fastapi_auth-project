.. _Postgres-Database:

Postgres Database / 数据库
==============================================================================
*Neon Serverless Postgres + SQLAlchemy ORM*


数据库策略
------------------------------------------------------------------------------
.. list-table::
   :widths: 20 40 40
   :header-rows: 1

   * - 环境
     - 数据库
     - 原因
   * - 本地开发
     - SQLite
     - 零配置，快速启动
   * - dev/tst/prd
     - Neon Postgres
     - Serverless，自动扩缩容，Connection Pool

**为什么用 Neon？**

`Neon <https://neon.tech/>`_ 是 Serverless Postgres 服务，提供：

- **Connection Pooling**：自动管理连接池，不用担心连接数超限
- **按需计费**：空闲时自动暂停，节省成本
- **兼容 PostgreSQL**：标准 Postgres 协议，无厂商锁定


相关文件
------------------------------------------------------------------------------
.. code-block:: text

    learn_fastapi_auth/
    ├── database.py              # Base 类定义
    ├── models.py                # ORM 模型（User, Token 等）
    ├── config/config_01_db.py   # 数据库 URL 配置
    └── one/one_03_db.py         # Engine 和 Session 工厂


连接 URL 配置
------------------------------------------------------------------------------
:class:`~learn_fastapi_auth.config.config_01_db.DbMixin` 根据运行时环境返回不同的连接 URL：

- **本地**：``sqlite+aiosqlite:///data.db``
- **生产**：``postgresql+asyncpg://user:pass@host/db?ssl=require``

**为什么本地用 SQLite？**

本地开发只需快速启动和迭代，SQLite 零配置、无需网络连接。SQLAlchemy ORM 抽象了 SQL 差异，大部分业务逻辑可以在本地验证。


ORM 模型
------------------------------------------------------------------------------
所有模型定义在 :mod:`learn_fastapi_auth.models`，继承自 ``Base``：

- :class:`~learn_fastapi_auth.models.User`：用户账户（由 fastapi-users 管理）
- :class:`~learn_fastapi_auth.models.UserData`：用户数据（One-to-One）
- :class:`~learn_fastapi_auth.models.Token`：访问令牌（One-to-Many）
- :class:`~learn_fastapi_auth.models.RefreshToken`：刷新令牌（One-to-Many）

**设计原则**：模型类只定义数据结构和关系，**不放业务逻辑**。业务逻辑在其他模块中实现。


Engine 和 Session
------------------------------------------------------------------------------
:class:`~learn_fastapi_auth.one.one_03_db.OneDbMixin` 提供懒加载的数据库资源：

- ``one.async_engine``：异步引擎
- ``one.sync_engine``：同步引擎
- ``one.async_session_maker``：异步会话工厂
- ``one.create_db_and_tables()``：创建表结构


未来规划：Neon Branching
------------------------------------------------------------------------------
`Neon Branching <https://neon.tech/docs/introduction/branching>`_ 允许从生产数据库创建即时分支：

- **开发隔离**：每个功能分支可以有独立的数据库分支
- **测试数据**：分支包含生产数据快照，测试更真实
- **零成本**：分支使用 Copy-on-Write，几乎不占额外存储

目前未启用此功能，计划在项目规模增长后引入。
