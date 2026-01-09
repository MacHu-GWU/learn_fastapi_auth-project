# Phase 4.3: 记住登录状态 (Remember Me) - 代码详解

本文档详细解释实现 "记住我" 功能的每一处代码改动。目标是帮助你理解这个功能是如何工作的，以便你能够自己手写类似的代码。

---

## 概述：Remember Me 是如何工作的

"记住我" 功能将用户的登录会话从 7 天延长到 30 天。关键点在于：

**我们不改变 access token 的有效期。** Access token 保持短期有效（1小时）以确保安全性。我们改变的是 **refresh token** 的有效期：

- **不勾选 Remember Me**：Refresh token 7 天后过期
- **勾选 Remember Me**：Refresh token 30 天后过期

Refresh token 存储在 HttpOnly cookie 中。只要这个 cookie 有效，用户就可以自动获取新的 access token，无需重新登录。

---

## 文件 1: `config.py` - 配置管理

### 改动内容

添加了一个新的配置字段，用于存储 Remember Me 的 token 有效期。

### 代码改动

```python
# 在 Config dataclass 中添加这个字段：
remember_me_refresh_token_lifetime: int = dataclasses.field()

# 在 from_env() 方法中添加这一行：
remember_me_refresh_token_lifetime=int(
    os.environ.get("REMEMBER_ME_REFRESH_TOKEN_LIFETIME", "2592000")  # 30 天
),
```

### 解释

- `2592000` = 30 天的秒数 (30 * 24 * 60 * 60)
- 这个值可以通过环境变量覆盖
- 默认是 30 天，而普通的 refresh token 是 7 天 (604800 秒)

### 为什么用这种方式？

集中配置使得：
1. 无需修改代码就能改变有效期
2. 开发环境和生产环境可以使用不同的值
3. 开发时可以用更短的有效期来测试

---

## 文件 2: `refresh_token.py` - Token 创建模块

### 改动内容

修改了两个函数，使它们接受可选的 `lifetime_seconds` 参数。

### 改动 1: `create_refresh_token()`

**修改前：**
```python
async def create_refresh_token(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> str:
    token_str = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=config.refresh_token_lifetime  # 始终是 7 天
    )
```

**修改后：**
```python
async def create_refresh_token(
    session: AsyncSession,
    user_id: uuid.UUID,
    lifetime_seconds: Optional[int] = None,  # 新增：可选参数
) -> str:
    token_str = generate_refresh_token()
    # 新增：如果提供了自定义有效期就使用它，否则使用默认值
    actual_lifetime = lifetime_seconds if lifetime_seconds is not None else config.refresh_token_lifetime
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=actual_lifetime
    )
```

### 改动 2: `get_refresh_token_cookie_settings()`

**修改前：**
```python
def get_refresh_token_cookie_settings() -> dict:
    return {
        "key": config.refresh_token_cookie_name,
        "httponly": True,
        "secure": config.refresh_token_cookie_secure,
        "samesite": config.refresh_token_cookie_samesite,
        "max_age": config.refresh_token_lifetime,  # 始终是 7 天
        "path": "/api/auth",
    }
```

**修改后：**
```python
def get_refresh_token_cookie_settings(lifetime_seconds: Optional[int] = None) -> dict:
    # 新增：如果提供了自定义有效期就使用它
    actual_lifetime = lifetime_seconds if lifetime_seconds is not None else config.refresh_token_lifetime
    return {
        "key": config.refresh_token_cookie_name,
        "httponly": True,
        "secure": config.refresh_token_cookie_secure,
        "samesite": config.refresh_token_cookie_samesite,
        "max_age": actual_lifetime,  # 使用计算后的有效期
        "path": "/api/auth",
    }
```

### 关键模式：带默认值的可选参数

```python
def function(lifetime_seconds: Optional[int] = None):
    actual_value = lifetime_seconds if lifetime_seconds is not None else config.default_value
```

这种模式的好处：
1. **向后兼容**：不传参数的旧代码仍然可以正常工作
2. **灵活性**：新代码可以传入自定义值
3. **显式处理 None**：我们用 `is not None` 而不是直接判断真假，因为 `0` 是一个有效的整数

---

## 文件 3: `signin.html` - 前端登录表单

### 改动内容

添加了一个复选框，并修改 JavaScript 来发送 `remember_me` 参数。

### HTML 改动

```html
<!-- 在密码输入框和提交按钮之间添加 -->
<div class="form-group-checkbox">
    <input type="checkbox" id="remember-me" name="remember_me">
    <label for="remember-me">Remember me for 30 days</label>
</div>
```

### JavaScript 改动

**修改前：**
```javascript
const email = document.getElementById('email').value.trim();
const password = document.getElementById('password').value;
// ... 验证逻辑 ...
const formData = new URLSearchParams();
formData.append('username', email);
formData.append('password', password);
```

**修改后：**
```javascript
const email = document.getElementById('email').value.trim();
const password = document.getElementById('password').value;
const rememberMe = document.getElementById('remember-me').checked;  // 新增：获取复选框状态
// ... 验证逻辑 ...
const formData = new URLSearchParams();
formData.append('username', email);
formData.append('password', password);
formData.append('remember_me', rememberMe ? 'true' : 'false');  // 新增：添加到表单数据
```

### 关键概念

1. **复选框的 `.checked` 属性**：返回 `true` 或 `false`
2. **三元运算符**：`rememberMe ? 'true' : 'false'` 将布尔值转换为字符串
3. **URLSearchParams**：用于 OAuth2 密码流（form-urlencoded 格式）

---

## 文件 4: `style.css` - 复选框样式

### 添加的内容

```css
/* Remember Me 复选框样式 */
.form-group-checkbox {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
}

.form-group-checkbox input[type="checkbox"] {
    width: auto;           /* 不要把复选框拉伸到全宽 */
    margin-right: 10px;    /* 复选框和标签之间的间距 */
    cursor: pointer;       /* 显示手型光标 */
}

.form-group-checkbox label {
    display: inline;       /* 让标签和复选框在同一行 */
    margin-bottom: 0;      /* 移除默认的标签下边距 */
    font-weight: normal;   /* 正常字重（不加粗） */
    cursor: pointer;       /* 点击标签也能切换复选框 */
    user-select: none;     /* 防止点击时选中文本 */
}
```

### 关键 CSS 概念

- `display: flex` + `align-items: center`：垂直居中复选框和标签
- 在两个元素上都设置 `cursor: pointer`：表明可点击
- 标签上的 `user-select: none`：防止意外选中文本，提升用户体验

---

## 文件 5: `app.py` - 登录中间件

这是最复杂的改动。中间件拦截登录请求和响应。

### 面临的挑战

登录端点由 `fastapi-users` 处理，我们不能直接修改它。因此，我们使用中间件来：
1. 在请求被处理之前读取表单数据
2. 在登录成功之后修改响应

### 完整的改动代码

```python
@app.middleware("http")
async def add_refresh_token_on_login(request: Request, call_next):
    """
    登录成功后添加 refresh token cookie 的中间件。

    支持 "记住我" 功能：
    - 如果 remember_me=true：refresh token 有效期 30 天
    - 如果 remember_me=false（默认）：refresh token 有效期 7 天
    """
    import json
    import jwt

    # === 第一步：在处理请求之前从请求中提取 remember_me ===
    remember_me = False
    if request.url.path == "/api/auth/login" and request.method == "POST":
        # 读取原始请求体
        body_bytes = await request.body()

        # 解析表单数据以获取 remember_me 参数
        try:
            from urllib.parse import parse_qs
            form_data = parse_qs(body_bytes.decode())
            remember_me_values = form_data.get("remember_me", ["false"])
            remember_me = remember_me_values[0].lower() == "true"
        except Exception:
            pass

        # 重要：重新创建请求，使请求体可以被路由再次读取
        async def receive():
            return {"type": "http.request", "body": body_bytes}
        request = Request(request.scope, receive, request._send)

    # === 第二步：正常处理请求 ===
    response = await call_next(request)

    # === 第三步：如果登录成功，添加正确有效期的 refresh token ===
    if (
        request.url.path == "/api/auth/login"
        and request.method == "POST"
        and response.status_code == 200
    ):
        # 读取响应体
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body.decode())
            access_token = data.get("access_token")

            if access_token:
                # 解码 JWT 获取 user_id
                payload = jwt.decode(access_token, options={"verify_signature": False})
                user_id = payload.get("sub")

                if user_id:
                    from .database import async_session_maker
                    import uuid

                    # 核心逻辑：根据 remember_me 选择有效期
                    token_lifetime = (
                        config.remember_me_refresh_token_lifetime  # 30 天
                        if remember_me
                        else config.refresh_token_lifetime  # 7 天
                    )

                    # 使用选定的有效期创建 refresh token
                    async with async_session_maker() as session:
                        refresh_token_str = await create_refresh_token(
                            session, uuid.UUID(user_id), token_lifetime
                        )

                    # 创建带有 cookie 的响应（也使用正确的有效期）
                    new_response = JSONResponse(
                        content=data,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                    )
                    cookie_settings = get_refresh_token_cookie_settings(token_lifetime)
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

### 关键概念详解

#### 1. 两次读取请求体

在 ASGI 中，请求体只能读取一次。但我们需要：
1. 读取它来获取 `remember_me`
2. 让 `fastapi-users` 读取它来获取用户名/密码

解决方案：缓存请求体并创建新的 `receive` 函数：

```python
body_bytes = await request.body()  # 读取一次

async def receive():
    return {"type": "http.request", "body": body_bytes}  # 返回缓存的内容

request = Request(request.scope, receive, request._send)  # 新的请求对象
```

#### 2. 解析表单数据

OAuth2 密码流以 `application/x-www-form-urlencoded` 格式发送数据：

```
username=user@example.com&password=secret&remember_me=true
```

我们使用 `urllib.parse.parse_qs` 来解析：

```python
from urllib.parse import parse_qs
form_data = parse_qs(body_bytes.decode())
# 结果: {"username": ["user@example.com"], "password": ["secret"], "remember_me": ["true"]}
```

注意：`parse_qs` 返回的是列表，因为 URL 参数可以出现多次。我们取 `[0]` 来获取第一个值。

#### 3. 条件选择有效期

```python
token_lifetime = (
    config.remember_me_refresh_token_lifetime  # 30 天
    if remember_me
    else config.refresh_token_lifetime  # 7 天
)
```

这个三元表达式等价于：

```python
if remember_me:
    token_lifetime = config.remember_me_refresh_token_lifetime
else:
    token_lifetime = config.refresh_token_lifetime
```

---

## 文件 6: 单元测试 (`test_refresh_token.py`)

### `create_refresh_token` 的测试

```python
@pytest.mark.asyncio
async def test_creates_token_with_custom_lifetime(self):
    """测试函数使用自定义有效期创建 token（Remember Me 场景）。"""
    from learn_fastapi_auth.models import RefreshToken

    mock_session = AsyncMock()
    user_id = uuid.uuid4()
    custom_lifetime = 2592000  # 30 天（秒）

    await create_refresh_token(mock_session, user_id, lifetime_seconds=custom_lifetime)

    # 获取传递给 session.add 的 RefreshToken 对象
    call_args = mock_session.add.call_args
    refresh_token = call_args[0][0]

    # 验证使用了正确的有效期
    expected_expires = datetime.now(timezone.utc) + timedelta(seconds=custom_lifetime)
    assert abs((refresh_token.expires_at - expected_expires).total_seconds()) < 5
```

### `get_refresh_token_cookie_settings` 的测试

```python
def test_custom_lifetime_sets_max_age(self):
    """测试自定义有效期参数正确设置 max_age。"""
    custom_lifetime = 2592000  # 30 天

    settings = get_refresh_token_cookie_settings(lifetime_seconds=custom_lifetime)
    assert settings["max_age"] == custom_lifetime

def test_remember_me_lifetime_longer_than_default(self):
    """测试 Remember Me 有效期比默认值更长。"""
    from learn_fastapi_auth.config import config

    default_settings = get_refresh_token_cookie_settings()
    remember_me_settings = get_refresh_token_cookie_settings(
        lifetime_seconds=config.remember_me_refresh_token_lifetime
    )

    assert remember_me_settings["max_age"] > default_settings["max_age"]
```

### 测试的关键概念

1. **Mock 对象**：`AsyncMock()` 模拟数据库会话
2. **捕获调用参数**：`mock_session.add.call_args[0][0]` 获取传给 `add()` 的对象
3. **时间容差**：允许 5 秒的误差，因为测试执行需要时间
4. **比较测试**：验证 Remember Me 有效期 > 默认有效期

---

## 总结：数据流程

1. **用户勾选 "记住我" 复选框** 在登录页面
2. **前端添加 `remember_me=true`** 到表单数据
3. **中间件读取表单数据** 在登录处理之前
4. **fastapi-users 验证凭据** 并创建 access token
5. **中间件拦截成功响应** 并且：
   - 创建 30 天有效期的 refresh token（如果未勾选则是 7 天）
   - 设置相应 `max_age` 的 cookie
6. **用户的浏览器存储 cookie** 30 天（或 7 天）
7. **当 access token 过期时**，前端调用 `/api/auth/refresh`
8. **后端验证 refresh token** 并签发新的 access token
9. **用户保持登录状态**，无需重新输入凭据

---

## 值得记住的常用模式

### 1. 带默认值的可选参数
```python
def func(param: Optional[int] = None):
    value = param if param is not None else default_value
```

### 2. 用于前/后处理的中间件
```python
@app.middleware("http")
async def my_middleware(request: Request, call_next):
    # 处理前的逻辑
    response = await call_next(request)
    # 处理后的逻辑
    return response
```

### 3. 重复读取请求体
```python
body = await request.body()
async def receive():
    return {"type": "http.request", "body": body}
new_request = Request(request.scope, receive, request._send)
```

### 4. 三元条件表达式
```python
result = value_if_true if condition else value_if_false
```

---

**文档版本**: 1.0
**创建日期**: 2025-01-09
