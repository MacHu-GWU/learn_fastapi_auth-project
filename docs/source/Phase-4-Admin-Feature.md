# Phase 4: Admin 管理后台实现计划

## 1. 需求概述

实现一个管理员后台，让具有 `is_superuser=True` 权限的用户能够：
- 查看所有注册用户的列表
- 搜索、筛选用户
- 查看用户详情
- 管理用户状态（激活/禁用、验证状态等）

## 2. 技术选型

**使用 [SQLAdmin](https://github.com/aminalaee/sqladmin)** - 一个专为 FastAPI + SQLAlchemy 设计的 Admin 库。

选择理由：
- 与现有技术栈（FastAPI + SQLAlchemy）完美契合
- 开箱即用，配置简单
- 自带美观的 UI（基于 Tabler Admin 模板）
- 支持自定义权限验证
- 活跃维护，文档完善

## 3. 功能范围（Scope）

### 3.1 本次实现（In Scope）

| 功能 | 描述 |
|------|------|
| Admin 入口 | `/admin` 路由，仅 superuser 可访问 |
| 用户列表 | 显示所有用户，支持分页 |
| 用户搜索 | 按 email 搜索用户 |
| 用户详情 | 查看单个用户的完整信息 |
| 用户编辑 | 修改用户的 `is_active`、`is_verified`、`is_superuser` 状态 |
| 权限保护 | 非 superuser 访问 admin 页面返回 403 |

### 3.2 暂不实现（Out of Scope）

| 功能 | 原因 |
|------|------|
| 删除用户 | 风险较高，暂不开放，后续可添加 |
| 创建用户 | 用户应通过正常注册流程创建 |
| 修改密码 | 用户应通过密码重置流程自行修改 |
| UserData 管理 | 用户私有数据，admin 不应直接访问 |
| Token 管理 | 技术细节，不需要在 UI 中管理 |
| Dashboard 统计 | 本次聚焦用户管理，统计功能后续添加 |

## 4. 用户列表显示字段

| 字段 | 说明 |
|------|------|
| ID | 用户 UUID（截断显示） |
| Email | 邮箱地址 |
| Is Active | 账户是否激活 |
| Is Verified | 邮箱是否已验证 |
| Is Superuser | 是否为管理员 |
| Created At | 注册时间 |

## 5. 实现计划

### Step 1: 添加依赖
在 `pyproject.toml` 中添加 `sqladmin` 依赖。

### Step 2: 创建 Admin 模块
创建 `learn_fastapi_auth/admin.py`，包含：
- `UserAdmin` 视图类配置
- 权限验证逻辑（基于 session/cookie 的 superuser 验证）

### Step 3: 集成到 App
在 `app.py` 中初始化并挂载 SQLAdmin。

### Step 4: 测试
- 验证 superuser 可以访问 `/admin`
- 验证普通用户无法访问
- 验证用户列表、搜索、编辑功能正常

## 6. 权限验证方案

SQLAdmin 使用基于 Session 的认证（与我们的 JWT Bearer Token 不同）。实现方案：

```
用户访问 /admin → SQLAdmin 检查 session →
  ├── 已登录且是 superuser → 允许访问
  └── 未登录或非 superuser → 重定向到登录页
```

SQLAdmin 提供 `AuthenticationBackend` 接口，我们需要实现：
- `login()`: 验证管理员凭据
- `logout()`: 清除 session
- `authenticate()`: 检查当前请求是否已认证

Admin 登录将使用独立的 session cookie，与主应用的 JWT 认证分离。

## 7. 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `pyproject.toml` | 修改 | 添加 `sqladmin` 依赖 |
| `learn_fastapi_auth/admin.py` | 新增 | Admin 配置和权限验证 |
| `learn_fastapi_auth/app.py` | 修改 | 挂载 SQLAdmin |

## 8. 预期效果

实现后，管理员可以：
1. 访问 `http://localhost:8000/admin`
2. 使用 superuser 账户登录
3. 在用户列表中查看、搜索所有用户
4. 点击用户查看详情
5. 编辑用户的激活状态、验证状态、管理员状态

---

**文档状态**: 已实现

**实际代码量**: ~100 行
