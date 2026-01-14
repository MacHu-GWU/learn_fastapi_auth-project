# Phase 4-2: Token Refresh - Code Walkthrough

本文档详细解释 Token 刷新机制的代码实现，帮助你理解并学会手写这些代码。

---

## 目录

1. [概念理解](#1-概念理解)
2. [配置管理](#2-配置管理)
3. [数据库模型](#3-数据库模型)
4. [核心模块实现](#4-核心模块实现)
5. [应用集成](#5-应用集成)
6. [单元测试](#6-单元测试)

---

## 1. 概念理解

### 为什么需要 Token 刷新？

单一 Token 机制的问题：

| Token 有效期 | 安全性 | 用户体验 |
|-------------|--------|---------|
| 短（15分钟）| 高 | 差（频繁重新登录）|
| 长（30天）| 低 | 好（长时间不用登录）|

**双 Token 机制解决这个矛盾**：

| Token 类型 | 有效期 | 存储位置 | 用途 |
|-----------|--------|----------|------|
| Access Token | 1 小时 | localStorage | API 请求认证 |
| Refresh Token | 7 天 | HttpOnly Cookie | 获取新 Access Token |

### Token 刷新流程

```
用户登录
    ↓
服务器返回 access_token (JSON) + refresh_token (Cookie)
    ↓
前端存储 access_token 到 localStorage
    ↓
前端用 access_token 调用 API
    ↓
1 小时后 access_token 过期
    ↓
前端调用 POST /api/auth/refresh
    ↓
服务器验证 Cookie 中的 refresh_token
    ↓
服务器返回新的 access_token
    ↓
前端更新 localStorage 中的 access_token
    ↓
用户无感知地继续使用
```

### 为什么 Refresh Token 存在 HttpOnly Cookie？

1. **HttpOnly**：JavaScript 无法读取，防止 XSS 攻击窃取 token
2. **自动发送**：浏览器自动在请求中携带 cookie
3. **可撤销**：存储在数据库中，可以随时使服务端失效

---

## 2. 配置管理

### 文件：`learn_fastapi_auth/config.py`

#### 添加配置字段

```python
@dataclasses.dataclass
class Config:
    # ... 其他字段 ...

    refresh_token_lifetime: int = dataclasses.field()

    # Refresh Token Cookie
    refresh_token_cookie_name: str = dataclasses.field()
    refresh_token_cookie_secure: bool = dataclasses.field()
    refresh_token_cookie_samesite: str = dataclasses.field()
```

#### 从环境变量读取

```python
refresh_token_lifetime=int(
    os.environ.get("REFRESH_TOKEN_LIFETIME", "604800")  # 7 days
),
# Refresh Token Cookie
refresh_token_cookie_name=os.environ.get(
    "REFRESH_TOKEN_COOKIE_NAME", "refresh_token"
),
refresh_token_cookie_secure=os.environ.get(
    "REFRESH_TOKEN_COOKIE_SECURE", "False"
).lower() == "true",
refresh_token_cookie_samesite=os.environ.get(
    "REFRESH_TOKEN_COOKIE_SAMESITE", "lax"
),
```

### 解释

1. **`refresh_token_lifetime`**：
   - 默认 604800 秒 = 7 天
   - 比 access_token（1小时）长很多

2. **Cookie 设置**：
   - `secure=False`：开发环境允许 HTTP
   - `samesite=lax`：防止 CSRF 攻击
   - 生产环境应设置 `secure=True`

---

## 3. 数据库模型

### 文件：`learn_fastapi_auth/models.py`

#### User 模型添加关系

```python
class User(SQLAlchemyBaseUserTableUUID, Base):
    # ... 其他字段 ...

    # 添加 refresh_tokens 关系
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
```

#### 新增 RefreshToken 模型

```python
class RefreshToken(Base):
    """
    Refresh token storage for token refresh mechanism.

    Stored in database for:
    - Validation on refresh requests
    - Revocation support (logout from all devices)
    - Token rotation (optional security enhancement)
    """

    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(String(500), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Relationship back to User
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
```

### 解释

1. **为什么存储在数据库？**
   - 可以随时撤销 token（登出、安全事件）
   - 可以查看用户有多少活跃会话
   - 可以实现"从所有设备登出"功能

2. **`cascade="all, delete-orphan"`**：
   - 删除用户时自动删除其所有 refresh tokens

3. **`ondelete="CASCADE"`**：
   - 数据库级别的级联删除

---

## 4. 核心模块实现

### 文件：`learn_fastapi_auth/refresh_token.py`

### 4.1 导入

```python
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import config
from .models import RefreshToken
```

### 4.2 生成 Refresh Token

```python
def generate_refresh_token() -> str:
    """
    Generate a secure random refresh token.
    """
    return secrets.token_urlsafe(48)
```

**解释**：

1. **`secrets.token_urlsafe(48)`**：
   - 生成 48 字节的随机数据
   - 编码为 URL 安全的 base64，得到 64 字符
   - 使用 `secrets` 模块而非 `random`，因为它是加密安全的

2. **为什么 48 字节？**
   - 48 * 8 = 384 位熵
   - 足够安全，无法被暴力破解

### 4.3 创建并存储 Token

```python
async def create_refresh_token(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> str:
    """
    Create and store a new refresh token for a user.
    """
    token_str = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=config.refresh_token_lifetime
    )

    refresh_token = RefreshToken(
        token=token_str,
        user_id=user_id,
        expires_at=expires_at,
    )
    session.add(refresh_token)
    await session.commit()

    return token_str
```

**解释**：

1. **流程**：
   - 生成随机 token
   - 计算过期时间
   - 创建数据库记录
   - 返回 token 字符串

2. **使用 UTC 时间**：
   - `datetime.now(timezone.utc)` 确保时区一致性
   - 避免时区相关的 bug

### 4.4 验证 Token

```python
async def validate_refresh_token(
    session: AsyncSession,
    token_str: str,
) -> Optional[uuid.UUID]:
    """
    Validate a refresh token and return the associated user ID.
    """
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token == token_str)
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token is None:
        return None

    # Handle both timezone-aware and naive datetimes
    now = datetime.now(timezone.utc)
    expires_at = refresh_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        # Token has expired, delete it
        await session.delete(refresh_token)
        await session.commit()
        return None

    return refresh_token.user_id
```

**解释**：

1. **返回值设计**：
   - 有效 token：返回 `user_id`
   - 无效 token：返回 `None`

2. **时区处理**：
   - SQLite 存储无时区的 datetime
   - 需要手动添加 UTC 时区进行比较

3. **自动清理**：
   - 发现过期 token 时自动删除
   - 减少数据库中的无效数据

### 4.5 撤销 Token

```python
async def revoke_refresh_token(
    session: AsyncSession,
    token_str: str,
) -> bool:
    """
    Revoke (delete) a specific refresh token.
    """
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token == token_str)
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token:
        await session.delete(refresh_token)
        await session.commit()
        return True

    return False
```

### 4.6 撤销用户所有 Token

```python
async def revoke_all_user_refresh_tokens(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> int:
    """
    Revoke all refresh tokens for a user.
    """
    result = await session.execute(
        delete(RefreshToken).where(RefreshToken.user_id == user_id)
    )
    await session.commit()
    return result.rowcount
```

**解释**：

- **使用场景**：
  - 用户点击"从所有设备登出"
  - 检测到安全事件（密码泄露等）
  - 用户修改密码后

### 4.7 Cookie 设置

```python
def get_refresh_token_cookie_settings() -> dict:
    """
    Get cookie settings for refresh token.
    """
    return {
        "key": config.refresh_token_cookie_name,
        "httponly": True,  # JavaScript cannot access
        "secure": config.refresh_token_cookie_secure,
        "samesite": config.refresh_token_cookie_samesite,
        "max_age": config.refresh_token_lifetime,
        "path": "/api/auth",  # Only send to auth endpoints
    }
```

**解释**：

1. **`httponly=True`**：
   - 最重要的安全设置
   - JavaScript 无法通过 `document.cookie` 读取
   - 防止 XSS 攻击窃取 token

2. **`path="/api/auth"`**：
   - 只有访问 `/api/auth/*` 时才发送 cookie
   - 减少不必要的 cookie 传输
   - 缩小攻击面

---

## 5. 应用集成

### 文件：`learn_fastapi_auth/app.py`

### 5.1 登录后设置 Cookie 的中间件

```python
@app.middleware("http")
async def add_refresh_token_on_login(request: Request, call_next):
    """
    Middleware to add refresh token cookie after successful login.
    """
    import json
    import jwt

    response = await call_next(request)

    # Only process POST to login endpoint with successful response
    if (
        request.url.path == "/api/auth/login"
        and request.method == "POST"
        and response.status_code == 200
    ):
        # Read the response body to get the access token
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body.decode())
            access_token = data.get("access_token")

            if access_token:
                # Decode JWT to get user_id
                payload = jwt.decode(
                    access_token, options={"verify_signature": False}
                )
                user_id = payload.get("sub")

                if user_id:
                    # Create refresh token
                    from .database import async_session_maker
                    import uuid

                    async with async_session_maker() as session:
                        refresh_token_str = await create_refresh_token(
                            session, uuid.UUID(user_id)
                        )

                    # Create new response with cookie
                    new_response = JSONResponse(
                        content=data,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                    )
                    cookie_settings = get_refresh_token_cookie_settings()
                    new_response.set_cookie(
                        value=refresh_token_str,
                        **cookie_settings,
                    )
                    return new_response
        except Exception:
            pass

        return JSONResponse(
            content=json.loads(body.decode()) if body else {},
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    return response
```

**解释**：

1. **为什么用中间件？**
   - fastapi-users 的登录路由是内置的
   - 我们无法直接修改它的行为
   - 中间件可以拦截并修改响应

2. **工作流程**：
   ```
   请求 → fastapi-users 登录 → 响应
                              ↓
                    中间件拦截响应
                              ↓
                    解析 access_token
                              ↓
                    从 JWT 获取 user_id
                              ↓
                    创建 refresh_token
                              ↓
                    设置 cookie 返回
   ```

3. **`verify_signature=False`**：
   - 我们只需要读取 JWT 的 payload
   - 不需要验证签名（已由 fastapi-users 验证）

### 5.2 刷新 Token 端点

```python
@app.post("/api/auth/refresh", response_model=TokenRefreshResponse, tags=["auth"])
@limiter.limit(config.rate_limit_default)
async def refresh_access_token(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a new access token using the refresh token.
    """
    from .auth.users import get_jwt_strategy
    from sqlalchemy import select
    from .models import User as UserModel

    # Get refresh token from cookie
    refresh_token = request.cookies.get(config.refresh_token_cookie_name)

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="REFRESH_TOKEN_MISSING",
        )

    # Validate refresh token
    user_id = await validate_refresh_token(session, refresh_token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="REFRESH_TOKEN_INVALID",
        )

    # Get user from database
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="USER_INACTIVE",
        )

    # Generate new access token
    jwt_strategy = get_jwt_strategy()
    access_token = await jwt_strategy.write_token(user)

    return TokenRefreshResponse(access_token=access_token)
```

**解释**：

1. **不需要 Bearer Token**：
   - 这个端点不需要认证
   - 只需要 cookie 中的 refresh_token

2. **验证步骤**：
   - 检查 cookie 是否存在
   - 验证 refresh_token（是否存在、是否过期）
   - 检查用户是否存在且活跃

3. **生成新 Access Token**：
   - 使用 fastapi-users 的 `JWTStrategy`
   - 保持与登录时相同的 token 格式

### 5.3 登出端点（更新）

```python
@app.post("/api/auth/logout", response_model=MessageResponse, tags=["auth"])
@limiter.limit(config.rate_limit_default)
async def logout(
    request: Request,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Logout user by revoking their refresh token.
    """
    refresh_token = request.cookies.get(config.refresh_token_cookie_name)

    if refresh_token:
        await revoke_refresh_token(session, refresh_token)

    response = JSONResponse(
        content={"message": "Successfully logged out"},
        status_code=200,
    )
    response.delete_cookie(
        key=config.refresh_token_cookie_name,
        path="/api/auth",
    )
    return response
```

**解释**：

1. **双重清理**：
   - 从数据库删除 refresh_token
   - 从浏览器删除 cookie

2. **`delete_cookie` 的 `path` 参数**：
   - 必须与设置时的 path 一致
   - 否则 cookie 不会被删除

### 5.4 从所有设备登出

```python
@app.post("/api/auth/logout-all", response_model=MessageResponse, tags=["auth"])
@limiter.limit(config.rate_limit_login)
async def logout_all_devices(
    request: Request,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Logout from all devices by revoking all refresh tokens.
    """
    count = await revoke_all_user_refresh_tokens(session, user.id)

    response = JSONResponse(
        content={
            "message": f"Successfully logged out from all devices. Revoked {count} sessions."
        },
        status_code=200,
    )
    response.delete_cookie(
        key=config.refresh_token_cookie_name,
        path="/api/auth",
    )
    return response
```

---

## 6. 单元测试

### 文件：`tests/test_refresh_token.py`

### 6.1 测试 Token 生成

```python
def test_generates_unique_tokens(self):
    """Test that each call generates a unique token."""
    tokens = [generate_refresh_token() for _ in range(100)]
    assert len(set(tokens)) == 100


def test_generates_url_safe_token(self):
    """Test that token is URL-safe."""
    token = generate_refresh_token()
    assert all(c.isalnum() or c in "-_" for c in token)
```

### 6.2 测试 Token 验证

```python
@pytest.mark.asyncio
async def test_returns_none_for_expired_token(self):
    """Test that expired token returns None and is deleted."""
    mock_session = AsyncMock()
    user_id = uuid.uuid4()

    # Create mock expired token
    mock_token = MagicMock()
    mock_token.user_id = user_id
    mock_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_token
    mock_session.execute.return_value = mock_result

    result = await validate_refresh_token(mock_session, "expired_token")

    assert result is None
    # Verify expired token was deleted
    mock_session.delete.assert_called_once_with(mock_token)
```

---

## 总结：实现流程

1. **添加配置**：refresh_token_lifetime 和 cookie 设置

2. **添加模型**：RefreshToken 表，存储 token 和过期时间

3. **创建模块**：
   - token 生成函数
   - 创建/验证/撤销函数
   - cookie 设置函数

4. **应用集成**：
   - 登录中间件设置 cookie
   - 刷新端点返回新 access_token
   - 登出端点清理 token

5. **编写测试**：验证各函数行为

---

## 关键知识点

1. **双 Token 机制**：
   - Access Token 短期（API 认证）
   - Refresh Token 长期（获取新 Access Token）

2. **HttpOnly Cookie**：
   - 防止 XSS 攻击
   - JavaScript 无法读取

3. **中间件模式**：
   - 拦截第三方库的响应
   - 添加自定义行为

4. **Token 撤销**：
   - 存储在数据库中才能撤销
   - 支持单个撤销和全部撤销

5. **Cookie Path**：
   - 限制 cookie 发送范围
   - 删除时必须指定相同 path

---

**文档完成于**: 2025-01
