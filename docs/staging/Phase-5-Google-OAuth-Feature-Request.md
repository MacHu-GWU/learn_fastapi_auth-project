# Phase 5: Google OAuth 登录功能 (Firebase 方案)

## 概述

本文档描述了使用 Firebase Authentication 为 FastAPI 认证系统添加 Google OAuth 登录功能的实现计划。

## 决策摘要

| 项目 | 决策 |
|------|------|
| OAuth 提供商 | Google（未来可轻松添加 Apple 等） |
| 实现方式 | Firebase Authentication |
| 前端库 | Firebase JS SDK |
| 后端库 | `firebase-admin` |

## 为什么选择 Firebase？

### 架构对比

```
直接 OAuth 方案（每个提供商都需要后端处理）:
┌──────┐    ┌────────┐    ┌──────────────────────────┐
│ 用户 │ -> │ Google │ -> │ 后端（处理 Google OAuth）│
└──────┘    └────────┘    └──────────────────────────┘
┌──────┐    ┌────────┐    ┌─────────────────────────┐
│ 用户 │ -> │ Apple  │ -> │ 后端（处理 Apple OAuth）│  <- 非常复杂
└──────┘    └────────┘    └─────────────────────────┘

Firebase 方案（后端只做一件事：验证 Firebase token）:
┌──────┐    ┌────────┐    ┌──────────┐    ┌─────────────────────┐
│ 用户 │ -> │ Google │ -> │ Firebase │ -> │ 后端（验证 token）  │
└──────┘    └────────┘    └──────────┘    └─────────────────────┘
┌──────┐    ┌────────┐    ┌──────────┐    ┌─────────────────────┐
│ 用户 │ -> │ Apple  │ -> │ Firebase │ -> │ 后端（同样的代码）  │
└──────┘    └────────┘    └──────────┘    └─────────────────────┘
```

### 选择 Firebase 的理由

1. **Apple Sign In 极其复杂**
   - 动态 client_secret（需要用私钥签名 JWT，每 6 个月过期）
   - 用户可隐藏邮箱（返回 `xxx@privaterelay.appleid.com`）
   - 只在首次登录返回用户姓名
   - Firebase 帮你处理所有这些

2. **后端代码一劳永逸**
   - 无论 Google、Apple、Facebook，后端只验证 Firebase token
   - 添加新提供商 = Firebase Console 点几下 + 前端加按钮
   - 后端零改动

3. **免费额度慷慨**
   - 每月 5 万活跃用户免费
   - 超出后按使用量付费

4. **用户主要在国外**
   - Firebase 全球可用，无访问问题
   - 国内用户继续使用邮箱注册

---

## 开始写代码之前：你需要做的外部工作

### 你需要准备的信息

完成 Firebase 配置后，你需要提供：

**后端需要的（放到服务器）**：
```
Firebase Service Account JSON 文件（或其内容）
```

**前端需要的（可以公开）**：
```javascript
const firebaseConfig = {
  apiKey: "xxx",
  authDomain: "xxx.firebaseapp.com",
  projectId: "xxx",
  // ... 其他配置
};
```

### 如何把凭据给我

1. 下载 Service Account JSON 文件
2. 将文件放到项目根目录，命名为 `firebase-service-account.json`
3. 在 `.env` 文件中添加：
   ```
   FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
   ```
4. 告诉我前端的 `firebaseConfig` 内容
5. 告诉我："Firebase 配置好了，可以开始写代码"

**安全提示**：
- `firebase-service-account.json` 已在 `.gitignore` 中，不会提交
- 前端的 `firebaseConfig` 可以公开（有安全规则保护）

---

## Firebase Console 配置详细步骤

### 前提条件

- 一个 Google 账号
- 访问 [Firebase Console](https://console.firebase.google.com/)

### 第一步：创建 Firebase 项目

1. 打开 [Firebase Console](https://console.firebase.google.com/)
2. 点击 **"创建项目"** 或 **"添加项目"**
3. 输入项目名称：`learn-fastapi-auth`
4. Google Analytics：可以选择启用或禁用（对认证功能无影响）
5. 点击 **"创建项目"**
6. 等待项目创建完成，点击 **"继续"**

**官方文档**：[创建 Firebase 项目](https://firebase.google.com/docs/projects/learn-more)

### 第二步：启用 Authentication 并配置 Google 登录

1. 在左侧边栏，点击 **"构建"** > **"Authentication"**
2. 点击 **"开始"** 按钮
3. 在 **"Sign-in method"** 标签页，点击 **"Google"**
4. 点击 **"启用"** 开关
5. 填写配置：
   - **项目公开名称**：`Learn FastAPI Auth`（用户在 Google 登录时看到）
   - **项目支持电子邮件**：选择你的邮箱
6. 点击 **"保存"**

**官方文档**：[Google 登录](https://firebase.google.com/docs/auth/web/google-signin)

### 第三步：添加 Web 应用

1. 在项目概览页面，点击 **"</>"** 图标（Web）添加应用
2. 输入应用昵称：`learn-fastapi-auth-web`
3. 可选：勾选 "同时设置 Firebase Hosting"（如果需要）
4. 点击 **"注册应用"**
5. **复制 firebaseConfig 配置**：
   ```javascript
   const firebaseConfig = {
     apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX",
     authDomain: "learn-fastapi-auth.firebaseapp.com",
     projectId: "learn-fastapi-auth",
     storageBucket: "learn-fastapi-auth.appspot.com",
     messagingSenderId: "123456789",
     appId: "1:123456789:web:abcdef123456"
   };
   ```
6. 保存这个配置，稍后需要告诉我
7. 点击 **"继续前往控制台"**

**官方文档**：[将 Firebase 添加到 Web 应用](https://firebase.google.com/docs/web/setup)

### 第四步：下载 Service Account 密钥

1. 点击左上角的 **齿轮图标** > **"项目设置"**
2. 点击 **"服务账号"** 标签页
3. 确保选中 **"Firebase Admin SDK"**
4. 点击 **"生成新的私钥"**
5. 确认对话框，点击 **"生成密钥"**
6. JSON 文件会自动下载
7. 将文件重命名为 `firebase-service-account.json`
8. 移动到项目根目录

**官方文档**：[Firebase Admin SDK 设置](https://firebase.google.com/docs/admin/setup)

### 第五步：配置授权域名

1. 在 Authentication 页面，点击 **"Settings"** 标签页
2. 点击 **"授权域名"**
3. 确认以下域名已添加（通常自动添加）：
   - `localhost`
   - `learn-fastapi-auth.firebaseapp.com`
4. 如果你有生产域名，点击 **"添加网域"** 添加它

**官方文档**：[授权域名](https://firebase.google.com/docs/auth/web/google-signin#before_you_begin)

### 第六步：（未来）添加 Apple Sign In

当你需要添加 Apple 登录时：

1. 在 **"Sign-in method"** 标签页，点击 **"Apple"**
2. 点击 **"启用"** 开关
3. Firebase 会显示引导步骤：
   - 配置 Apple Developer Console
   - 创建 Service ID
   - 下载密钥
4. 按照 Firebase 的引导完成配置
5. 点击 **"保存"**

**后端不需要任何改动！** 只需要前端添加 Apple 登录按钮。

**官方文档**：[Apple 登录](https://firebase.google.com/docs/auth/web/apple)

---

## 检查清单：开始写代码前

在告诉我 "开始写代码" 之前，请确认：

- [ ] 已创建 Firebase 项目
- [ ] 已启用 Authentication 的 Google 登录
- [ ] 已添加 Web 应用并复制了 `firebaseConfig`
- [ ] 已下载 Service Account JSON 文件
- [ ] 已将 JSON 文件放到项目根目录（`firebase-service-account.json`）
- [ ] 已在 `.env` 中添加 `FIREBASE_SERVICE_ACCOUNT_PATH`
- [ ] 已确认 `localhost` 在授权域名列表中

完成后告诉我 `firebaseConfig` 的内容，我会开始实现代码。

---

## 实现计划

### 需要添加的依赖

```bash
uv add firebase-admin
```

### 数据库变更

#### 更新 User 模型

添加 `firebase_uid` 字段用于关联 Firebase 用户：

```python
# 在 learn_fastapi_auth/models.py 中

class User(SQLAlchemyBaseUserTableUUID, Base):
    # ... 现有字段 ...

    # Firebase 用户 ID（可选，仅 OAuth 用户有）
    firebase_uid: Mapped[str | None] = mapped_column(
        String(128),
        unique=True,
        nullable=True,
        index=True,
    )
```

### 配置变更

在 `learn_fastapi_auth/config.py` 中添加：

```python
@dataclass
class Config:
    # ... 现有配置 ...

    # Firebase
    FIREBASE_SERVICE_ACCOUNT_PATH: str = "firebase-service-account.json"
```

### 新文件

#### `learn_fastapi_auth/auth/firebase.py`

```python
"""Firebase Authentication 集成。

处理 Firebase ID Token 验证和用户关联。
"""

import firebase_admin
from firebase_admin import auth, credentials

def init_firebase(service_account_path: str):
    """初始化 Firebase Admin SDK。"""
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)

def verify_firebase_token(id_token: str) -> dict:
    """验证 Firebase ID Token。

    返回解码后的 token 信息，包含：
    - uid: Firebase 用户 ID
    - email: 用户邮箱
    - name: 用户名称（可能为空）
    - picture: 头像 URL（可能为空）
    """
    return auth.verify_id_token(id_token)
```

### 需要修改的文件

| 文件 | 修改内容 |
|------|---------|
| `models.py` | 添加 `firebase_uid` 字段 |
| `config.py` | 添加 Firebase 配置 |
| `auth/firebase.py` | **新文件** - Firebase 初始化和 token 验证 |
| `auth/users.py` | 添加 Firebase 用户创建/关联函数 |
| `app.py` | 初始化 Firebase，添加登录路由 |
| 前端模板 | 集成 Firebase JS SDK，添加登录按钮 |

### 新增路由

| 路由 | 方法 | 描述 |
|------|------|------|
| `/api/auth/firebase` | POST | 接收 Firebase ID Token，返回我们的 JWT |

### 实现步骤

1. **添加依赖**
   ```bash
   uv add firebase-admin
   ```

2. **更新数据库模型**
   - 添加 `firebase_uid` 字段到 User

3. **添加配置**
   - 添加 Firebase 配置字段

4. **创建 Firebase 模块**
   - 初始化 Firebase Admin SDK
   - 实现 token 验证函数

5. **实现 Firebase 登录路由**
   ```python
   @router.post("/api/auth/firebase")
   async def firebase_login(id_token: str):
       # 1. 验证 Firebase token
       # 2. 提取用户信息（email, uid）
       # 3. 查找或创建本地用户
       # 4. 生成 JWT + refresh token
       # 5. 返回 token
   ```

6. **更新前端**
   - 添加 Firebase JS SDK
   - 实现 "使用 Google 登录" 按钮
   - 登录成功后发送 ID Token 到后端

7. **集成现有认证流程**
   - 复用现有的 JWT 生成逻辑
   - 复用现有的 refresh token 逻辑

8. **编写测试**

---

## 用户体验流程

### 新用户（首次 Google 登录）

```
1. 用户点击 "使用 Google 登录" 按钮
   |
   v
2. Firebase JS SDK 弹出 Google 登录窗口
   （或重定向到 Google，取决于配置）
   |
   v
3. 用户在 Google 页面登录/选择账号
   |
   v
4. Google 返回授权给 Firebase
   |
   v
5. Firebase JS SDK 获取 ID Token
   |
   v
6. 前端发送 POST /api/auth/firebase { id_token: "xxx" }
   |
   v
7. 后端用 firebase-admin 验证 token
   - 确认 token 有效且未过期
   - 提取 email, uid, name
   |
   v
8. 后端查找或创建用户
   - 通过 firebase_uid 查找
   - 或通过 email 查找并关联
   - 或创建新用户（is_verified=True）
   |
   v
9. 后端生成我们自己的 JWT + refresh token
   - 与密码登录使用完全相同的机制
   |
   v
10. 返回 { access_token, token_type }
    - 设置 refresh_token cookie
   |
   v
11. 前端保存 token，跳转到 /app
    - 用户已登录
```

### 已有用户（邮箱匹配）

如果用户之前用邮箱/密码注册，后来使用相同邮箱的 Google 登录：

```
步骤 1-7 同上
   |
   v
8. 后端通过 email 找到已有用户
   - 更新 firebase_uid 字段
   - 用户现在可以通过两种方式登录
   |
   v
步骤 9-11 同上
```

### 返回用户

```
步骤 1-7 同上（更快，Google 可能记住登录状态）
   |
   v
8. 后端通过 firebase_uid 找到用户
   |
   v
步骤 9-11 同上
```

---

## 前端集成示例

### HTML 模板中添加 Firebase SDK

```html
<!-- 在 </body> 前添加 -->
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-auth-compat.js"></script>

<script>
  // Firebase 配置（你从 Firebase Console 复制的）
  const firebaseConfig = {
    apiKey: "xxx",
    authDomain: "xxx.firebaseapp.com",
    projectId: "xxx",
    // ...
  };

  // 初始化 Firebase
  firebase.initializeApp(firebaseConfig);
</script>
```

### 登录按钮

```html
<button id="google-signin-btn" class="google-btn">
  <img src="/static/google-icon.svg" alt="Google" />
  使用 Google 登录
</button>
```

### JavaScript 登录逻辑

```javascript
document.getElementById('google-signin-btn').addEventListener('click', async () => {
  try {
    // 1. 使用 Firebase 登录
    const provider = new firebase.auth.GoogleAuthProvider();
    const result = await firebase.auth().signInWithPopup(provider);

    // 2. 获取 ID Token
    const idToken = await result.user.getIdToken();

    // 3. 发送到后端
    const response = await fetch('/api/auth/firebase', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: idToken }),
      credentials: 'include',  // 接收 refresh token cookie
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      window.location.href = '/app';
    } else {
      const error = await response.json();
      alert('登录失败: ' + error.detail);
    }
  } catch (error) {
    console.error('Google 登录失败:', error);
    alert('登录失败，请重试');
  }
});
```

---

## 安全考量

| 特性 | 实现方式 |
|------|---------|
| **Token 验证** | Firebase Admin SDK 验证签名和过期时间 |
| **用户身份** | Firebase 保证 email 已验证 |
| **CSRF 保护** | 现有 CSRF 中间件保护 POST 请求 |
| **Rate Limiting** | 复用现有的登录 rate limit |
| **Refresh Token** | 复用现有的 HttpOnly cookie 机制 |

### Service Account 安全

```
firebase-service-account.json 包含敏感信息：
- 私钥（可以签发任意 token）
- 项目 ID

安全措施：
- 已添加到 .gitignore
- 生产环境使用环境变量或 secrets manager
- 定期轮换密钥
```

---

## 测试策略

### 单元测试

```python
# tests/auth/test_auth_firebase.py

async def test_verify_valid_firebase_token():
    """测试验证有效的 Firebase token。"""
    # 需要 mock firebase_admin.auth.verify_id_token
    pass

async def test_firebase_login_creates_user():
    """测试 Firebase 登录创建新用户。"""
    pass

async def test_firebase_login_links_existing_user():
    """测试 Firebase 登录关联已有用户。"""
    pass

async def test_firebase_login_returns_jwt():
    """测试 Firebase 登录返回我们的 JWT。"""
    pass
```

### 集成测试

```python
async def test_firebase_endpoint_requires_token():
    """测试 /api/auth/firebase 需要 token。"""
    pass

async def test_firebase_endpoint_rejects_invalid_token():
    """测试拒绝无效的 Firebase token。"""
    pass
```

### 手动测试清单

- [ ] 点击 "使用 Google 登录" 弹出 Google 登录窗口
- [ ] 选择 Google 账号后成功登录
- [ ] 新用户正确创建（邮箱正确，is_verified=True）
- [ ] 已有相同邮箱的用户被关联（firebase_uid 被设置）
- [ ] JWT access token 有效
- [ ] Refresh token cookie 已设置
- [ ] OAuth 登录后可以访问受保护路由
- [ ] 登出正常工作
- [ ] 可以再次通过 Google 登录

---

## 未来扩展

### 添加 Apple Sign In

当需要添加 Apple 登录时：

**Firebase Console（5 分钟）**：
1. Authentication > Sign-in method > Apple > 启用
2. 按照 Firebase 引导配置 Apple Developer Console

**前端（10 分钟）**：
```javascript
// 添加 Apple 登录按钮
document.getElementById('apple-signin-btn').addEventListener('click', async () => {
  const provider = new firebase.auth.OAuthProvider('apple.com');
  provider.addScope('email');
  provider.addScope('name');

  const result = await firebase.auth().signInWithPopup(provider);
  const idToken = await result.user.getIdToken();

  // 与 Google 登录完全相同的后端调用
  await fetch('/api/auth/firebase', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: idToken }),
    credentials: 'include',
  });
});
```

**后端（0 分钟）**：
- 不需要任何改动！
- 验证的是 Firebase token，不是 Apple token

### 添加其他提供商

Firebase 支持的提供商：
- Google ✓
- Apple（未来）
- Facebook
- Twitter
- GitHub
- Microsoft
- Yahoo
- 手机号 SMS

每个只需要：
1. Firebase Console 启用
2. 前端添加按钮和对应的 provider
3. 后端零改动

---

## 回滚计划

如果出现问题：

1. **功能开关**：添加 `FIREBASE_AUTH_ENABLED` 配置
2. **数据库**：`firebase_uid` 字段可以保留，不影响密码登录
3. **路由**：Firebase 登录路由独立，可以禁用

---

## 参考资料

### Firebase 官方文档

- [Firebase Authentication 概述](https://firebase.google.com/docs/auth)
- [Web 端 Google 登录](https://firebase.google.com/docs/auth/web/google-signin)
- [Web 端 Apple 登录](https://firebase.google.com/docs/auth/web/apple)
- [验证 ID Token (Admin SDK)](https://firebase.google.com/docs/auth/admin/verify-id-tokens)
- [管理用户](https://firebase.google.com/docs/auth/admin/manage-users)

### Firebase Console 链接

- [Firebase Console](https://console.firebase.google.com/)
- [Authentication 设置](https://console.firebase.google.com/project/_/authentication/providers)

### Python 库文档

- [firebase-admin Python SDK](https://firebase.google.com/docs/admin/setup#python)
- [firebase-admin PyPI](https://pypi.org/project/firebase-admin/)

### 安全资源

- [Firebase 安全规则](https://firebase.google.com/docs/rules)
- [ID Token 验证最佳实践](https://firebase.google.com/docs/auth/admin/verify-id-tokens#verify_id_tokens_using_the_firebase_admin_sdk)
