# 认证系统工作原理详解

本文档详细解释 fastapi-users 库如何实现用户登录认证，以及为什么只有登录用户才能访问 /app 页面。

---

## 目录

1. [Router 和 app.include_router 详解](#1-router-和-appinclude_router-详解)
2. [auth/users.py 模块解析](#2-authusers-py-模块解析)
3. [前端认证机制](#3-前端认证机制)
4. [完整认证流程图](#4-完整认证流程图)

---

## 1. Router 和 app.include_router 详解

### 1.1 什么是 Router？

**Router（路由器）** 是 FastAPI 中用于组织和管理 API 端点的对象。你可以把它理解为一个"子应用"或"端点分组器"。

**类比理解**：
- `app` 是整个公司
- `router` 是公司里的不同部门
- 每个部门（router）有自己的职责（端点）
- 最终所有部门都归属于公司（include_router）

**代码示例**：

```python
from fastapi import APIRouter

# 创建一个路由器
router = APIRouter()

# 在路由器上定义端点
@router.get("/hello")
async def say_hello():
    return {"message": "Hello"}

@router.post("/goodbye")
async def say_goodbye():
    return {"message": "Goodbye"}
```

### 1.2 app.include_router 做了什么？

`app.include_router()` 把一个 Router 中定义的所有端点"挂载"到主应用上。

**在 app.py 中的实际使用**：

```python
# 第62行：挂载页面路由
app.include_router(pages_router)
# 这会添加: GET /, GET /signup, GET /signin, GET /app

# 第69-73行：挂载注册路由
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/auth",
    tags=["auth"],
)
# 这会添加: POST /api/auth/register
```

**参数说明**：
- `prefix="/api/auth"`: 给所有端点添加前缀。原本的 `/register` 变成 `/api/auth/register`
- `tags=["auth"]`: 在 Swagger 文档中分组显示

### 1.3 fastapi-users 提供的 Router

fastapi-users 库预先定义了多个 Router，我们只需要"挂载"它们：

| 方法调用 | 添加的端点 | 功能 |
|---------|-----------|------|
| `get_register_router()` | POST /register | 用户注册 |
| `get_auth_router()` | POST /login, POST /logout | 登录登出 |
| `get_verify_router()` | POST /verify, POST /request-verify-token | 邮箱验证 |
| `get_reset_password_router()` | POST /forgot-password, POST /reset-password | 密码重置 |
| `get_users_router()` | GET /me, PATCH /me, DELETE /me | 用户信息管理 |

---

## 2. auth/users.py 模块解析

这个模块是认证系统的核心，包含以下关键组件：

### 2.1 认证后端 (auth_backend)

**位置**: 第121-136行

```python
# 1. 定义传输方式 - 使用 Bearer Token
bearer_transport = BearerTransport(tokenUrl="api/auth/login")

# 2. 定义 Token 策略 - 使用 JWT
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=config.secret_key,        # 签名密钥
        lifetime_seconds=config.access_token_lifetime,  # 有效期
    )

# 3. 组合成认证后端
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
```

**三个组件的作用**：

| 组件 | 作用 | 类比 |
|------|------|------|
| **BearerTransport** | 定义 Token 如何传输（在 HTTP Header 中以 `Bearer xxx` 格式） | 快递的运输方式 |
| **JWTStrategy** | 定义 Token 如何生成和验证（JWT 格式，带签名） | 快递包裹的打包和验货方式 |
| **AuthenticationBackend** | 把传输和策略组合在一起，形成完整的认证方案 | 整个快递服务 |

**Bearer Token 格式**：
```
HTTP Header:
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2.2 FastAPIUsers 实例

**位置**: 第142行

```python
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
```

这是整个认证系统的核心对象，它：
- 接收 `get_user_manager` 函数来管理用户
- 接收 `[auth_backend]` 列表来定义支持的认证方式
- 提供各种 Router 生成器（`get_register_router()` 等）
- 提供用户依赖项生成器（`current_user()` 等）

### 2.3 当前用户依赖项

**位置**: 第144-148行

```python
# 要求用户已登录且账户激活
current_active_user = fastapi_users.current_user(active=True)

# 要求用户已登录、账户激活、且邮箱已验证
current_verified_user = fastapi_users.current_user(active=True, verified=True)
```

**这是保护 API 端点的关键！**

在 app.py 中的使用：

```python
@app.get("/api/user-data")
async def get_user_data(
    user: User = Depends(current_verified_user),  # <-- 这里！
    session: AsyncSession = Depends(get_async_session),
):
    # 只有通过验证的用户才能执行到这里
    ...
```

**工作原理**：
1. 用户请求 `/api/user-data`
2. FastAPI 看到 `Depends(current_verified_user)`
3. 从请求 Header 中提取 `Authorization: Bearer xxx`
4. 用 JWT 密钥验证 Token 签名
5. 解码 Token 获取 user_id
6. 从数据库查询用户
7. 检查用户是否 `is_active=True` 且 `is_verified=True`
8. 如果全部通过，把 user 对象传给函数
9. 如果任何步骤失败，返回 401 Unauthorized

### 2.4 UserManager 生命周期钩子

**位置**: 第36-108行

UserManager 定义了用户相关事件的回调函数：

```python
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    
    async def on_after_register(self, user, request):
        """用户注册成功后调用"""
        # 1. 发送验证邮件
        await self.request_verify(user, request)
        # 2. 设置用户为未激活状态
        user.is_active = False
        await session.commit()
    
    async def on_after_request_verify(self, user, token, request):
        """请求验证邮件时调用"""
        await send_verification_email(user.email, token)
    
    async def on_after_verify(self, user, request):
        """用户验证邮箱成功后调用"""
        # 激活用户账户
        user.is_active = True
        # 创建 UserData 记录
        user_data = UserData(user_id=user.id, text_value="")
        await session.commit()
    
    async def on_after_forgot_password(self, user, token, request):
        """用户请求重置密码时调用"""
        print(f"Reset token: {token}")  # 生产环境应发送邮件
```

**钩子调用时机**：

| 钩子 | 触发条件 | 用途 |
|------|----------|------|
| `on_after_register` | POST /api/auth/register 成功 | 发送验证邮件，设置未激活 |
| `on_after_request_verify` | POST /api/auth/request-verify-token 成功 | 发送验证邮件 |
| `on_after_verify` | POST /api/auth/verify 成功 | 激活账户，初始化用户数据 |
| `on_after_forgot_password` | POST /api/auth/forgot-password 成功 | 发送重置密码邮件 |

### 2.5 get_user_db 和 get_user_manager

这两个是 FastAPI 的**依赖注入函数**：

```python
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """提供数据库访问层"""
    yield SQLAlchemyUserDatabase(session, User)

async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """提供用户管理器"""
    yield UserManager(user_db)
```

**依赖链**：
```
get_async_session (数据库会话)
       ↓
   get_user_db (用户数据库操作)
       ↓
 get_user_manager (用户管理器)
       ↓
   FastAPIUsers (认证系统)
```

---

## 3. 前端认证机制

### 3.1 Token 存储和管理 (auth.js)

**Token 存储在浏览器的 localStorage 中**：

```javascript
// 存储 Token
function setToken(token) {
    localStorage.setItem('auth_token', token);
}

// 获取 Token
function getToken() {
    return localStorage.getItem('auth_token');
}

// 检查是否已登录
function isLoggedIn() {
    return !!getToken();  // Token 存在则为 true
}
```

### 3.2 登录流程 (signin.html)

**第75-93行的关键代码**：

```javascript
// 1. 用户提交表单
const formData = new URLSearchParams();
formData.append('username', email);
formData.append('password', password);

// 2. 调用后端登录 API
const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: formData
});

// 3. 登录成功，保存 Token
if (response.ok) {
    const data = await response.json();
    setToken(data.access_token);  // <-- 保存到 localStorage
    setUserEmail(email);
    window.location.href = '/app';  // 跳转到 app 页面
}
```

### 3.3 访问保护页面 (app.js)

**/app 页面的访问控制是在前端 JavaScript 中实现的**：

```javascript
document.addEventListener('DOMContentLoaded', async () => {
    // 检查是否已登录
    if (!isLoggedIn()) {
        // 未登录，跳转到登录页
        window.location.href = '/signin?error=login_required';
        return;
    }

    // 已登录，加载用户数据
    await loadUserData();
});
```

**这只是第一层保护（前端）**。即使绕过前端检查，后端 API 仍然有保护。

### 3.4 API 请求携带 Token (auth.js)

```javascript
async function apiRequest(url, options = {}) {
    const token = getToken();
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    // 如果有 Token，添加到 Header
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, { ...options, headers });
    
    // 如果返回 401，说明 Token 无效或过期
    if (response.status === 401) {
        removeToken();
        window.location.href = '/signin?error=session_expired';
        return null;
    }
    
    return response;
}
```

### 3.5 为什么 /app 页面需要登录才能看？

**两层保护机制**：

| 层级 | 保护机制 | 代码位置 | 作用 |
|------|----------|----------|------|
| **前端** | JavaScript 检查 localStorage | app.js 第17-20行 | 未登录用户立即跳转 |
| **后端** | Depends(current_verified_user) | app.py 第144行 | API 拒绝无效请求 |

**流程图**：

```
用户访问 /app
     ↓
[前端检查] isLoggedIn()?
     ↓
   No → 跳转到 /signin
     ↓
   Yes → 调用 /api/user-data
     ↓
[后端检查] Token 有效?
     ↓
   No → 返回 401, 前端跳转登录
     ↓
   Yes → 返回用户数据
     ↓
显示数据
```

---

## 4. 完整认证流程图

### 4.1 注册流程

```
用户填写邮箱密码
        ↓
POST /api/auth/register
        ↓
fastapi-users 创建用户 (is_active=True, is_verified=False)
        ↓
调用 on_after_register()
        ↓
    ├── 发送验证邮件 (request_verify)
    └── 设置 is_active=False
        ↓
用户收到邮件，点击链接
        ↓
GET /auth/verify-email?token=xxx
        ↓
重定向到 /signin?verified=pending&token=xxx
        ↓
前端 JavaScript 调用 POST /api/auth/verify
        ↓
fastapi-users 验证 token
        ↓
调用 on_after_verify()
        ↓
    ├── 设置 is_active=True
    ├── 设置 is_verified=True
    └── 创建 UserData 记录
        ↓
注册完成，可以登录
```

### 4.2 登录流程

```
用户输入邮箱密码
        ↓
POST /api/auth/login (form-urlencoded)
        ↓
fastapi-users 验证密码
        ↓
检查 is_active=True?
        ↓
    No → 返回错误 "LOGIN_BAD_CREDENTIALS"
        ↓
    Yes → 生成 JWT Token
        ↓
返回 { access_token: "eyJ...", token_type: "bearer" }
        ↓
前端保存 Token 到 localStorage
        ↓
跳转到 /app
```

### 4.3 访问受保护资源流程

```
用户访问 /app
        ↓
app.js 检查 isLoggedIn()
        ↓
调用 apiRequest('/api/user-data')
        ↓
自动添加 Header: Authorization: Bearer eyJ...
        ↓
后端收到请求
        ↓
Depends(current_verified_user) 执行验证
        ↓
    ├── 解析 JWT Token
    ├── 验证签名
    ├── 检查过期时间
    ├── 从数据库查询用户
    ├── 检查 is_active=True
    └── 检查 is_verified=True
        ↓
全部通过 → 执行 API 逻辑，返回数据
任一失败 → 返回 401 Unauthorized
```

---

## 5. 关键代码文件总结

| 文件 | 职责 |
|------|------|
| `auth/users.py` | 认证后端配置、用户管理器、生命周期钩子 |
| `app.py` | 挂载所有路由、定义受保护的 API 端点 |
| `static/js/auth.js` | Token 存储、API 请求封装、导航状态管理 |
| `static/js/app.js` | /app 页面逻辑、前端访问控制 |
| `templates/signin.html` | 登录表单、调用登录 API |

---

## 6. 安全性说明

### 6.1 JWT Token 安全

- Token 使用 `config.secret_key` 签名，无法伪造
- Token 有过期时间（`access_token_lifetime`）
- Token 存储在 localStorage，XSS 攻击可能窃取

### 6.2 密码安全

- 密码使用 bcrypt 哈希存储
- fastapi-users 内置密码强度验证
- 数据库不存储明文密码

### 6.3 双重验证

- 前端 JavaScript 检查提供用户体验
- 后端 Depends 检查提供真正的安全保障
- 即使前端被绕过，后端仍然安全

---

**文档结束**
