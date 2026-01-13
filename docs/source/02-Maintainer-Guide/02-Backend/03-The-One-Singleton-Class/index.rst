.. _The-One-Singleton-Class:

The One Singleton Class / One 单例类
==============================================================================
*集中式懒加载资源访问，模块化架构*


核心理念
------------------------------------------------------------------------------
``one`` 单例是应用程序所有共享资源的统一入口点。通过懒加载模式，资源只在真正需要时才初始化，避免循环依赖和不必要的启动开销。

.. code-block:: python

    from learn_fastapi_auth.one.api import one

    # 访问配置、数据库、AWS 服务等
    config = one.config
    engine = one.async_engine
    bsm = one.bsm


目录结构
------------------------------------------------------------------------------
.. code-block:: text

    learn_fastapi_auth/one/
    ├── one_00_main.py       # One 主类，组合所有 Mixin
    ├── one_01_bsm.py        # AWS Boto Session Manager
    ├── one_02_config.py     # 配置加载
    ├── one_03_db.py         # 数据库引擎和会话
    ├── one_04_webapp.py     # Firebase 初始化
    ├── one_05_devops.py     # DevOps 自动化
    ├── one_06_quick_links.py # 快速链接生成
    └── api.py               # 公共 API 导出


Mixin 模块化架构
------------------------------------------------------------------------------
每个 Mixin 负责一个功能域，使用 ``@cached_property`` 实现懒加载：

- :class:`~learn_fastapi_auth.one.one_01_bsm.OneBsmMixin`：AWS 会话管理
- :class:`~learn_fastapi_auth.one.one_02_config.OneConfigMixin`：配置加载
- :class:`~learn_fastapi_auth.one.one_03_db.OneDbMixin`：数据库引擎、会话工厂
- :class:`~learn_fastapi_auth.one.one_04_webapp.OneWebAppMixin`：Firebase 初始化
- :class:`~learn_fastapi_auth.one.one_05_devops.OneDevOpsMixin`：部署自动化
- :class:`~learn_fastapi_auth.one.one_06_quick_links.OneQuickLinksMixin`：文档链接

**为什么用 Mixin + 懒加载？**

- **避免循环依赖**：导入 ``one`` 不会触发任何资源初始化
- **按需加载**：只有访问 ``one.async_engine`` 时才创建数据库连接
- **模块独立**：每个 Mixin 可以独立开发和测试


测试友好的分层设计
------------------------------------------------------------------------------
这是本项目最重要的设计模式之一。架构分为三层，从上到下依次为：

1. **Router 层** (``routers/``)：HTTP 入口，调用 ``one.xxx()`` wrapper 函数
2. **One 层** (``one/``)：Wrapper 函数，负责绑定 singleton（engine, config 等）
3. **业务逻辑层** (其他模块)：纯函数 ``func(engine, session, ...args)``，不依赖 singleton

调用链路为 Router → One → 业务逻辑，每一层只依赖下一层。

**为什么这样分层？**

1. **底层函数易于测试**：``func(engine, session, user_id)`` 可以直接传入测试用的 engine/session，无需 mock
2. **One 层是简单的 wrapper**：只负责绑定 singleton，逻辑简单，维护成本低
3. **Router 层保持精简**：只处理 HTTP 请求/响应，业务逻辑在下层

**示例模式**：

.. code-block:: python

    # 底层模块：纯函数，易于测试
    # learn_fastapi_auth/auth/users.py
    async def get_user_by_id(session: AsyncSession, user_id: int) -> User:
        ...

    # One 层：wrapper，绑定 singleton
    # learn_fastapi_auth/one/one_xx_auth.py
    class OneAuthMixin:
        async def get_user(self, user_id: int) -> User:
            async with self.async_session_maker() as session:
                return await get_user_by_id(session, user_id)

    # Router 层：HTTP 处理
    # learn_fastapi_auth/routers/users.py
    @router.get("/users/{user_id}")
    async def get_user(user_id: int):
        return await one.get_user(user_id)


扩展新功能
------------------------------------------------------------------------------
添加新 Mixin 遵循命名规范 ``one_07_*.py``、``one_08_*.py``：

1. 创建新的 Mixin 类
2. 在 ``one_00_main.py`` 中添加到 ``One`` 类的继承列表
3. 使用 ``@cached_property`` 实现懒加载
