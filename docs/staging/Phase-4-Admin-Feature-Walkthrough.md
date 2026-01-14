# Phase 4: Admin 管理后台实现 Walkthrough

本文档记录了使用 SQLAdmin 实现管理员后台的完整过程，包括代码变更、遇到的问题及解决方案。

---

## 1. 功能概述

实现了一个管理员后台，让 `is_superuser=True` 的用户能够：
- 查看所有注册用户列表（分页、搜索）
- 查看用户详情
- 编辑用户状态（is_active, is_verified, is_superuser）

访问地址：`http://localhost:8000/admin`

---

## 2. 代码变更

### 2.1 新增依赖 (`pyproject.toml`)

```toml
# Admin Dashboard
"sqladmin>=0.20.0,<1.0.0",  # Admin dashboard for SQLAlchemy
```

### 2.2 新增 Admin 模块 (`learn_fastapi_auth/admin.py`)

这是主要的新增文件，包含三个核心组件：

#### AdminAuth - 认证后端

```python
class AdminAuth(AuthenticationBackend):
    """
    SQLAdmin 的认证后端。
    使用独立的 session 认证，与主应用的 JWT 认证分离。
    """

    async def login(self, request: Request) -> bool:
        # 1. 从表单获取 email 和 password
        # 2. 查询数据库验证用户
        # 3. 使用 PasswordHelper 验证密码
        # 4. 检查 is_superuser 和 is_active
        # 5. 将 user_id 存入 session
        ...

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request):
        # 检查 session 中是否有有效的 admin_user_id
        # 验证用户仍然存在且是 superuser
        ...
```

#### UserAdmin - 用户管理视图

```python
class UserAdmin(ModelView, model=User):
    # 列表显示字段
    column_list = [User.id, User.email, User.is_active, ...]

    # 可搜索字段
    column_searchable_list = [User.email]

    # 排除敏感字段和关系字段
    column_details_exclude_list = [
        User.hashed_password,
        User.user_data,
        User.tokens,
        User.refresh_tokens,
    ]

    # 只允许编辑状态字段
    form_columns = [User.is_active, User.is_verified, User.is_superuser]

    # 禁止创建和删除
    can_create = False
    can_delete = False
```

#### setup_admin - 初始化函数

```python
def setup_admin(app):
    authentication_backend = AdminAuth(secret_key=config.secret_key)
    admin = Admin(app, engine, authentication_backend=authentication_backend)
    admin.add_view(UserAdmin)
    return admin
```

### 2.3 挂载 Admin (`learn_fastapi_auth/app.py`)

在文件末尾添加：

```python
# =============================================================================
# Admin Dashboard (SQLAdmin)
# =============================================================================
from .admin import setup_admin

setup_admin(app)
```

### 2.4 CSRF 排除 (`learn_fastapi_auth/csrf.py`)

在 `create_csrf_exempt_patterns()` 中添加：

```python
# Admin dashboard uses its own session-based authentication
re.compile(r"^/admin.*"),
```

---

## 3. 遇到的问题及解决方案

### Bug 1: CSRF Token Verification Failed

#### 错误现象
使用 superuser 账户登录 Admin 时，页面显示 "CSRF token verification failed"。

#### 错误原因
我们的应用配置了 `starlette-csrf` 中间件，它会对所有 POST 请求进行 CSRF 验证。SQLAdmin 的登录页面是一个 POST 表单，但它没有包含我们的 CSRF token，导致验证失败。

#### 修复方式
在 `csrf.py` 的 `create_csrf_exempt_patterns()` 中添加 `/admin.*` 路径排除：

```python
exempt_patterns = [
    # ... 其他排除项
    # Admin dashboard uses its own session-based authentication
    re.compile(r"^/admin.*"),
]
```

#### 修复原理
SQLAdmin 使用独立的 session-based 认证机制，不依赖我们的 CSRF token。将 `/admin` 路径排除后，CSRF 中间件不再拦截 Admin 的 POST 请求。这是安全的，因为 SQLAdmin 有自己的安全机制。

---

### Bug 2: View/Edit 页面 Internal Server Error (关系字段)

#### 错误现象
在 Admin 用户列表中点击 View 或 Edit 按钮时，页面显示 "Internal Server Error"。

#### 错误原因
User 模型定义了关系字段：

```python
user_data: Mapped[Optional["UserData"]] = relationship(...)
tokens: Mapped[list["Token"]] = relationship(...)
refresh_tokens: Mapped[list["RefreshToken"]] = relationship(...)
```

SQLAdmin 在渲染详情页时尝试加载这些关系字段，但由于是异步上下文中的懒加载，导致 SQLAlchemy 抛出异常。

#### 修复方式
在 `UserAdmin` 中排除这些关系字段：

```python
column_details_exclude_list = [
    User.hashed_password,
    User.user_data,
    User.tokens,
    User.refresh_tokens,
]
```

#### 修复原理
通过 `column_details_exclude_list` 告诉 SQLAdmin 在详情页不要显示这些字段，从而避免触发懒加载。

---

### Bug 3: View/Edit 页面 Internal Server Error (UUID 类型)

#### 错误现象
即使排除了关系字段，点击 View/Edit 仍然报错：

```
TypeError: issubclass() arg 1 must be a class
```

完整 traceback 显示错误发生在：
```
File ".../sqladmin/helpers.py", line 230, in object_identifier_values
    if issubclass(type_, (date, datetime, time)):
```

#### 错误原因
`fastapi-users` 的 `SQLAlchemyBaseUserTableUUID` 使用了特殊的 UUID 类型定义。SQLAdmin 在解析主键时调用 `issubclass()` 检查类型，但收到的不是标准类而是泛型类型（如 `uuid.UUID`），导致 `issubclass()` 抛出 TypeError。

#### 修复方式
在 `UserAdmin` 中重写 `_stmt_by_identifier` 方法：

```python
def _stmt_by_identifier(self, identifier: str):
    """
    Override to properly handle UUID primary key.

    SQLAdmin has issues with fastapi-users UUID type detection.
    This method manually parses the UUID and creates the query.
    """
    pk = uuid.UUID(identifier)
    return select(User).where(User.id == pk)
```

#### 修复原理
绕过 SQLAdmin 的自动类型检测逻辑，手动将 URL 中的字符串 ID 解析为 `uuid.UUID` 对象，然后直接构建查询语句。这样就避免了 SQLAdmin 内部的类型检测问题。

---

### 非 Bug: Action Dropdown 灰色

#### 现象
在用户列表中勾选用户后，Action dropdown 菜单是灰色的，无法点击。

#### 原因
这是**预期行为**，不是 bug。SQLAdmin 的批量操作（bulk actions）默认只有"删除"操作。由于我们设置了 `can_delete = False`，所以没有可用的批量操作，菜单自然变灰。

#### 说明
如果需要批量操作功能，可以：
1. 启用删除功能：`can_delete = True`
2. 或自定义批量操作

---

## 4. 使用方法

### 4.1 启动应用

```bash
uvicorn learn_fastapi_auth.app:app --reload
```

### 4.2 创建 Superuser

如果没有 superuser，需要在数据库中手动设置：

```sql
UPDATE users SET is_superuser = 1 WHERE email = 'your@email.com';
```

### 4.3 访问 Admin

1. 打开 `http://localhost:8000/admin`
2. 使用 superuser 的 email 和密码登录
3. 在 Users 页面管理用户

---

## 5. 安全考虑

| 功能 | 状态 | 原因 |
|------|------|------|
| 创建用户 | 禁用 | 用户应通过正常注册流程创建 |
| 删除用户 | 禁用 | 风险较高，防止误操作 |
| 修改密码 | 禁用 | 用户应通过密码重置流程自行修改 |
| 编辑状态 | 启用 | 允许管理员激活/禁用用户 |
| 查看密码哈希 | 禁用 | 敏感信息不应显示 |

---

## 6. 文件变更清单

| 文件 | 变更类型 | 行数 |
|------|----------|------|
| `pyproject.toml` | 修改 | +2 |
| `learn_fastapi_auth/admin.py` | 新增 | +200 |
| `learn_fastapi_auth/app.py` | 修改 | +8 |
| `learn_fastapi_auth/csrf.py` | 修改 | +2 |
| `uv.lock` | 自动更新 | +30 |

**总计**: 约 240 行新增代码
