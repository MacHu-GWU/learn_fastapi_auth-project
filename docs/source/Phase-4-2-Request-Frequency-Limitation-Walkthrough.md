# Phase 4-2: Request Frequency Limitation - Code Walkthrough

本文档详细解释请求频率限制功能的代码实现，帮助你理解并学会手写这些代码。

---

## 目录

1. [概念理解](#1-概念理解)
2. [添加依赖](#2-添加依赖)
3. [配置管理](#3-配置管理)
4. [核心模块实现](#4-核心模块实现)
5. [应用集成](#5-应用集成)
6. [测试适配](#6-测试适配)
7. [单元测试](#7-单元测试)

---

## 1. 概念理解

### 什么是 Rate Limiting？

Rate Limiting（请求频率限制）是一种安全机制，限制单个客户端在特定时间内可以发送的请求数量。

### 为什么需要它？

1. **防止暴力破解**：攻击者无法快速尝试大量密码
2. **防止 DDoS**：阻止恶意请求占用服务器资源
3. **防止滥用**：保护 API 不被过度调用

### 限制格式

```
<count>/<period>
```

例如：
- `5/minute`：每分钟最多 5 次请求
- `10/hour`：每小时最多 10 次请求
- `100/day`：每天最多 100 次请求

---

## 2. 添加依赖

### 文件：`pyproject.toml`

```toml
dependencies = [
    # ... 其他依赖 ...
    # Rate Limiting
    "slowapi>=0.1.9,<1.0.0",  # Request rate limiting
]
```

### 解释

`slowapi` 是一个基于 Flask-Limiter 的 FastAPI 扩展，提供：
- 装饰器方式添加限制 (`@limiter.limit()`)
- 中间件支持
- 内存/Redis 存储选项

安装后，它会自动安装 `limits` 库，用于解析限制字符串。

---

## 3. 配置管理

### 文件：`learn_fastapi_auth/config.py`

#### 添加配置字段

```python
@dataclasses.dataclass
class Config:
    # ... 其他字段 ...

    # Rate Limiting
    rate_limit_login: str = dataclasses.field()
    rate_limit_register: str = dataclasses.field()
    rate_limit_forgot_password: str = dataclasses.field()
    rate_limit_default: str = dataclasses.field()
```

#### 从环境变量读取

```python
@classmethod
def from_env(cls) -> "Config":
    return cls(
        # ... 其他配置 ...

        # Rate Limiting (default values follow common security practices)
        rate_limit_login=os.environ.get("RATE_LIMIT_LOGIN", "5/minute"),
        rate_limit_register=os.environ.get("RATE_LIMIT_REGISTER", "10/hour"),
        rate_limit_forgot_password=os.environ.get(
            "RATE_LIMIT_FORGOT_PASSWORD", "3/hour"
        ),
        rate_limit_default=os.environ.get("RATE_LIMIT_DEFAULT", "60/minute"),
    )
```

### 解释

1. **为什么使用配置类？**
   - 集中管理所有配置
   - 支持环境变量覆盖
   - 提供合理的默认值

2. **默认值的选择**：
   - 登录 5/分钟：防止密码暴力破解
   - 注册 10/小时：防止垃圾注册
   - 密码重置 3/小时：防止邮件轰炸
   - 默认 60/分钟：适合普通 API 使用

---

## 4. 核心模块实现

### 文件：`learn_fastapi_auth/ratelimit.py`

这是最核心的部分，让我们逐段分析。

### 4.1 导入和异常定义

```python
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from limits import parse
from limits.storage import MemoryStorage
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


class PathRateLimitExceeded(Exception):
    """Exception raised when path-based rate limit is exceeded."""

    def __init__(self, limit_string: str):
        self.limit_string = limit_string
        super().__init__(f"Rate limit exceeded: {limit_string}")
```

**解释**：

1. **为什么需要自定义异常？**
   - `slowapi` 的 `RateLimitExceeded` 需要 `Limit` 对象
   - 我们的路径检查使用字符串，所以创建简单的自定义异常

2. **异常设计**：
   - 存储 `limit_string` 以便在响应中使用
   - 继承 `Exception`，可以被 FastAPI 异常处理器捕获

### 4.2 获取客户端 IP

```python
def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for X-Forwarded-For header (set by reverse proxies like nginx)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # The first one is the original client IP
        return forwarded_for.split(",")[0].strip()

    # Fall back to the direct remote address
    return get_remote_address(request)
```

**解释**：

1. **为什么检查 X-Forwarded-For？**
   - 当应用部署在 nginx/负载均衡后面时，`request.client.host` 是代理的 IP
   - 真实客户端 IP 在 `X-Forwarded-For` 头中

2. **多个 IP 的情况**：
   ```
   X-Forwarded-For: client_ip, proxy1_ip, proxy2_ip
   ```
   第一个是原始客户端 IP，后面是经过的代理

3. **`strip()` 的作用**：
   - 移除可能的空格，确保 IP 格式正确

### 4.3 创建限制器和存储

```python
# Create the limiter instance with custom key function
limiter = Limiter(key_func=get_client_ip)

# Storage for path-based rate limiting (used for fastapi-users routes)
_path_storage = MemoryStorage()
```

**解释**：

1. **`limiter`**：用于 `@limiter.limit()` 装饰器
2. **`_path_storage`**：用于中间件的路径检查
3. **为什么两个？**
   - 装饰器和中间件使用不同的机制
   - 分开管理更清晰

### 4.4 重置存储函数

```python
def reset_rate_limit_storage():
    """Reset the rate limit storage for testing."""
    global _path_storage
    _path_storage = MemoryStorage()
```

**解释**：

1. **为什么需要这个？**
   - 测试之间需要隔离
   - 防止一个测试的请求影响另一个测试

2. **`global` 关键字**：
   - 允许函数修改模块级别的变量

### 4.5 路径限制检查

```python
def check_path_rate_limit(
    request: Request,
    limit_string: str,
    path_identifier: str,
) -> bool:
    """Check rate limit for a specific path."""
    client_ip = get_client_ip(request)
    # Create a unique key combining client IP and path
    key = f"{path_identifier}:{client_ip}"

    # Parse the limit string
    rate_limit = parse(limit_string)

    # Try to acquire an entry
    if not _path_storage.acquire_entry(key, rate_limit.amount, rate_limit.get_expiry()):
        raise PathRateLimitExceeded(limit_string)

    return True
```

**解释**：

1. **Key 的设计**：
   ```
   /api/auth/login:192.168.1.1
   ```
   - 组合路径和 IP，确保不同路径/IP 有独立计数

2. **`parse()` 函数**：
   - 将 `"5/minute"` 解析为 `RateLimitItem` 对象
   - 包含 `amount`（数量）和 `get_expiry()`（过期时间）

3. **`acquire_entry()` 方法**：
   - 尝试获取一个"名额"
   - 返回 `True`：成功，请求可以继续
   - 返回 `False`：已超限

### 4.6 异常处理器

```python
async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """Handler for slowapi decorator rate limit errors."""
    detail = str(exc.detail) if hasattr(exc, "detail") else "Rate limit exceeded"

    response = JSONResponse(
        status_code=429,
        content={
            "detail": "RATE_LIMIT_EXCEEDED",
            "message": f"Too many requests. {detail}",
        },
    )
    return response


async def path_rate_limit_exceeded_handler(
    request: Request,
    exc: PathRateLimitExceeded,
) -> JSONResponse:
    """Handler for path-based rate limit errors."""
    response = JSONResponse(
        status_code=429,
        content={
            "detail": "RATE_LIMIT_EXCEEDED",
            "message": f"Too many requests. Limit: {exc.limit_string}",
        },
    )
    return response
```

**解释**：

1. **HTTP 429 状态码**：
   - "Too Many Requests" 的标准响应码
   - 客户端应该理解并等待后重试

2. **两个处理器**：
   - `rate_limit_exceeded_handler`：处理 `@limiter.limit()` 装饰器的异常
   - `path_rate_limit_exceeded_handler`：处理中间件的异常

3. **响应格式设计**：
   - `detail`：机器可读的错误码
   - `message`：人类可读的信息

### 4.7 路径限制中间件

```python
def create_path_rate_limit_middleware(
    path_limits: dict[str, str],
) -> Callable:
    """Create middleware for path-based rate limiting."""

    async def middleware(request: Request, call_next):
        """Apply rate limiting based on request path."""
        path = request.url.path

        # Check if this path matches any rate limit rules
        for path_prefix, limit_string in path_limits.items():
            if path.startswith(path_prefix):
                try:
                    check_path_rate_limit(request, limit_string, path_prefix)
                except PathRateLimitExceeded as exc:
                    return await path_rate_limit_exceeded_handler(request, exc)
                break

        return await call_next(request)

    return middleware
```

**解释**：

1. **工厂函数模式**：
   - `create_path_rate_limit_middleware` 返回一个中间件函数
   - 允许通过参数配置不同的路径限制

2. **中间件工作流程**：
   ```
   请求进入 → 检查路径是否匹配 → 检查限制 → 通过则继续 / 超限则返回 429
   ```

3. **`path.startswith()`**：
   - 简单的路径匹配
   - `/api/auth/login` 匹配 `/api/auth/login`
   - 也会匹配 `/api/auth/login/something`（如果存在）

4. **`break` 的作用**：
   - 一个路径只匹配一个规则
   - 找到后不再继续检查

### 4.8 应用设置函数

```python
def setup_rate_limiting(app):
    """Configure rate limiting for a FastAPI application."""
    # Store limiter in app state
    app.state.limiter = limiter

    # Register exception handlers
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_exception_handler(PathRateLimitExceeded, path_rate_limit_exceeded_handler)
```

**解释**：

1. **`app.state.limiter`**：
   - `slowapi` 需要从 app.state 获取 limiter
   - 这是 slowapi 的约定

2. **异常处理器注册**：
   - FastAPI 在遇到对应异常时会调用这些处理器
   - 返回统一格式的 429 响应

---

## 5. 应用集成

### 文件：`learn_fastapi_auth/app.py`

### 5.1 导入

```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .ratelimit import (
    create_path_rate_limit_middleware,
    limiter,
    rate_limit_exceeded_handler,
    setup_rate_limiting,
)
```

### 5.2 设置 rate limiting

```python
app = FastAPI(...)

# Setup rate limiting
setup_rate_limiting(app)
app.add_middleware(SlowAPIMiddleware)

# Add path-based rate limiting for fastapi-users routes
path_rate_limits = {
    "/api/auth/login": config.rate_limit_login,
    "/api/auth/register": config.rate_limit_register,
    "/api/auth/forgot-password": config.rate_limit_forgot_password,
}
app.middleware("http")(create_path_rate_limit_middleware(path_rate_limits))
```

**解释**：

1. **中间件顺序**：
   - `SlowAPIMiddleware` 用于装饰器方式的限制
   - 路径中间件用于 fastapi-users 的路由

2. **为什么 fastapi-users 需要中间件？**
   - fastapi-users 的路由通过 `include_router` 添加
   - 我们无法直接在它们上面加装饰器
   - 中间件在请求到达路由之前就进行检查

### 5.3 装饰器方式

```python
@app.post("/api/auth/change-password", ...)
@limiter.limit(config.rate_limit_login)
async def change_password(
    request: Request,  # 必须添加 request 参数
    data: ChangePasswordRequest,
    user: User = Depends(current_active_user),
    ...
):
    ...
```

**解释**：

1. **`@limiter.limit()` 装饰器**：
   - 直接在端点函数上添加
   - 接受限制字符串

2. **`request` 参数**：
   - slowapi 需要 Request 对象来获取客户端 IP
   - **必须**显式添加这个参数

---

## 6. 测试适配

### 文件：`learn_fastapi_auth/tests/conftest.py`

```python
@pytest_asyncio.fixture
async def client(test_engine):
    """Create test client with overridden database session."""
    from learn_fastapi_auth.app import app
    from learn_fastapi_auth.ratelimit import reset_rate_limit_storage

    # Reset rate limit storage before each test
    reset_rate_limit_storage()

    # ... 其他设置 ...

    yield ac

    app.dependency_overrides.clear()
    # Reset after test as well
    reset_rate_limit_storage()
```

**解释**：

1. **为什么要重置？**
   - 测试共享同一个 app 实例
   - rate limit 存储是全局的
   - 如果不重置，一个测试可能影响另一个

2. **前后都重置**：
   - 测试前：确保干净的状态
   - 测试后：清理，不影响下一个测试

---

## 7. 单元测试

### 文件：`tests/test_ratelimit.py`

### 7.1 测试 IP 获取

```python
class MockRequest:
    """Mock request object for testing."""
    def __init__(self, headers: dict = None, client_host: str = "127.0.0.1"):
        self.headers = Headers(headers or {})
        self.client = MagicMock()
        self.client.host = client_host


def test_with_x_forwarded_for_multiple(self):
    """Test getting IP from X-Forwarded-For header (multiple IPs)."""
    request = MockRequest(
        headers={"X-Forwarded-For": "203.0.113.195, 70.41.3.18, 150.172.238.178"},
        client_host="192.168.1.100",
    )
    ip = get_client_ip(request)
    assert ip == "203.0.113.195"  # 第一个是真实客户端 IP
```

### 7.2 测试限制检查

```python
def test_exceeds_limit(self):
    """Test requests exceeding rate limit raise exception."""
    request = MockRequest(client_host="10.0.0.2")

    # 用完限额
    for _ in range(5):
        check_path_rate_limit(request, "5/minute", "/api/test")

    # 下一个请求应该被拒绝
    with pytest.raises(PathRateLimitExceeded) as exc_info:
        check_path_rate_limit(request, "5/minute", "/api/test")

    assert exc_info.value.limit_string == "5/minute"
```

**解释**：

1. **`pytest.raises()`**：
   - 断言代码会抛出指定异常
   - `exc_info.value` 获取异常实例

2. **测试策略**：
   - 先发送允许数量的请求
   - 然后验证超出时会抛出异常

---

## 总结：实现流程

1. **添加依赖**：在 `pyproject.toml` 添加 `slowapi`

2. **添加配置**：在 `config.py` 定义可配置的限制参数

3. **创建模块**：
   - 获取客户端 IP 函数
   - 限制检查函数
   - 自定义异常
   - 异常处理器
   - 中间件工厂函数
   - 设置函数

4. **集成到应用**：
   - 调用设置函数
   - 添加中间件
   - 给自定义端点加装饰器

5. **适配测试**：
   - 在测试 fixture 中重置存储

6. **编写测试**：
   - 测试 IP 获取
   - 测试限制检查
   - 测试异常处理

---

## 关键知识点

1. **中间件 vs 装饰器**：
   - 装饰器：适合自己定义的端点
   - 中间件：适合第三方库的路由

2. **全局存储的问题**：
   - 内存存储在测试中会累积
   - 需要提供重置机制

3. **X-Forwarded-For 处理**：
   - 生产环境必须正确处理代理头
   - 否则所有请求看起来都是同一个 IP

4. **异常处理设计**：
   - 统一的响应格式
   - HTTP 429 状态码
   - 机器可读和人类可读的信息

---

**文档完成于**: 2024-12
