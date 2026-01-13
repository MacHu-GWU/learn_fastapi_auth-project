.. _Environment-Runtime-Matrix:

Environment Runtime Matrix / 环境运行时矩阵
==============================================================================
*Runtime 和 Environment 的组合决定配置加载和资源访问策略*


核心概念
------------------------------------------------------------------------------
本项目需要在多种 **Runtime（运行时）** 和 **Environment（环境）** 的组合下运行。不同的组合需要不同的配置加载策略和资源访问方式。

**Runtime（运行时）** 指代码执行的物理环境：

- **local**：开发者本地电脑
- **ci**：GitHub Actions 等 CI/CD 流水线
- **app**：生产环境（本项目为 Vercel）

**Environment（环境）** 指逻辑部署环境：

- **dev**：开发环境
- **tst**：测试环境
- **prd**：生产环境

这两个维度组合成一个矩阵，每个单元格有不同的行为。


为什么需要矩阵
------------------------------------------------------------------------------
不同的 Runtime + Environment 组合需要不同的策略：

1. **配置来源不同**：本地开发从文件读配置，云端从 SSM Parameter Store 读配置
2. **数据库不同**：本地用 SQLite 快速迭代，云端用 Postgres 持久化
3. **AWS 凭证不同**：本地用 profile，Vercel 用环境变量注入的临时凭证

如果不统一管理，代码中会充满散落的 if-else 判断。


配置加载策略
------------------------------------------------------------------------------
根据 Runtime 的不同，配置从不同来源加载：

- **local + ***：从本地 ``config.json`` 和 ``secret-config.json`` 文件加载
- **vercel + ***：通过 ``ENV_NAME`` 环境变量确定环境，然后从 AWS SSM Parameter Store 读取


数据库策略
------------------------------------------------------------------------------
根据 Runtime + Environment 的不同，使用不同的数据库：

- **local + dev**：SQLite（本地文件，快速迭代）
- **vercel + dev**：Neon Postgres (dev 实例)
- **vercel + tst**：Neon Postgres (tst 实例)
- **vercel + prd**：Neon Postgres (prd 实例)


AWS 凭证策略
------------------------------------------------------------------------------
根据 Runtime 的不同，使用不同的 AWS 凭证获取方式：

- **local**：本地 ``~/.aws/credentials`` 中的 named profile
- **vercel**：Vercel 环境变量注入的 ``AWS_ACCESS_KEY_ID`` 等


源码参考
------------------------------------------------------------------------------
具体实现细节请参阅：

- :mod:`learn_fastapi_auth.runtime`：Runtime 检测逻辑
- :mod:`learn_fastapi_auth.env`：Environment 检测和枚举
- :mod:`learn_fastapi_auth.boto_ses`：AWS 凭证管理
