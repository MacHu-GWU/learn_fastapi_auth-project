# Phase 4-2: CSRF Protection - Code Walkthrough

本文档详细解释 CSRF 保护功能的代码实现，帮助你理解并学会手写这些代码。

---

## 目录

1. [概念理解](#1-概念理解)
2. [添加依赖](#2-添加依赖)
3. [配置管理](#3-配置管理)
4. [核心模块实现](#4-核心模块实现)
5. [应用集成](#5-应用集成)
6. [模板使用](#6-模板使用)
7. [单元测试](#7-单元测试)

---

## 1. 概念理解

### 什么是 CSRF？

CSRF（Cross-Site Request Forgery，跨站请求伪造）是一种攻击方式，利用用户已认证的会话在用户不知情的情况下执行恶意操作。

### 攻击场景示例

1. 用户登录了银行网站 `bank.com`，浏览器保存了 cookie
2. 用户访问恶意网站 `evil.com`
3. `evil.com` 包含一个隐藏的表单，自动提交到 `bank.com/transfer`
4. 浏览器会自动携带 `bank.com` 的 cookie
5. 银行服务器无法区分这是用户的真实请求还是恶意请求

### Double Submit Cookie 模式

我们使用的 `starlette-csrf` 采用 Double Submit Cookie 模式：

```
1. 服务器生成随机 token，存入 cookie
2. 客户端提交时，必须从 cookie 读取 token 并放入请求头/表单
3. 服务器验证：请求中的 token == cookie 中的 token
4. 恶意网站无法读取 cookie（同源策略），所以无法伪造
```

### 为什么 Bearer Token API 不需要 CSRF 保护？

我们的 API 使用 JWT Bearer Token，存储在 localStorage 而不是 cookie：

1. 恶意网站无法访问 localStorage（同源策略）
2. 攻击者无法获取 JWT token
3. 没有 token，就无法调用 API

因此，我们将 `/api/*` 端点从 CSRF 保护中排除。

---

## 2. 添加依赖

### 文件：`pyproject.toml`

```toml
dependencies = [
    # ... 其他依赖 ...
    # CSRF Protection
    "starlette-csrf>=3.0.0,<4.0.0",  # CSRF protection middleware
]
```

### 解释

`starlette-csrf` 是专为 Starlette/FastAPI 设计的 CSRF 中间件：
- 自动设置 CSRF cookie
- 验证 POST/PUT/DELETE/PATCH 请求的 token
- 支持排除特定 URL
- 支持正则表达式匹配

---

## 3. 配置管理

### 文件：`learn_fastapi_auth/config.py`

#### 添加配置字段

```python
@dataclasses.dataclass
class Config:
    # ... 其他字段 ...

    # CSRF Protection
    csrf_cookie_name: str = dataclasses.field()
    csrf_cookie_secure: bool = dataclasses.field()
    csrf_cookie_samesite: str = dataclasses.field()
```

#### 从环境变量读取

```python
@classmethod
def from_env(cls) -> "Config":
    return cls(
        # ... 其他配置 ...

        # CSRF Protection
        csrf_cookie_name=os.environ.get("CSRF_COOKIE_NAME", "csrftoken"),
        csrf_cookie_secure=os.environ.get("CSRF_COOKIE_SECURE", "False").lower()
        == "true",
        csrf_cookie_samesite=os.environ.get("CSRF_COOKIE_SAMESITE", "lax"),
    )
```

### 解释

1. **`csrf_cookie_name`**：
   - Cookie 的名称
   - 默认 `csrftoken`（和 Django 保持一致）

2. **`csrf_cookie_secure`**：
   - 设为 `True` 时，cookie 只通过 HTTPS 发送
   - 开发环境默认 `False`
   - **生产环境应设为 `True`**

3. **`csrf_cookie_samesite`**：
   - `lax`：大多数情况下阻止跨站发送
   - `strict`：完全阻止跨站发送
   - `none`：允许跨站发送（需要 `secure=True`）

---

## 4. 核心模块实现

### 文件：`learn_fastapi_auth/csrf.py`

### 4.1 导入

```python
import re
from typing import List, Optional, Set

from fastapi import Request
from starlette_csrf import CSRFMiddleware

from .config import config
```

### 4.2 获取 CSRF Token

```python
def get_csrf_token(request: Request) -> Optional[str]:
    """Get CSRF token from request cookies."""
    return request.cookies.get(config.csrf_cookie_name)
```

**解释**：

1. **用途**：在 Jinja2 模板中获取 token 用于表单
2. **实现简单**：直接从 cookie 读取
3. **返回 `Optional[str]`**：可能不存在（首次访问）

### 4.3 创建排除模式

```python
def create_csrf_exempt_patterns() -> List[re.Pattern]:
    """Create regex patterns for URLs exempt from CSRF protection."""
    exempt_patterns = [
        # API endpoints using Bearer token auth are already protected
        re.compile(r"^/api/.*"),
        # Health check doesn't need CSRF
        re.compile(r"^/health$"),
        # Static files don't need CSRF
        re.compile(r"^/static/.*"),
        # API docs don't need CSRF (GET requests)
        re.compile(r"^/docs.*"),
        re.compile(r"^/redoc.*"),
        re.compile(r"^/openapi\.json$"),
    ]
    return exempt_patterns
```

**解释**：

1. **正则表达式**：
   - `^` 表示开头
   - `.*` 匹配任意字符
   - `$` 表示结尾
   - `\.` 匹配字面点号

2. **排除的 URL**：
   - `/api/*`：使用 Bearer Token，不需要 CSRF
   - `/health`：健康检查，不改变状态
   - `/static/*`：静态文件
   - `/docs*`, `/redoc*`, `/openapi.json`：API 文档（只有 GET）

3. **为什么返回编译后的模式？**
   - `re.compile()` 预编译，提高性能
   - 中间件每次请求都会匹配，预编译很重要

### 4.4 创建必须保护的模式

```python
def create_csrf_required_patterns() -> Optional[List[re.Pattern]]:
    """Create regex patterns for URLs that require CSRF protection."""
    # Return None to protect all non-exempt URLs
    return None
```

**解释**：

1. **返回 `None`**：保护所有非排除的 URL
2. **可选设计**：如果只想保护特定 URL，可以返回模式列表

### 4.5 设置 CSRF 保护

```python
def setup_csrf_protection(app, secret: str) -> None:
    """Configure CSRF protection for a FastAPI application."""
    app.add_middleware(
        CSRFMiddleware,
        secret=secret,
        exempt_urls=create_csrf_exempt_patterns(),
        required_urls=create_csrf_required_patterns(),
        cookie_name=config.csrf_cookie_name,
        cookie_secure=config.csrf_cookie_secure,
        cookie_samesite=config.csrf_cookie_samesite,
        cookie_httponly=False,
        header_name="x-csrftoken",
    )
```

**解释**：

1. **`secret`**：
   - 用于签名 CSRF token
   - 应使用应用的 SECRET_KEY

2. **`cookie_httponly=False`**：
   - 允许 JavaScript 读取 cookie
   - 这是必须的，因为 AJAX 请求需要读取 token

3. **`header_name`**：
   - AJAX 请求中携带 token 的头名称
   - 使用小写 `x-csrftoken`

4. **中间件工作流程**：
   ```
   请求进入 → 检查是否排除 URL
             ↓ 是 → 直接通过
             ↓ 否 → 检查是否安全方法（GET/HEAD/OPTIONS）
                   ↓ 是 → 设置 cookie，通过
                   ↓ 否 → 验证 token → 通过/403
   ```

### 4.6 辅助函数

```python
def get_csrf_header_name() -> str:
    """Get the header name for CSRF token."""
    return "x-csrftoken"


def get_csrf_cookie_name() -> str:
    """Get the cookie name for CSRF token."""
    return config.csrf_cookie_name
```

**解释**：

1. **为什么有这些函数？**
   - 前端 JavaScript 需要知道使用什么头/cookie 名
   - 提供统一接口，避免硬编码

---

## 5. 应用集成

### 文件：`learn_fastapi_auth/app.py`

### 5.1 导入

```python
from .csrf import get_csrf_token, setup_csrf_protection
```

### 5.2 设置 CSRF 保护

```python
app = FastAPI(...)

# Setup CSRF protection
# Note: API endpoints using Bearer token auth are exempt from CSRF checks
setup_csrf_protection(app, config.secret_key)
```

**解释**：

1. **中间件顺序很重要**：
   - CSRF 中间件应该在其他中间件之前添加
   - 这样可以尽早拦截恶意请求

2. **注释说明**：
   - 说明 API 端点为什么被排除
   - 帮助其他开发者理解设计决策

### 5.3 添加到模板全局变量

```python
# Jinja2 templates
templates = Jinja2Templates(directory=str(dir_templates))

# Add CSRF token function to Jinja2 globals for use in templates
templates.env.globals["get_csrf_token"] = get_csrf_token
```

**解释**：

1. **`templates.env.globals`**：
   - Jinja2 的全局变量
   - 所有模板都可以访问

2. **使用方式**：
   ```html
   {{ get_csrf_token(request) }}
   ```

---

## 6. 模板使用

### HTML 表单示例

```html
<form method="POST" action="/some-endpoint">
    <!-- CSRF token hidden field -->
    <input type="hidden" name="csrftoken" value="{{ get_csrf_token(request) }}">

    <!-- 其他表单字段 -->
    <input type="text" name="username">
    <button type="submit">Submit</button>
</form>
```

### JavaScript AJAX 示例

```javascript
// 从 cookie 获取 CSRF token
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// 发送 POST 请求
fetch('/some-endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')  // 注意大小写
    },
    body: JSON.stringify(data)
});
```

**注意**：
- 请求头名称大小写不敏感
- `X-CSRFToken` 和 `x-csrftoken` 都可以

---

## 7. 单元测试

### 文件：`tests/test_csrf.py`

### 7.1 测试 Token 获取

```python
from unittest.mock import MagicMock

def test_returns_token_when_present(self):
    """Test that CSRF token is returned when present in cookies."""
    mock_request = MagicMock()
    mock_request.cookies = {"csrftoken": "test-token-123"}

    result = get_csrf_token(mock_request)

    assert result == "test-token-123"


def test_returns_none_when_missing(self):
    """Test that None is returned when CSRF token is not in cookies."""
    mock_request = MagicMock()
    mock_request.cookies = {}

    result = get_csrf_token(mock_request)

    assert result is None
```

**解释**：

1. **Mock 对象**：
   - 使用 `MagicMock` 模拟 Request 对象
   - 只需要设置 `cookies` 属性

2. **测试两种情况**：
   - Cookie 存在：返回 token
   - Cookie 不存在：返回 None

### 7.2 测试排除模式

```python
def test_api_routes_are_exempt(self):
    """Test that /api/* routes are marked as exempt."""
    patterns = create_csrf_exempt_patterns()

    test_urls = [
        "/api/auth/login",
        "/api/auth/register",
        "/api/users/me",
    ]

    for url in test_urls:
        matches = any(p.match(url) for p in patterns)
        assert matches, f"Expected {url} to be exempt"


def test_page_routes_are_not_exempt(self):
    """Test that HTML page routes are NOT marked as exempt."""
    patterns = create_csrf_exempt_patterns()

    test_urls = [
        "/signin",
        "/signup",
        "/app",
    ]

    for url in test_urls:
        matches = any(p.match(url) for p in patterns)
        assert not matches, f"Expected {url} to NOT be exempt"
```

**解释**：

1. **正向测试**：
   - API 路由应该被排除

2. **反向测试**：
   - 页面路由不应该被排除
   - 确保我们没有意外排除需要保护的 URL

---

## 总结：实现流程

1. **添加依赖**：在 `pyproject.toml` 添加 `starlette-csrf`

2. **添加配置**：在 `config.py` 定义 cookie 设置

3. **创建模块**：
   - 获取 token 函数
   - 排除/必须保护模式
   - 设置函数
   - 辅助函数

4. **集成到应用**：
   - 调用设置函数
   - 添加到 Jinja2 全局变量

5. **编写测试**：
   - 测试 token 获取
   - 测试 URL 模式匹配

---

## 关键知识点

1. **CSRF vs API Token**：
   - CSRF 保护用于 cookie 认证的表单
   - API 使用 Bearer Token，不需要 CSRF

2. **Double Submit Cookie**：
   - Token 在 cookie 和请求中都出现
   - 服务器验证两者一致
   - 攻击者无法读取 cookie，所以无法伪造

3. **Cookie 设置**：
   - `httponly=False`：必须，否则 JS 无法读取
   - `secure=True`：生产环境必须
   - `samesite=lax`：基本保护

4. **中间件配置**：
   - 正确设置排除模式
   - 使用相同的 secret key
   - 理解中间件顺序

---

**文档完成于**: 2025-01
