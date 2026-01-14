# FastAPI Users 项目概览与维护模式说明

## 项目背景

### 项目简介

FastAPI Users 是一个为 FastAPI 框架提供即用型, 可定制化的用户管理解决方案的 Python 库. 该项目由 Fran ç ois Voron (GitHub: @frankie567) 创建和维护, 旨在解决在 FastAPI 项目中实现用户注册, 登录, 认证等功能的痛点.

**核心特性:**
- 可扩展的基础用户模型
- 开箱即用的注册, 登录, 密码重置和邮箱验证路由
- 社交 OAuth2 登录流程支持
- 依赖注入式的当前用户获取
- 可插拔的密码验证
- 多种数据库后端支持:SQLAlchemy, MongoDB (motor), Tortoise ORM, Beanie 等
- 多种认证后端:JWT, Cookie 等
- 完整的 OpenAPI schema 支持

### 项目历史里程碑

- **2019 年**: 项目首次提交, 最初只是一个简单的用户认证解决方案
- **2021 年**: 项目在社区中获得广泛关注和使用
- **2023 年 7 月**: v12.1.0 版本引入 Pydantic V2 支持, 保持与 V1 的向后兼容性
- **2024 年 3 月**: v13.0.0 版本, 将默认密码哈希算法从 bcrypt 改为 Argon2, 提升安全性
- **2024 年 11 月**: v14.0.0 版本, 放弃 Python 3.8 支持
- **2025 年 10 月 25 日**: v15.0.0 版本发布, 正式进入维护模式, 放弃 Python 3.9 和 Pydantic v1 支持

### 项目影响力

- **GitHub Stars**: 5,900+
- **每月下载量**: 32,797+ (PyPI 统计)
- **开源许可**: MIT License
- **社区贡献者**: 10+ 核心贡献者, 数百位社区贡献者
- **生产环境使用**: 被广泛应用于各类 FastAPI 项目的用户认证系统

## 维护模式决定

### 官方公告时间

**2025 年 10 月 25 日**,FastAPI Users 团队在 GitHub Discussions [#1543](https://github.com/fastapi-users/fastapi-users/discussions/1543) 中正式宣布项目进入维护模式.

### 什么是维护模式?

在维护模式下, 项目将遵循以下原则:

**✅ 将继续提供的支持:**
- 安全更新 (Security updates)
- 依赖项维护 (Dependency maintenance), 确保与最新版本的 FastAPI 和其他依赖项兼容
- 保持项目稳定性和安全性

**❌ 不再提供的功能:**
- 新功能开发 (No new features)
- 一般性 Bug 修复仅限于影响安全性或核心功能的严重问题
- 功能增强型 Pull Requests 将不再被接受

### 版本进入维护模式的时间线

从 Release 历史可以看出:

1. **v14.0.2 (2025 年 10 月 25 日)**:
- 这是最后一个支持 Python 3.9 和 Pydantic v1 的版本
- 公告中明确标注:"This is the last release to support Python 3.9 and Pydantic v1"
- 同时发布维护模式公告

2. **v15.0.0 (2025 年 10 月 25 日)**:
- 放弃 Python 3.9 支持
- 放弃 Pydantic v1 支持
- 正式进入维护模式

3. **v15.0.1 (2025 年 10 月 25 日)**:
- 修复了一个 OAuth callback 中过期 JWT 处理的 bug
- 证明在维护模式下仍然会修复关键 bug

### 做出这个决定的原因

根据项目维护者 Fran ç ois Voron 在 Discussion #1543 中的说明, 主要原因包括:

1. **架构限制**: 多年前做出的某些设计选择现在成为了障碍, 无法在不重建整个项目的情况下改进

2. **框架局限性**: FastAPI Users 仅支持 FastAPI 框架, 而团队希望为更广泛的 Python 框架提供认证解决方案

3. **社区学习**: 从多年的社区反馈和实践中学到了很多, 希望将这些经验融入到新的项目中

4. **认证生态演变**: Python 认证领域的需求和最佳实践在不断演进, 需要一个更现代, 更灵活的解决方案

## 未来规划: 新的 Python 认证工具包

### 官方声明

FastAPI Users 团队正在开发一个**全新的 Python 认证工具包** (new Python authentication toolkit), 该工具包最终将取代 FastAPI Users.

### 新项目的愿景

根据维护者在 Discussion 中的说明, 新项目将具备以下特点:

1. **框架无关性 (Framework-agnostic)**:
- 不仅限于 FastAPI
- 支持任何 Python 框架的认证需求
- 提供核心认证功能库, 各框架可基于此构建集成

2. **更高的灵活性和模块化**:
- 吸取 FastAPI Users 的经验教训
- 提供更灵活的架构设计
- 更好的开发者体验

3. **现代认证模式和标准**:
- 支持最新的认证模式
- 符合现代安全标准
- 更广泛的框架兼容性

4. **100% 开源**:
- 维护者明确承诺新项目将完全开源
- 继续采用宽松许可证
- 欢迎社区贡献

### 当前状态

截至 2025 年 10 月 25 日:
- 新项目尚未公开发布
- 没有公开的代码仓库或具体时间表
- 团队表示 "Stay tuned for updates!" (敬请期待更新)

## 对开发者的建议

### 当前用户

如果你正在使用 FastAPI Users:

1. **继续使用无虞**: 项目稳定, 经过实战检验, 将继续保持安全
2. **及时更新**: 关注安全更新和依赖项维护
3. **选择合适版本**:
- 如果需要 Python 3.9 或 Pydantic v1 支持, 使用 v14.0.2
- 否则可以使用 v15.x 版本

### 新用户

如果你正在考虑使用 FastAPI Users:

1. **评估需求**: 确认现有功能是否满足你的需求
2. **了解限制**: 明确不会有新功能添加
3. **考虑替代方案**:
- 等待新的 Python 认证工具包发布
- 考虑其他认证库如直接使用 FastAPI 的认证功能
- 评估是否适合你的长期项目规划

### 贡献者

1. **安全补丁欢迎**: 关键的安全修复 Pull Requests 仍然会被接受
2. **新功能不接受**: 功能增强型 PR 将不再被审查和合并
3. **关注新项目**: 等待新认证工具包的发布和贡献机会

## 相关资源

- **项目主页**: https://github.com/fastapi-users/fastapi-users
- **文档**: https://fastapi-users.github.io/fastapi-users/
- **PyPI**: https://pypi.org/project/fastapi-users/
- **维护模式公告**: https://github.com/fastapi-users/fastapi-users/discussions/1543
- **作者 GitHub**: https://github.com/frankie567
- **最新版本**: v15.0.1 (2025 年 10 月 25 日)

## 技术细节

### 支持的 Python 版本

- **v15.x**: Python 3.10, 3.11, 3.12, 3.13, 3.14
- **v14.x**: Python 3.9, 3.10, 3.11, 3.12, 3.13
- **更早版本**: 支持 Python 3.8

### 支持的 Pydantic 版本

- **v15.x**: Pydantic V2 only
- **v14.x**: Pydantic V1 和 V2 (向后兼容)
- **v12.x**: Pydantic V1 和 V2 (向后兼容)

### 主要依赖

- FastAPI
- Pydantic
- email-validator
- python-multipart
- pyjwt[crypto]
- pwdlib[argon2,bcrypt] (用于密码哈希)
- 数据库适配器 (sqlalchemy, motor, beanie 等, 可选)

## 总结

FastAPI Users 作为一个成熟的认证库, 进入维护模式是一个深思熟虑的决定. 虽然不会再有新功能, 但项目将继续保持安全和稳定. 对于现有用户而言, 这是一个可靠的选择; 对于新用户, 需要权衡是否等待新的认证工具包发布.

团队正在开发的新 Python 认证工具包承诺提供更灵活, 更现代, 更广泛的框架支持, 值得期待. 这一转变体现了开源项目的成熟度和维护者对社区负责任的态度.