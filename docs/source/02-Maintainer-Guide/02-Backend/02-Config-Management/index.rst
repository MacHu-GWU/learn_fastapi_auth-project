.. _Config-Management:

Config Management / 配置管理
==============================================================================
*集中式配置管理，提升开发效率的基石*


核心理念
------------------------------------------------------------------------------
**当你需要修改任何配置值时，你永远不需要在源代码中搜索。所有修改都发生在集中式配置系统中。**

这解决了一个常见痛点：开发者需要在复杂代码库中寻找硬编码值。通过集中管理，无论某个参数在代码中被引用多少次，修改点永远只有一个。


目录结构
------------------------------------------------------------------------------
.. code-block:: text

    config/
    ├── config.json              # 非敏感配置（进 Git）
    └── secret-config.json       # 敏感配置（不进 Git）

    learn_fastapi_auth/
    ├── config/                  # 配置定义
    │   ├── config_00_main.py    # Config, Env 主类
    │   ├── config_01_db.py      # DbMixin
    │   └── config_02_webapp.py  # WebAppMixin
    └── one/
        └── one_02_config.py     # 配置加载 (Singleton)

    tests/config/
        └── test_config.py       # 单元测试


配置数据格式
------------------------------------------------------------------------------
JSON 文件采用 ``_defaults`` + 环境覆盖的结构：

.. code-block:: javascript

    {
        "_defaults": {
            "*.project_name": "learn_fastapi_auth"
            // 所有环境共享
        },
        "dev": { /* 开发环境特定值 */ },
        "tst": { /* 测试环境特定值 */ },
        "prd": { /* 生产环境特定值 */ }
    }

**为什么分离 config.json 和 secret-config.json？**

- ``config.json``：可以进入版本控制，方便团队协作和代码审查
- ``secret-config.json``：包含密码、密钥等敏感信息，必须排除在 Git 之外


Mixin 模式
------------------------------------------------------------------------------
配置定义使用 Mixin 模式组织，每个 Mixin 负责一个功能域：

- :class:`~learn_fastapi_auth.config.config_01_db.DbMixin`：数据库连接 URL
- :class:`~learn_fastapi_auth.config.config_02_webapp.WebAppMixin`：前端 URL、Firebase 集成

**为什么用 Mixin？**

随着项目增长，配置字段会越来越多。Mixin 模式让我们按功能域拆分配置逻辑，保持每个模块的关注点单一，易于维护。


运行时感知加载
------------------------------------------------------------------------------
:class:`~learn_fastapi_auth.one.one_02_config.OneConfigMixin` 根据运行时环境自动选择加载策略：

- **本地开发**：从本地 JSON 文件加载
- **CI/CD**：本地 config.json + SSM Parameter Store 敏感配置
- **生产环境**：完全从 SSM Parameter Store 加载

**为什么这样设计？**

本地开发需要快速迭代，直接读文件最方便。生产环境需要安全性，敏感配置应存储在 AWS SSM Parameter Store 中，支持加密和访问控制。


多环境支持
------------------------------------------------------------------------------
项目支持四种环境：``devops``、``dev``、``tst``、``prd``。

环境检测由 ``which_env`` 库自动完成，详见 :mod:`learn_fastapi_auth.env`。


使用方式
------------------------------------------------------------------------------
.. code-block:: python

    from learn_fastapi_auth.one.api import one

    env = one.env              # 当前环境配置
    url = env.async_db_url     # 访问计算属性


依赖库
------------------------------------------------------------------------------
基于 `aws_config <https://github.com/MacHu-GWU/aws_config-project>`_ 构建，提供环境覆盖、SSM 集成等能力。
