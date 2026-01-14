# Phase 5: Google OAuth Feature Walkthrough

本文档记录了使用 Firebase Authentication 实现 Google OAuth 登录功能的所有代码变更。

## 变更概览

| 类别 | 文件 | 变更类型 |
|------|------|---------|
| 依赖 | `pyproject.toml` | 修改 |
| 模型 | `learn_fastapi_auth/models.py` | 修改 |
| 配置 | `learn_fastapi_auth/config.py` | 修改 |
| 后端 | `learn_fastapi_auth/auth/firebase.py` | 新建 |
| 后端 | `learn_fastapi_auth/app.py` | 修改 |
| Schema | `learn_fastapi_auth/schemas.py` | 修改 |
| 前端 | `learn_fastapi_auth/templates/signin.html` | 修改 |
| 样式 | `learn_fastapi_auth/static/css/style.css` | 修改 |
| JS | `learn_fastapi_auth/static/js/errors.js` | 修改 |
| JS | `learn_fastapi_auth/static/js/auth.js` | 修改（Bug Fix） |
| JS | `learn_fastapi_auth/static/js/app.js` | 修改（OAuth 用户检查） |

---

## 1. 添加依赖

**文件**: `pyproject.toml`

```diff
 dependencies = [
     # ... existing dependencies ...
     "sqladmin>=0.20.0,<1.0.0",  # Admin dashboard for SQLAlchemy
+    # Firebase Authentication
+    "firebase-admin>=6.0.0,<7.0.0",  # Firebase Admin SDK for token verification
 ]
```

安装命令：
```bash
uv sync
```

---

## 2. 更新数据库模型

**文件**: `learn_fastapi_auth/models.py`

添加 `firebase_uid` 字段用于关联 Firebase 用户：

```diff
 class User(SQLAlchemyBaseUserTableUUID, Base):
     # ... existing fields ...
     updated_at: Mapped[datetime] = mapped_column(
         DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
     )

+    # Firebase OAuth - stores Firebase UID for users who sign in via Google/Apple
+    # Nullable because password-based users don't have a Firebase UID
+    firebase_uid: Mapped[Optional[str]] = mapped_column(
+        String(128), unique=True, nullable=True, index=True
+    )
+
     # Relationships
     user_data: Mapped[Optional["UserData"]] = relationship(
```

**说明**：
- `firebase_uid` 是 Firebase 为每个用户生成的唯一 ID
- 设置为 `nullable=True` 因为密码登录的用户没有这个值
- 添加索引以加快查询速度

---

## 3. 添加 Firebase 配置

**文件**: `learn_fastapi_auth/config.py`

### Config 类添加新字段

```diff
     # CSRF Protection
     csrf_cookie_name: str = dataclasses.field()
     csrf_cookie_secure: bool = dataclasses.field()
     csrf_cookie_samesite: str = dataclasses.field()

+    # Firebase Authentication
+    firebase_service_account_path: str = dataclasses.field()
+    firebase_enabled: bool = dataclasses.field()
```

### from_env 方法添加加载逻辑

```diff
             csrf_cookie_samesite=os.environ.get("CSRF_COOKIE_SAMESITE", "lax"),
+            # Firebase Authentication
+            firebase_service_account_path=os.environ.get(
+                "FIREBASE_SERVICE_ACCOUNT_PATH", "firebase-service-account.json"
+            ),
+            firebase_enabled=os.environ.get("FIREBASE_ENABLED", "True").lower()
+            == "true",
         )
```

**配置项说明**：
- `FIREBASE_SERVICE_ACCOUNT_PATH`: Firebase Service Account JSON 文件路径
- `FIREBASE_ENABLED`: 是否启用 Firebase 认证（方便禁用）

---

## 4. 创建 Firebase 模块

**文件**: `learn_fastapi_auth/auth/firebase.py` (新建)

```python
"""
Firebase Authentication integration.

Handles Firebase ID Token verification and user association for OAuth logins.
"""

import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError

# 自定义异常
class FirebaseAuthError(Exception):
    """Base exception for Firebase authentication errors."""
    pass

class FirebaseTokenInvalidError(FirebaseAuthError):
    """Raised when the Firebase token is invalid or expired."""
    pass

class FirebaseNotInitializedError(FirebaseAuthError):
    """Raised when Firebase is not properly initialized."""
    pass

# Firebase 初始化
_firebase_app = None

def init_firebase() -> bool:
    """Initialize Firebase Admin SDK."""
    # 加载 Service Account JSON
    # 验证文件存在
    # 调用 firebase_admin.initialize_app()
    ...

def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID Token and return the decoded claims."""
    # 调用 auth.verify_id_token()
    # 处理各种异常
    ...

def get_user_info_from_token(decoded_token: dict) -> dict:
    """Extract user information from a decoded Firebase token."""
    # 提取 uid, email, name, picture, provider
    ...
```

**核心功能**：
1. `init_firebase()`: 在应用启动时初始化 Firebase SDK
2. `verify_firebase_token()`: 验证前端发送的 ID Token
3. `get_user_info_from_token()`: 从 token 中提取用户信息

---

## 5. 添加 Firebase 登录请求/响应 Schema

**文件**: `learn_fastapi_auth/schemas.py`

```diff
+# =============================================================================
+# Firebase Authentication Schemas
+# =============================================================================
+class FirebaseLoginRequest(BaseModel):
+    """Schema for Firebase login request."""
+
+    id_token: str = Field(..., description="Firebase ID token from frontend")
+
+
+class FirebaseLoginResponse(BaseModel):
+    """Schema for Firebase login response."""
+
+    access_token: str
+    token_type: str = "bearer"
+    is_new_user: bool = Field(
+        default=False, description="True if this is a newly created user"
+    )
+
+
 # =============================================================================
 # General Response Schemas
```

---

## 6. 添加 Firebase 登录路由

**文件**: `learn_fastapi_auth/app.py`

### 添加 imports

```diff
 from .schemas import (
     ChangePasswordRequest,
+    FirebaseLoginRequest,
+    FirebaseLoginResponse,
     MessageResponse,
     ...
 )
+from .auth.firebase import (
+    init_firebase,
+    verify_firebase_token,
+    get_user_info_from_token,
+    FirebaseTokenInvalidError,
+    FirebaseNotInitializedError,
+)
```

### 修改 lifespan 初始化 Firebase

```diff
 @asynccontextmanager
 async def lifespan(app: FastAPI):
     """Application lifespan handler - creates database tables on startup."""
     await create_db_and_tables()
+    # Initialize Firebase if enabled
+    if config.firebase_enabled:
+        init_firebase()
     yield
```

### 添加 Firebase 登录端点

```python
@app.post("/api/auth/firebase", response_model=FirebaseLoginResponse, tags=["auth"])
@limiter.limit(config.rate_limit_login)
async def firebase_login(
    request: Request,
    data: FirebaseLoginRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Login or register using Firebase Authentication."""

    # 1. 验证 Firebase token
    decoded_token = verify_firebase_token(data.id_token)
    user_info = get_user_info_from_token(decoded_token)

    # 2. 查找或创建用户
    #    - 先按 firebase_uid 查找
    #    - 再按 email 查找（关联已有账户）
    #    - 都没有则创建新用户

    # 3. 生成 JWT access token
    jwt_strategy = get_jwt_strategy()
    access_token = await jwt_strategy.write_token(user)

    # 4. 创建 refresh token cookie
    refresh_token_str = await create_refresh_token(session, user.id, ...)

    # 5. 返回响应
    response = JSONResponse(content={...})
    response.set_cookie(value=refresh_token_str, **cookie_settings)
    return response
```

**关键逻辑**：
- 新用户通过 Firebase 登录时自动创建账户（is_verified=True）
- 已有用户（邮箱匹配）会自动关联 Firebase UID
- 返回的 token 与密码登录完全一致

---

## 7. 更新登录页面模板

**文件**: `learn_fastapi_auth/templates/signin.html`

### 添加 Google 登录按钮

```html
<!-- Google Sign In Button -->
<button type="button" class="btn btn-google btn-full" id="google-signin-btn">
    <svg class="google-icon" viewBox="0 0 24 24" width="18" height="18">
        <!-- Google logo SVG paths -->
    </svg>
    Sign in with Google
</button>

<div class="auth-divider">
    <span>or sign in with email</span>
</div>
```

### 添加 Firebase SDK

```html
{% block extra_js %}
<!-- Firebase SDK -->
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-auth-compat.js"></script>

<script>
// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyAOh8zUvhxuVLavOK3Hav64kHSmcOjxeWc",
    authDomain: "learn-fastapi-auth.firebaseapp.com",
    projectId: "learn-fastapi-auth",
    // ...
};

firebase.initializeApp(firebaseConfig);
</script>
```

### 添加 Google 登录逻辑

```javascript
googleSignInBtn.addEventListener('click', async () => {
    try {
        setButtonLoading(googleSignInBtn, 'Signing in...');

        // 1. 使用 Firebase 弹出登录窗口
        const provider = new firebase.auth.GoogleAuthProvider();
        const result = await firebase.auth().signInWithPopup(provider);

        // 2. 获取 ID token
        const idToken = await result.user.getIdToken();

        // 3. 发送到后端
        const response = await fetch('/api/auth/firebase', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: idToken }),
            credentials: 'include'
        });

        // 4. 处理响应
        if (response.ok) {
            setToken(data.access_token);
            window.location.href = '/app';
        }
    } catch (error) {
        // 处理错误
    } finally {
        resetButton(googleSignInBtn);
    }
});
```

---

## 8. 添加 Google 按钮样式

**文件**: `learn_fastapi_auth/static/css/style.css`

```css
/* Google Sign In Button */
.btn-google {
    background-color: #fff;
    color: #757575;
    border: 1px solid #ddd;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    font-weight: 500;
}

.btn-google:hover {
    background-color: #f8f9fa;
    border-color: #ccc;
}

.google-icon {
    flex-shrink: 0;
}

/* Auth Divider */
.auth-divider {
    display: flex;
    align-items: center;
    margin: 24px 0;
    color: #999;
    font-size: 0.875rem;
}

.auth-divider::before,
.auth-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background-color: #ddd;
}

.auth-divider span {
    padding: 0 16px;
}
```

---

## 9. 添加 Firebase 错误消息

**文件**: `learn_fastapi_auth/static/js/errors.js`

```diff
     // CSRF errors
     'CSRF_TOKEN_MISSING': 'Security validation failed...',
     'CSRF_TOKEN_INVALID': 'Security validation failed...',

+    // Firebase/OAuth errors
+    'FIREBASE_AUTH_DISABLED': 'Google sign in is temporarily unavailable...',
+    'FIREBASE_NOT_INITIALIZED': 'Google sign in is not properly configured...',
+    'FIREBASE_TOKEN_INVALID': 'Google sign in failed. Please try again.',
+    'FIREBASE_EMAIL_REQUIRED': 'Email is required for sign in...',

     // Generic fallback
     'UNKNOWN_ERROR': 'An unexpected error occurred...'
```

---

## Bug Fix: Google 登录按钮闪退问题

### 问题描述

点击 "Sign in with Google" 按钮后，按钮在加载状态和原始状态之间闪退，Google 图标丢失。

### 根本原因

**文件**: `learn_fastapi_auth/static/js/auth.js`

`setButtonLoading` 和 `resetButton` 函数使用 `textContent` 保存和恢复按钮内容：

```javascript
// 原代码 - 有问题
button.dataset.originalText = button.textContent;  // 只保存文本
button.textContent = text || button.dataset.originalText;  // 丢失 SVG 图标
```

Google 按钮包含 SVG 图标，使用 `textContent` 会丢失 HTML 结构。

### 修复方案

改用 `innerHTML` 保存和恢复完整的 HTML 内容：

```diff
 function setButtonLoading(button, loadingText = 'Loading...') {
     if (!button) return;

-    // Store original text if not already stored
-    if (!button.dataset.originalText) {
-        button.dataset.originalText = button.textContent;
+    // Store original HTML if not already stored (supports buttons with icons)
+    if (!button.dataset.originalHtml) {
+        button.dataset.originalHtml = button.innerHTML;
     }

     button.disabled = true;
     button.classList.add('loading');
     button.innerHTML = `<span class="spinner"></span> ${loadingText}`;
 }

-function resetButton(button, text = null) {
+function resetButton(button, html = null) {
     if (!button) return;

     button.disabled = false;
     button.classList.remove('loading');
-    button.textContent = text || button.dataset.originalText || 'Submit';
+    // Restore original HTML (including icons) or use provided HTML
+    button.innerHTML = html || button.dataset.originalHtml || 'Submit';
 }
```

### 影响范围

此修复对所有按钮都有效：
- 纯文本按钮：正常工作
- 带图标按钮（如 Google 按钮）：现在可以正确恢复图标

---

## 测试验证

```bash
# 安装依赖
uv sync --all-extras

# 运行测试
.venv/bin/pytest tests/ -v

# 所有 74 个测试通过
```

---

## 使用方式

### 启动服务器

```bash
.venv/bin/uvicorn learn_fastapi_auth.app:app --reload --host 0.0.0.0 --port 8000
```

### 测试 Google 登录

1. 访问 http://localhost:8000/signin
2. 点击 "Sign in with Google" 按钮
3. 在弹出窗口中选择 Google 账号
4. 授权后自动登录并跳转到 /app

### API 端点

```
POST /api/auth/firebase
Content-Type: application/json

{
    "id_token": "<Firebase ID Token from frontend>"
}

Response:
{
    "access_token": "eyJ...",
    "token_type": "bearer",
    "is_new_user": false
}

Cookie: refresh_token (HttpOnly)
```

---

## 10. OAuth 用户修改密码限制

### 问题背景

OAuth 用户（通过 Google 登录）没有设置密码，后端会为他们生成随机密码。当这些用户在 `/app` 页面点击 "Change Password" 时，会遇到问题：
- 他们不知道当前密码
- 修改密码对他们没有意义（他们用 Google 登录）

### 解决方案

当 OAuth 用户点击 "Change Password" 时，显示友好提示而不是打开修改密码对话框。

### 代码变更

#### 1. 添加 `is_oauth_user` 字段到 UserRead Schema

**文件**: `learn_fastapi_auth/schemas.py`

```diff
 class UserRead(schemas.BaseUser[uuid.UUID]):
     """Schema for reading user data."""

     created_at: Optional[datetime] = None
     updated_at: Optional[datetime] = None
+    is_oauth_user: bool = False
+
+    @classmethod
+    def model_validate(cls, obj, **kwargs):
+        """Override to compute is_oauth_user from firebase_uid."""
+        if hasattr(obj, "firebase_uid"):
+            data = {
+                "id": obj.id,
+                "email": obj.email,
+                "is_active": obj.is_active,
+                "is_superuser": obj.is_superuser,
+                "is_verified": obj.is_verified,
+                "created_at": getattr(obj, "created_at", None),
+                "updated_at": getattr(obj, "updated_at", None),
+                "is_oauth_user": obj.firebase_uid is not None,
+            }
+            return super().model_validate(data, **kwargs)
+        return super().model_validate(obj, **kwargs)
```

#### 2. 添加错误消息

**文件**: `learn_fastapi_auth/static/js/errors.js`

```diff
     // Firebase/OAuth errors
     'FIREBASE_AUTH_DISABLED': '...',
     'FIREBASE_TOKEN_INVALID': '...',
     'FIREBASE_EMAIL_REQUIRED': '...',

+    // OAuth user limitations
+    'OAUTH_USER_NO_PASSWORD': 'You signed in with Google, so there is no password to change. Your account security is managed by Google.',
```

#### 3. 加载用户信息并检查 OAuth 状态

**文件**: `learn_fastapi_auth/static/js/app.js`

```diff
 // Global State
 let currentUserData = '';
+let currentUserInfo = null;

 document.addEventListener('DOMContentLoaded', async () => {
     if (!isLoggedIn()) {
         window.location.href = '/signin?error=login_required';
         return;
     }

-    await loadUserData();
+    // Load user info and user data in parallel
+    await Promise.all([
+        loadUserInfo(),
+        loadUserData()
+    ]);

     setupEventListeners();
 });

+async function loadUserInfo() {
+    try {
+        const response = await apiRequest('/api/users/me');
+        if (!response) return;
+        if (response.ok) {
+            currentUserInfo = await response.json();
+        }
+    } catch (error) {
+        console.error('Error loading user info:', error);
+    }
+}

 function openPasswordModal() {
+    // Check if user signed in via OAuth (Google)
+    if (currentUserInfo && currentUserInfo.is_oauth_user) {
+        showToast(getErrorMessage('OAUTH_USER_NO_PASSWORD'), 'info');
+        return;
+    }
+
     const modal = document.getElementById('password-modal-overlay');
     if (modal) modal.classList.add('show');
     // ...
 }
```

### 用户体验

| 用户类型 | 点击 "Change Password" 后 |
|---------|--------------------------|
| 密码用户 | 正常打开修改密码对话框 |
| OAuth 用户 | 显示蓝色提示消息："You signed in with Google, so there is no password to change..." |

---

## 文件变更总结

| 文件 | 行数变化 | 说明 |
|------|---------|------|
| `pyproject.toml` | +2 | 添加 firebase-admin 依赖 |
| `models.py` | +5 | 添加 firebase_uid 字段 |
| `config.py` | +10 | 添加 Firebase 配置项 |
| `auth/firebase.py` | +140 | 新建 Firebase 集成模块 |
| `schemas.py` | +35 | 添加 Firebase Schema + is_oauth_user 字段 |
| `app.py` | +80 | 添加 Firebase 登录路由 |
| `signin.html` | +75 | 添加 Google 按钮、Firebase SDK 和改进的错误处理 |
| `style.css` | +35 | 添加 Google 按钮样式 |
| `errors.js` | +8 | 添加 Firebase 和 OAuth 用户错误消息 |
| `auth.js` | +4 | Bug fix: 修复按钮 HTML 恢复 |
| `app.js` | +20 | 加载用户信息 + OAuth 用户密码检查 |
