# Phase 4: 优化和扩展 - 详细任务说明

本文档详细解释 Phase 4 中每个任务的具体内容、实现方式和目的。

---

## 1. 账户管理 (Account Management)

### 1.1 密码重置功能 (Forgot Password)

**是什么**: 用户忘记密码时，通过邮箱验证重置密码的完整流程。

**用户流程**:
1. 用户点击登录页面的"忘记密码"链接
2. 进入"忘记密码"页面，输入注册邮箱
3. 系统发送包含重置链接的邮件到该邮箱
4. 用户点击邮件中的链接，进入"设置新密码"页面
5. 用户输入新密码，确认后完成重置
6. 跳转到登录页面，用新密码登录

**需要实现的组件**:
- 前端页面: `forgot_password.html` (输入邮箱) 和 `reset_password.html` (设置新密码)
- 后端 API: fastapi-users 已内置 `/auth/forgot-password` 和 `/auth/reset-password` 端点
- 邮件模板: 重置密码邮件内容
- UserManager 钩子: `on_after_forgot_password()` 发送邮件

**与邮箱验证的区别**:
- 邮箱验证: 新用户注册后激活账户
- 密码重置: 已有用户忘记密码时重新设置

---

### 1.2 修改密码功能 (Change Password)

**是什么**: 已登录用户在账户设置中主动修改密码。

**用户流程**:
1. 用户登录后进入账户设置页面
2. 点击"修改密码"
3. 输入当前密码（验证身份）
4. 输入新密码和确认新密码
5. 提交后密码更新成功

**需要实现的组件**:
- 前端 UI: 修改密码表单（在账户设置页面或弹窗）
- 后端 API: 验证旧密码 + 更新新密码的端点
- 安全考虑: 必须验证当前密码，防止他人在用户未退出时修改

**与密码重置的区别**:
- 修改密码: 用户知道当前密码，主动更换
- 密码重置: 用户忘记密码，通过邮箱验证重置

---

### 1.3 账户设置页面 (Account Settings Page)

**是什么**: 一个集中管理用户账户信息的页面。

**页面功能**:
- 显示当前邮箱地址
- 修改密码入口
- 删除账户选项（可选）
- 查看账户创建时间
- 查看最后登录时间（可选）

**需要实现的组件**:
- 前端页面: `settings.html`
- 页面路由: `GET /settings`
- 后端 API: 获取用户详细信息的端点（fastapi-users 的 `/users/me` 已提供基础信息）

---

## 2. 安全增强 (Security Enhancements)

### 2.1 CSRF 保护 (Cross-Site Request Forgery Protection)

**是什么**: 防止恶意网站冒用已登录用户的身份发起请求。

**攻击场景举例**:
1. 用户在浏览器中登录了你的网站（有 Cookie/Token）
2. 用户访问了一个恶意网站
3. 恶意网站的页面包含隐藏表单，自动提交到你的网站
4. 浏览器会自动带上 Cookie，请求被当作用户本人发起

**防护机制**:
- 服务器生成一个随机 CSRF Token，存在 Session 或 Cookie 中
- 每个表单提交时必须携带这个 Token
- 服务器验证 Token 是否匹配
- 恶意网站无法获取这个 Token，所以伪造请求会被拒绝

**实现方式**:
- 使用 `starlette-csrf` 或 `fastapi-csrf-protect` 库
- 或者在 Cookie 中设置 `SameSite=Strict` 属性

**我们项目的情况**:
由于我们使用 JWT Bearer Token（存在 localStorage，不是 Cookie），CSRF 风险相对较低。但如果后续改用 Cookie 存储 Token，就必须添加 CSRF 保护。

---

### 2.2 请求频率限制 (Rate Limiting)

**是什么**: 限制单个 IP 或用户在一定时间内的请求次数。

**防护目的**:
- **防止暴力破解**: 攻击者尝试大量密码组合猜测用户密码
- **防止 DDoS**: 阻止恶意请求占用服务器资源
- **防止滥用**: 限制 API 调用频率，保护服务稳定性

**常见策略**:
- 登录接口: 每 IP 每分钟最多 5 次尝试
- 注册接口: 每 IP 每小时最多 10 次
- 密码重置: 每邮箱每小时最多 3 次
- 通用 API: 每用户每分钟 60 次

**实现方式**:
- 使用 `slowapi` 库（基于 Flask-Limiter）
- 或使用 Redis 存储计数器
- 返回 `429 Too Many Requests` 状态码

**示例代码结构**:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

---

### 2.3 Token 刷新机制 (Token Refresh)

**是什么**: 在 Access Token 过期前，使用 Refresh Token 获取新的 Access Token，无需用户重新登录。

**为什么需要**:
- Access Token 有效期短（如 15-60 分钟）-> 安全性高，但用户体验差
- Refresh Token 有效期长（如 7-30 天）-> 用户体验好
- 结合使用：用短期 Token 做认证，用长期 Token 刷新

**双 Token 机制**:

| Token 类型 | 有效期 | 存储位置 | 用途 |
|-----------|--------|----------|------|
| Access Token | 15-60 分钟 | localStorage | API 请求认证 |
| Refresh Token | 7-30 天 | HttpOnly Cookie | 获取新 Access Token |

**刷新流程**:
1. 前端检测 Access Token 即将过期（或收到 401）
2. 自动调用 `/auth/refresh` 端点
3. 服务器验证 Refresh Token，签发新的 Access Token
4. 前端更新存储的 Access Token
5. 用户无感知地继续使用

**安全考虑**:
- Refresh Token 应存储在 HttpOnly Cookie 中（JavaScript 无法读取）
- Refresh Token 被盗用时，可以在服务器端撤销
- 可实现"Refresh Token Rotation"：每次刷新都发放新的 Refresh Token

---

## 3. 用户体验优化 (UX Improvements)

### 3.1 加载动画 (Loading States)

**是什么**: 在异步操作期间显示视觉反馈，让用户知道系统正在处理。

**需要添加加载状态的地方**:
- 登录/注册按钮点击后
- 数据保存时
- 页面初始化加载数据时
- 任何 API 请求期间

**实现方式**:
- 按钮内显示 Spinner：`<button><span class="spinner"></span> Loading...</button>`
- 禁用按钮防止重复提交
- 全局加载遮罩（可选）
- 骨架屏 Skeleton Screen（可选）

**当前项目已有**:
我们在 `app.js` 的 `saveUserData()` 中已实现按钮加载状态：

```javascript
saveBtn.innerHTML = '<span class="spinner"></span> Saving...';
```

**可以改进的地方**:
- 登录/注册表单提交时添加加载状态
- 页面初始加载时显示骨架屏
- 统一的 Loading 组件

---

### 3.2 更友好的错误提示 (Better Error Messages)

**是什么**: 将技术性的错误信息转换为用户能理解的提示。

**当前问题**:
API 返回的错误如 `LOGIN_BAD_CREDENTIALS`、`REGISTER_USER_ALREADY_EXISTS` 对用户不友好。

**改进方案**:

| 原始错误 | 用户友好提示 |
|---------|------------|
| `LOGIN_BAD_CREDENTIALS` | "邮箱或密码不正确，请检查后重试" |
| `REGISTER_USER_ALREADY_EXISTS` | "该邮箱已被注册，请直接登录或使用其他邮箱" |
| `VERIFY_USER_BAD_TOKEN` | "验证链接已失效，请重新申请验证邮件" |
| `RESET_PASSWORD_BAD_TOKEN` | "重置链接已过期，请重新申请" |
| `Network Error` | "网络连接失败，请检查网络后重试" |
| `500 Internal Server Error` | "服务器出现问题，请稍后重试" |

**实现方式**:

```javascript
const ERROR_MESSAGES = {
    'LOGIN_BAD_CREDENTIALS': '邮箱或密码不正确',
    'REGISTER_USER_ALREADY_EXISTS': '该邮箱已被注册',
    // ...
};

function getErrorMessage(apiError) {
    return ERROR_MESSAGES[apiError] || '操作失败，请重试';
}
```

---

### 3.3 记住登录状态 (Remember Me)

**是什么**: 登录时勾选"记住我"，延长登录状态的有效期。

**用户流程**:
1. 登录页面显示"记住我"复选框
2. 不勾选：Token 有效期短（如 1 小时）
3. 勾选：Token 有效期长（如 30 天）

**实现方式**:

**方案 A - 不同有效期的 Token**:

```python
@app.post("/api/auth/login")
async def login(remember_me: bool = False):
    lifetime = 30 * 24 * 3600 if remember_me else 3600  # 30天 vs 1小时
    token = create_token(user, lifetime)
    return {"access_token": token}
```

**方案 B - 使用 Refresh Token**:
- 不勾选：只发 Access Token
- 勾选：同时发 Refresh Token（存在持久 Cookie 中）

**安全考虑**:
- 公共电脑上不建议使用"记住我"
- 可以在账户设置中查看和撤销已登录的设备
- 敏感操作（如修改密码）即使"记住我"也需重新验证

---

## 4. 管理功能 (Admin Features)

### 4.1 管理员后台 (Admin Dashboard)

**是什么**: 只有管理员能访问的页面，用于管理系统和用户。

**功能列表**:
- 查看系统统计（总用户数、今日注册数、活跃用户数）
- 用户管理（查看、搜索、禁用、删除用户）
- 查看系统日志（可选）

**权限控制**:
需要在 User 模型中添加 `is_superuser` 字段（fastapi-users 已内置）：

```python
class User(SQLAlchemyBaseUserTableUUID, Base):
    # fastapi-users 已包含:
    # is_superuser: bool = False
```

**访问控制**:

```python
# 只允许超级用户访问
current_superuser = fastapi_users.current_user(active=True, superuser=True)

@router.get("/admin/users")
async def list_users(user: User = Depends(current_superuser)):
    # 只有 is_superuser=True 的用户能访问
    ...
```

**需要实现的组件**:
- 前端页面: `admin.html` 或 `admin/` 目录下多个页面
- 页面路由: `GET /admin`, `GET /admin/users`
- 后端 API: 用户列表、删除用户等管理接口

---

### 4.2 用户列表查看 (User List View)

**是什么**: 管理员查看所有注册用户的列表。

**显示信息**:
- 用户 ID
- 邮箱地址
- 注册时间
- 是否已验证邮箱
- 是否激活
- 最后登录时间（可选）

**功能**:
- 分页显示（每页 20 条）
- 搜索（按邮箱搜索）
- 排序（按注册时间、邮箱等）
- 操作按钮（查看详情、禁用、删除）

**后端 API 示例**:

```python
@router.get("/admin/users")
async def list_users(
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    query = select(User)
    if search:
        query = query.where(User.email.contains(search))
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await session.execute(query)
    users = result.scalars().all()
    return {"users": users, "page": page, "total": total_count}
```

**删除用户功能**:

```python
@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    admin: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    # 删除用户及其关联数据（UserData, Token 等）
    ...
```

---

## 总结：Phase 4 任务优先级建议

| 优先级 | 任务 | 原因 |
|-------|------|------|
| **高** | 密码重置功能 | 用户基本需求，丢失密码无法恢复账户 |
| **高** | 请求频率限制 | 安全必需，防止暴力破解 |
| **中** | 修改密码 | 账户安全基本功能 |
| **中** | 更友好的错误提示 | 提升用户体验，减少支持工作 |
| **中** | 账户设置页面 | 整合账户管理功能的入口 |
| **低** | CSRF 保护 | 当前使用 Bearer Token，风险较低 |
| **低** | Token 刷新机制 | 当前 Token 有效期可设长一些替代 |
| **低** | 记住登录状态 | 可通过调整 Token 有效期简单实现 |
| **低** | 加载动画 | 已有基础实现，可后续完善 |
| **可选** | 管理员后台 | 取决于项目规模和需求 |

---

**文档结束**
