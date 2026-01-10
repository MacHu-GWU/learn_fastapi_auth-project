# Project Code Structure Overview

本文档是项目代码结构的快速索引，帮助开发者快速定位功能模块。

---

## Quick Navigation

| 我想要... | 查看文件 |
|----------|---------|
| 了解整体架构 | [FastAPI-User-Authentication-SaaS-项目技术规格文档.md](FastAPI-User-Authentication-SaaS-项目技术规格文档.md) |
| 添加新的配置项 | [`config.py`](../../learn_fastapi_auth/config.py) |
| 修改数据库模型 | [`models.py`](../../learn_fastapi_auth/models.py) |
| 添加新的 API 端点 | [`app.py`](../../learn_fastapi_auth/app.py) |
| 添加新的 HTML 页面 | [`routers/pages.py`](../../learn_fastapi_auth/routers/pages.py) + [`templates/`](../../learn_fastapi_auth/templates/) |

---

## Backend Module Index

### Core Application

| 文件 | 职责 | 详细文档 |
|-----|------|---------|
| [`app.py`](../../learn_fastapi_auth/app.py) | FastAPI 主应用、路由注册、中间件 | [Phase-1](Phase-1-Change-Walkthrough.md) |
| [`config.py`](../../learn_fastapi_auth/config.py) | 环境变量和配置管理 | [Phase-1](Phase-1-Change-Walkthrough.md#2-配置管理-configpy) |
| [`database.py`](../../learn_fastapi_auth/database.py) | SQLAlchemy 异步数据库连接 | [Phase-1](Phase-1-Change-Walkthrough.md#3-数据库连接-databasepy) |
| [`models.py`](../../learn_fastapi_auth/models.py) | ORM 模型 (User, UserData, Token, RefreshToken) | [Phase-1](Phase-1-Change-Walkthrough.md#4-数据模型-modelspy) |
| [`schemas.py`](../../learn_fastapi_auth/schemas.py) | Pydantic 请求/响应 Schema | [Phase-1](Phase-1-Change-Walkthrough.md#5-请求响应模式-schemaspy) |
| [`paths.py`](../../learn_fastapi_auth/paths.py) | 项目路径集中管理 | - |

### Authentication (`auth/`)

| 文件 | 职责 | 详细文档 |
|-----|------|---------|
| [`auth/users.py`](../../learn_fastapi_auth/auth/users.py) | fastapi-users 配置、UserManager、JWT 策略 | [Phase-1](Phase-1-Change-Walkthrough.md#6-用户认证核心-authuserspy) |
| [`auth/email.py`](../../learn_fastapi_auth/auth/email.py) | 邮件发送 (验证邮件、密码重置邮件) | [Phase-1](Phase-1-Change-Walkthrough.md#7-邮件发送-authemailpy), [Phase-4.1](Phase-4-1-Password-Reset-Feature-Walkthrough.md#3-password-reset-email-function) |
| [`auth/firebase.py`](../../learn_fastapi_auth/auth/firebase.py) | Firebase/Google OAuth 集成 | [Phase-5](Phase-5-Google-OAuth-Feature-Walkthrough.md#4-创建-firebase-模块) |

### Security & Middleware

| 文件 | 职责 | 详细文档 |
|-----|------|---------|
| [`csrf.py`](../../learn_fastapi_auth/csrf.py) | CSRF 保护配置 | [Phase-4.2](Phase-4-2-CSRF-Protection-Walkthrough.md) |
| [`ratelimit.py`](../../learn_fastapi_auth/ratelimit.py) | 请求频率限制 | [Phase-4.2](Phase-4-2-Request-Frequency-Limitation-Walkthrough.md) |
| [`refresh_token.py`](../../learn_fastapi_auth/refresh_token.py) | Refresh Token 管理 | [Phase-4.2](Phase-4-2-Token-Refresh-Walkthrough.md) |

### Admin & Pages

| 文件 | 职责 | 详细文档 |
|-----|------|---------|
| [`admin.py`](../../learn_fastapi_auth/admin.py) | SQLAdmin 管理后台 | [Phase-4 Admin](Phase-4-Admin-Feature-Walkthrough.md) |
| [`routers/pages.py`](../../learn_fastapi_auth/routers/pages.py) | HTML 页面路由 | [Phase-2](Phase-2-Change-Walkthrough.md#3-page-router) |

---

## Frontend File Index

### Templates (`templates/`)

| 文件 | 页面 | 路由 |
|-----|-----|------|
| [`base.html`](../../learn_fastapi_auth/templates/base.html) | 基础模板 (导航栏、Toast) | - |
| [`index.html`](../../learn_fastapi_auth/templates/index.html) | 首页 | `/` |
| [`signup.html`](../../learn_fastapi_auth/templates/signup.html) | 注册页 | `/signup` |
| [`signin.html`](../../learn_fastapi_auth/templates/signin.html) | 登录页 (含 Google OAuth) | `/signin` |
| [`app.html`](../../learn_fastapi_auth/templates/app.html) | 用户主页 (数据编辑、改密码) | `/app` |
| [`forgot_password.html`](../../learn_fastapi_auth/templates/forgot_password.html) | 忘记密码 | `/forgot-password` |
| [`reset_password.html`](../../learn_fastapi_auth/templates/reset_password.html) | 重置密码 | `/reset-password` |
| [`verify_email.html`](../../learn_fastapi_auth/templates/verify_email.html) | 邮箱验证成功 | `/auth/verify-email` |

### JavaScript (`static/js/`)

| 文件 | 职责 | 详细文档 |
|-----|------|---------|
| [`auth.js`](../../learn_fastapi_auth/static/js/auth.js) | 认证工具 (Token 管理、API 请求、Toast、Loading) | [Phase-2](Phase-2-Change-Walkthrough.md#7-authentication-javascript), [Phase-4.3](Phase-4-3-Loading-States-Walkthrough.md) |
| [`app.js`](../../learn_fastapi_auth/static/js/app.js) | App 页面逻辑 (数据加载、编辑、改密码) | [Phase-2](Phase-2-Change-Walkthrough.md#8-app-page-javascript) |
| [`errors.js`](../../learn_fastapi_auth/static/js/errors.js) | 错误消息集中管理 | [Phase-4.3](Phase-4-3-Better-Error-Messages-Walkthrough.md) |

### CSS (`static/css/`)

| 文件 | 内容 |
|-----|-----|
| [`style.css`](../../learn_fastapi_auth/static/css/style.css) | 全局样式、表单、按钮、Toast、Modal、Spinner、骨架屏 |

---

## Feature → Code Mapping

### Authentication Features

| 功能 | 后端 | 前端 | 文档 |
|-----|-----|-----|------|
| 用户注册 | `app.py` (fastapi-users router) | `signup.html` | [Phase-1](Phase-1-Change-Walkthrough.md) |
| 邮箱验证 | `auth/users.py` → `on_after_verify` | `verify_email.html` | [Phase-1](Phase-1-Change-Walkthrough.md) |
| 用户登录 | `app.py` (fastapi-users router) | `signin.html` | [Phase-1](Phase-1-Change-Walkthrough.md) |
| Google OAuth | `auth/firebase.py`, `app.py` → `/api/auth/firebase` | `signin.html` (Firebase SDK) | [Phase-5](Phase-5-Google-OAuth-Feature-Walkthrough.md) |
| 忘记密码 | `auth/email.py` → `send_password_reset_email` | `forgot_password.html` | [Phase-4.1](Phase-4-1-Password-Reset-Feature-Walkthrough.md) |
| 重置密码 | `app.py` (fastapi-users router) | `reset_password.html` | [Phase-4.1](Phase-4-1-Password-Reset-Feature-Walkthrough.md) |
| 修改密码 | `app.py` → `/api/auth/change-password` | `app.html` (modal) | [Phase-4.1](Phase-4-1-Password-Reset-Feature-Walkthrough.md) |
| 记住登录 | `app.py` (middleware), `refresh_token.py` | `signin.html` (checkbox) | [Phase-4.3](Phase-4-3-Remember-Me-Walkthrough.md) |

### Security Features

| 功能 | 实现文件 | 文档 |
|-----|---------|------|
| JWT Access Token | `auth/users.py` → `JWTStrategy` | [Phase-1](Phase-1-Change-Walkthrough.md) |
| Refresh Token | `refresh_token.py`, `app.py` (middleware) | [Phase-4.2](Phase-4-2-Token-Refresh-Walkthrough.md) |
| CSRF 保护 | `csrf.py` | [Phase-4.2](Phase-4-2-CSRF-Protection-Walkthrough.md) |
| 频率限制 | `ratelimit.py` | [Phase-4.2](Phase-4-2-Request-Frequency-Limitation-Walkthrough.md) |

### User Experience Features

| 功能 | 实现文件 | 文档 |
|-----|---------|------|
| 加载状态 | `auth.js`, `style.css` | [Phase-4.3](Phase-4-3-Loading-States-Walkthrough.md) |
| 错误提示 | `errors.js` | [Phase-4.3](Phase-4-3-Better-Error-Messages-Walkthrough.md) |
| 管理后台 | `admin.py` | [Phase-4 Admin](Phase-4-Admin-Feature-Walkthrough.md) |

---

## API Endpoints Summary

### Authentication API

| Method | Path | 功能 | 需要认证 |
|--------|------|------|---------|
| POST | `/api/auth/register` | 注册 | No |
| POST | `/api/auth/login` | 登录 | No |
| POST | `/api/auth/logout` | 登出 | Yes |
| POST | `/api/auth/logout-all` | 登出所有设备 | Yes |
| POST | `/api/auth/refresh` | 刷新 Token | No (需 Cookie) |
| POST | `/api/auth/forgot-password` | 请求重置密码 | No |
| POST | `/api/auth/reset-password` | 重置密码 | No |
| POST | `/api/auth/change-password` | 修改密码 | Yes |
| POST | `/api/auth/firebase` | Google OAuth 登录 | No |
| GET | `/api/users/me` | 获取当前用户信息 | Yes |

### User Data API

| Method | Path | 功能 | 需要认证 |
|--------|------|------|---------|
| GET | `/api/user-data` | 获取用户数据 | Yes |
| PUT | `/api/user-data` | 更新用户数据 | Yes |

### Admin

| Path | 功能 |
|------|------|
| `/admin` | 管理后台 (需 superuser) |

---

## Development Phase Summary

| Phase | 主题 | 核心内容 |
|-------|------|---------|
| **Phase 1** | 核心认证 | fastapi-users 集成、JWT、邮件验证 |
| **Phase 2** | 前端页面 | Jinja2 模板、静态文件、页面路由 |
| **Phase 3** | 用户数据 | UserData CRUD、App 页面 |
| **Phase 4.1** | 密码管理 | 忘记密码、重置密码、修改密码 |
| **Phase 4.2** | 安全增强 | CSRF、频率限制、Token 刷新 |
| **Phase 4.3** | 用户体验 | 加载状态、错误消息、记住登录 |
| **Phase 4 Admin** | 管理后台 | SQLAdmin 用户管理 |
| **Phase 5** | OAuth | Google 登录 (Firebase) |

---

## Where to Look When...

### Adding a New Feature

1. **新 API 端点**: 在 `app.py` 添加路由
2. **新数据模型**: 在 `models.py` 定义，在 `schemas.py` 添加 Schema
3. **新配置项**: 在 `config.py` 添加字段和 `from_env` 加载逻辑
4. **新 HTML 页面**: 在 `templates/` 创建模板，在 `routers/pages.py` 添加路由

### Debugging

| 问题类型 | 检查文件 |
|---------|---------|
| 认证失败 | `auth/users.py`, `app.py` (middleware) |
| 数据库错误 | `database.py`, `models.py` |
| 前端不工作 | 浏览器控制台, `auth.js`, `app.js` |
| CSRF 错误 | `csrf.py`, 检查是否需要排除 URL |
| 频率限制 | `ratelimit.py`, 检查配置 |
| 邮件发送失败 | `auth/email.py`, 检查 SMTP 配置 |

### Testing

| 测试类型 | 位置 |
|---------|------|
| 单元测试 | `tests/` 目录 |
| 集成测试 | `tests/test_app.py` |
| 运行测试 | `mise run test` 或 `.venv/bin/pytest` |
| 覆盖率报告 | `mise run cov` |

---

*Last updated: 2025-01*
