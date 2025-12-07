# FastAPI User Authentication SaaS - 项目技术规格文档

> 本文档为项目实现指南。项目概述、技术栈和开发方式详见 [README.md](../../README.md)

## 核心功能需求

- 用户注册（邮箱 + 密码）
- 邮箱验证（发送验证邮件）
- 用户登录（JWT token）
- 用户专属资源管理（文本数据的读写）

---

## 📁 项目结构

```
learn_fastapi_auth-project/
├── learn_fastapi_auth/          # 主应用包
│   ├── __init__.py
│   ├── paths.py                 # 路径管理（使用 PathEnum）
│   ├── config.py                # 配置管理（从 .env 读取）
│   ├── database.py              # 数据库连接和初始化
│   ├── models.py                # SQLAlchemy ORM 模型
│   ├── schemas.py               # Pydantic schemas
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── users.py             # fastapi-users 配置
│   │   └── email.py             # 邮件发送功能
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py             # 页面路由（返回 HTML）
│   │   └── api.py               # API 路由（用户数据 CRUD）
│   ├── templates/               # Jinja2 模板
│   │   ├── base.html            # 基础模板
│   │   ├── index.html           # 主页
│   │   ├── signup.html          # 注册页面
│   │   ├── signin.html          # 登录页面
│   │   ├── app.html             # 用户 App 页面
│   │   └── verify_email.html    # 邮箱验证成功页面
│   ├── static/                  # 静态文件
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── auth.js          # 认证相关 JS
│   │       └── app.js           # App 页面 JS
│   └── tests/                   # 测试辅助
│       ├── helper.py
│       └── pytest_cov_helper.py
├── tests/                       # 单元测试
├── main.py                      # FastAPI 应用入口
├── .env                         # 环境变量配置（不提交 git）
├── .env.example                 # 环境变量示例
├── pyproject.toml               # Python 项目配置和依赖
├── mise.toml                    # 任务自动化配置
├── README.md                    # 项目概述
└── data.db                      # SQLite 数据库文件（自动生成）
```

---

## 🗄️ 数据库设计

### 表 1: users (由 fastapi-users 管理)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,                    -- 用户唯一标识
    email VARCHAR(255) UNIQUE NOT NULL,     -- 邮箱 (唯一)
    hashed_password VARCHAR(1024) NOT NULL, -- 密码哈希
    is_active BOOLEAN DEFAULT FALSE,        -- 账户是否激活 (邮箱验证后为 True)
    is_superuser BOOLEAN DEFAULT FALSE,     -- 是否超级用户
    is_verified BOOLEAN DEFAULT FALSE,      -- 邮箱是否验证
    created_at TIMESTAMP DEFAULT NOW(),     -- 创建时间
    updated_at TIMESTAMP DEFAULT NOW()      -- 更新时间
);
```

**字段说明**:
- `is_active`: 账户是否可用（邮箱验证后设为 True）
- `is_verified`: 邮箱验证状态
- fastapi-users 会自动管理这些字段

### 表 2: user_data (用户专属数据)

```sql
CREATE TABLE user_data (
    user_id UUID PRIMARY KEY,               -- 用户 ID (FK -> users.id)
    text_value TEXT DEFAULT '',             -- 用户文本数据
    created_at TIMESTAMP DEFAULT NOW(),     -- 创建时间
    updated_at TIMESTAMP DEFAULT NOW(),     -- 更新时间
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**说明**:
- `user_id` 是主键，同时也是外键，确保每个用户只有一条数据
- `text_value` 存储用户的文本内容
- 删除用户时自动删除对应数据 (CASCADE)

---

## 🔐 认证流程设计

### 1. 用户注册流程

```
用户操作:
1. 访问 /signup
2. 输入邮箱和密码
3. 点击 "Create Account"
   ↓
后端处理:
4. 验证邮箱格式
5. 检查邮箱是否已存在 → 若存在返回错误
6. 哈希密码
7. 创建用户记录 (is_active=False, is_verified=False)
8. 生成验证 token (JWT, 15分钟有效)
9. 发送验证邮件到用户邮箱
10. 返回 "注册成功，请查收验证邮件"
   ↓
用户操作:
11. 打开邮箱，点击验证链接
   ↓
后端处理:
12. 验证 token 有效性
13. 更新用户: is_active=True, is_verified=True
14. 创建 user_data 记录 (text_value='')
15. 重定向到登录页，显示 "邮箱验证成功，请登录"
```

**验证邮件内容示例**:
```
主题: 验证您的邮箱地址

欢迎注册！

请点击下方链接验证您的邮箱地址：

[验证邮箱] (http://localhost:8000/auth/verify-email?token=xxx)

此链接将在 15 分钟后过期。

如果您没有注册此账户，请忽略此邮件。
```

### 2. 邮箱验证流程

```
用户点击验证链接:
GET /auth/verify-email?token=xxx
   ↓
后端处理:
1. 解码 JWT token
2. 验证 token 是否过期
3. 从 token 中获取 user_id
4. 查询用户记录
5. 检查用户是否已验证 → 若已验证显示 "邮箱已验证"
6. 更新用户: is_active=True, is_verified=True
7. 创建 user_data 记录
8. 返回成功页面，提示用户登录
```

### 3. 用户登录流程

```
用户操作:
1. 访问 /signin
2. 输入邮箱和密码
3. 点击 "Sign In"
   ↓
后端处理:
4. 查询用户记录
5. 验证密码是否匹配
6. 检查 is_active 状态 → 若未激活返回 "请先验证邮箱"
7. 生成 JWT access token (有效期 1 小时)
8. 将 token 存储到 SQLite (tokens 表)
9. 返回 token 给前端
   ↓
前端处理:
10. 将 token 存储到 localStorage
11. 重定向到 /app
```

### 4. Token 存储（SQLite）

```sql
CREATE TABLE tokens (
    token VARCHAR(500) PRIMARY KEY,         -- JWT token
    user_id UUID NOT NULL,                  -- 用户 ID
    created_at TIMESTAMP DEFAULT NOW(),     -- 创建时间
    expires_at TIMESTAMP NOT NULL,          -- 过期时间
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**Token 验证流程**:
```
每次 API 请求:
1. 前端从 localStorage 读取 token
2. 在请求 Header 中添加: Authorization: Bearer <token>
3. 后端中间件验证 token:
   - 检查 token 是否存在于 tokens 表
   - 检查 token 是否过期
   - 验证 JWT 签名
4. 验证通过 → 继续处理请求
5. 验证失败 → 返回 401 Unauthorized
```

### 5. 访问受保护资源

```
用户访问 /app:
1. 前端检查 localStorage 是否有 token
2. 若无 token → 重定向到 /signin
3. 若有 token → 向后端请求用户数据
   GET /api/user-data
   Headers: Authorization: Bearer <token>
   ↓
后端验证:
4. 验证 token 有效性
5. 从 token 中获取 user_id
6. 查询 user_data 表
7. 返回数据给前端
   ↓
前端渲染:
8. 显示用户邮箱和文本框
9. 文本框显示 text_value
```

---

## 🌐 页面路由设计

### 页面路由 (返回 HTML)

| 路由 | 方法 | 说明 | 需要登录 |
|------|------|------|----------|
| `/` | GET | 主页 (Hello World + 导航栏) | ❌ |
| `/signup` | GET | 注册页面 | ❌ |
| `/signin` | GET | 登录页面 | ❌ |
| `/app` | GET | 用户 App 页面 | ✅ |
| `/auth/verify-email` | GET | 邮箱验证处理 (query: token) | ❌ |

### API 路由 (返回 JSON)

| 路由 | 方法 | 说明 | 需要登录 |
|------|------|------|----------|
| `/api/auth/register` | POST | 用户注册 | ❌ |
| `/api/auth/login` | POST | 用户登录 | ❌ |
| `/api/auth/logout` | POST | 用户登出 | ✅ |
| `/api/user-data` | GET | 获取用户数据 | ✅ |
| `/api/user-data` | PUT | 更新用户数据 | ✅ |
| `/api/users/me` | GET | 获取当前用户信息 | ✅ |

---

## 🎨 前端页面设计

### 1. 主页 (`/`)

**布局**:
```
┌─────────────────────────────────────────────────┐
│  Logo          [Sign In]  [Create Account]  [App] │  ← 导航栏
├─────────────────────────────────────────────────┤
│                                                  │
│              Hello World!                        │  ← 标题
│                                                  │
│       Welcome to FastAPI Auth Project           │  ← 副标题
│                                                  │
└─────────────────────────────────────────────────┘
```

**导航栏逻辑**:
- **未登录**: 显示 `Sign In` 和 `Create Account`
- **已登录**: 显示用户邮箱 (`user@example.com`) 和 `App` 按钮

### 2. 注册页面 (`/signup`)

**表单字段**:
```
┌─────────────────────────────────────┐
│        Create Account                │
├─────────────────────────────────────┤
│  Email:                              │
│  [____________________________]      │
│                                      │
│  Password:                           │
│  [____________________________]      │
│                                      │
│  Confirm Password:                   │
│  [____________________________]      │
│                                      │
│  [     Create Account     ]          │
│                                      │
│  Already have an account? Sign In    │
└─────────────────────────────────────┘
```

**验证规则**:
- 邮箱: 必填，格式验证
- 密码: 最少 8 位，必须包含字母和数字
- 确认密码: 必须与密码一致

**提交后**:
- 成功: 显示提示框 "注册成功！请查收验证邮件"，3秒后跳转到主页
- 失败: 显示错误提示（如"邮箱已存在"）

### 3. 登录页面 (`/signin`)

**表单字段**:
```
┌─────────────────────────────────────┐
│          Sign In                     │
├─────────────────────────────────────┤
│  Email:                              │
│  [____________________________]      │
│                                      │
│  Password:                           │
│  [____________________________]      │
│                                      │
│  [        Sign In        ]           │
│                                      │
│  Don't have an account? Sign Up      │
└─────────────────────────────────────┘
```

**提交后**:
- 成功: 保存 token 到 localStorage，跳转到 `/app`
- 失败: 显示错误提示（如"邮箱或密码错误"，"请先验证邮箱"）

### 4. App 页面 (`/app`)

**布局**:
```
┌─────────────────────────────────────────────────┐
│  Logo          user@example.com  [Logout]        │  ← 导航栏
├─────────────────────────────────────────────────┤
│                                                  │
│  Your Personal Data                              │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │                                         │    │
│  │  Hello, this is my data!                │    │  ← 文本框 (只读)
│  │                                         │    │
│  └────────────────────────────────────────┘    │
│                                                  │
│  [     Edit     ]                                │  ← 编辑按钮
│                                                  │
└─────────────────────────────────────────────────┘
```

**编辑功能**:
1. 点击 "Edit" 按钮
2. 弹出对话框:
   ```
   ┌─────────────────────────────────────┐
   │  Edit Your Data                      │
   ├─────────────────────────────────────┤
   │  ┌────────────────────────────────┐ │
   │  │ Hello, this is my data!        │ │
   │  │                                │ │
   │  └────────────────────────────────┘ │
   │                                      │
   │  [  Cancel  ]  [  Save  ]            │
   └─────────────────────────────────────┘
   ```
3. 点击 "Save" → 调用 API 更新数据 → 关闭对话框 → 刷新显示

---

## 📧 环境变量配置

创建 `.env` 文件（参考 `.env.example`）：

```bash
# 数据库
DATABASE_URL=sqlite:///./data.db

# JWT 密钥（生成方式: openssl rand -hex 32）
SECRET_KEY=your-secret-key-here

# 邮件 SMTP 配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=True
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # Gmail 应用专用密码
SMTP_FROM=your-gmail@gmail.com
SMTP_FROM_NAME=FastAPI Auth

# 应用配置
FRONTEND_URL=http://localhost:8000
VERIFICATION_TOKEN_LIFETIME=900  # 验证 token 有效期（秒），15分钟
ACCESS_TOKEN_LIFETIME=3600       # 访问 token 有效期（秒），1小时
```

**Gmail 应用专用密码获取步骤**:
1. 启用 Gmail 的 2FA
2. 访问 [Google 账户安全设置](https://myaccount.google.com/security)
3. 在"应用密码"中生成 SMTP 专用密码（16 位，包含空格）
4. 将密码复制到 `.env` 的 `SMTP_PASSWORD` 中

### 邮件验证模板

**文件位置**: `learn_fastapi_auth/templates/verify_email.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .button { 
            display: inline-block; 
            padding: 12px 24px; 
            background-color: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 4px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>验证您的邮箱地址</h2>
        <p>欢迎注册！</p>
        <p>请点击下方按钮验证您的邮箱地址：</p>
        <p>
            <a href="{{ verification_url }}" class="button">验证邮箱</a>
        </p>
        <p>或复制此链接到浏览器：<br>{{ verification_url }}</p>
        <p>此链接将在 15 分钟后过期。</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            如果您没有注册此账户，请忽略此邮件。
        </p>
    </div>
</body>
</html>
```

---

## 🔨 开发阶段划分

### Phase 1: 核心认证功能 (后端为主)

**目标**: 实现 fastapi-users 集成和基础认证功能

**任务清单**:
- [ ] 项目初始化
  - [ ] 创建项目结构
  - [ ] 配置 pyproject.toml 依赖
  - [ ] 创建 .env 配置文件
- [ ] 数据库设计
  - [ ] 定义 User 模型 (使用 fastapi-users)
  - [ ] 定义 UserData 模型
  - [ ] 创建数据库迁移
- [ ] 认证功能
  - [ ] 配置 fastapi-users
  - [ ] 实现用户注册 API
  - [ ] 实现邮箱验证逻辑
  - [ ] 实现用户登录 API
  - [ ] 实现 JWT token 管理
- [ ] 邮件功能
  - [ ] 配置 Gmail SMTP
  - [ ] 实现邮件发送函数
  - [ ] 创建验证邮件模板
  - [ ] 测试邮件发送

**验收标准**:
- ✅ 可以通过 API 注册用户
- ✅ 收到验证邮件（真实 Gmail 收件箱）
- ✅ 点击验证链接激活账户
- ✅ 可以通过 API 登录并获得 token
- ✅ Token 存储在 SQLite 并可验证

**预计时间**: 2-3 天

---

### Phase 2: 前端页面 (UI 实现)

**目标**: 实现所有页面的 HTML/CSS/JS

**任务清单**:
- [ ] 基础模板
  - [ ] 创建 base.html (导航栏、公共样式)
  - [ ] 编写 style.css (全局样式)
- [ ] 主页
  - [ ] index.html 模板
  - [ ] 导航栏登录状态切换逻辑
- [ ] 注册页面
  - [ ] signup.html 模板
  - [ ] 表单验证 JavaScript
  - [ ] 注册 API 调用
  - [ ] 错误提示显示
- [ ] 登录页面
  - [ ] signin.html 模板
  - [ ] 登录 API 调用
  - [ ] Token 存储到 localStorage
  - [ ] 跳转逻辑
- [ ] 邮箱验证页面
  - [ ] verify_email.html 模板
  - [ ] 成功/失败提示

**验收标准**:
- ✅ 所有页面样式美观、响应式
- ✅ 表单验证正常工作
- ✅ 错误提示清晰友好
- ✅ 页面跳转逻辑正确

**预计时间**: 2-3 天

---

### Phase 3: App 功能 (用户数据管理)

**目标**: 实现用户专属数据的读写功能

**任务清单**:
- [ ] App 页面
  - [ ] app.html 模板
  - [ ] 显示当前登录用户邮箱
  - [ ] 文本框展示用户数据
- [ ] 数据 API
  - [ ] GET /api/user-data (获取数据)
  - [ ] PUT /api/user-data (更新数据)
  - [ ] Token 验证中间件
- [ ] 编辑功能
  - [ ] 编辑按钮和对话框 UI
  - [ ] 编辑对话框 JavaScript
  - [ ] 保存功能实现
  - [ ] 实时更新显示
- [ ] 登出功能
  - [ ] 登出按钮
  - [ ] 清除 localStorage token
  - [ ] 删除数据库 token 记录
  - [ ] 跳转到主页

**验收标准**:
- ✅ 未登录访问 /app 自动跳转到登录页
- ✅ 登录后可以看到自己的数据
- ✅ 可以编辑并保存数据
- ✅ 刷新页面数据仍然存在
- ✅ 不同用户看到不同数据
- ✅ 登出功能正常工作

**预计时间**: 1-2 天

---

### Phase 4: 优化和扩展 (可选)

**目标**: 完善用户体验和安全性

**任务清单**:
- [ ] 账户管理
  - [ ] 密码重置功能 (发送重置邮件)
  - [ ] 修改密码功能
  - [ ] 账户设置页面
- [ ] 安全增强
  - [ ] 添加 CSRF 保护
  - [ ] 添加请求频率限制
  - [ ] Token 刷新机制
- [ ] 用户体验优化
  - [ ] 加载动画
  - [ ] 更友好的错误提示
  - [ ] 记住登录状态（延长 token 有效期）
- [ ] 管理功能
  - [ ] 管理员后台 (删除用户)
  - [ ] 用户列表查看

**验收标准**:
- ✅ 所有功能稳定可靠
- ✅ 用户体验流畅
- ✅ 安全性符合基本要求

**预计时间**: 2-3 天 (可选)

---

## 🔒 安全性考虑

### 1. 密码安全
- ✅ 使用 bcrypt 哈希算法
- ✅ 不存储明文密码
- ✅ 密码最少 8 位，包含字母和数字

### 2. Token 安全
- ✅ JWT token 设置过期时间
- ✅ 使用 HTTPS (生产环境)
- ✅ Token 存储在数据库，可撤销
- ✅ 验证 token 签名

### 3. 邮箱验证
- ✅ 验证 token 15 分钟过期
- ✅ Token 一次性使用
- ✅ 未验证用户无法登录

### 4. API 安全
- ✅ 所有敏感操作需要 token 验证
- ✅ 输入验证和清理
- ✅ 防止 SQL 注入 (SQLAlchemy ORM)

### 5. 数据隔离
- ✅ 用户只能访问自己的数据
- ✅ API 中验证 user_id 匹配
- ✅ 数据库级外键约束

---

## 📦 核心依赖

项目依赖定义在 `pyproject.toml` 中。主要依赖包括：

**核心框架与认证**:
- `fastapi` - Web 框架
- `fastapi-users[sqlalchemy]` - 用户认证库
- `sqlalchemy` - ORM 框架
- `uvicorn` - ASGI 服务器

**数据库与邮件**:
- `python-dotenv` - 环境变量管理
- `aiosmtplib` - 异步 SMTP 客户端（邮件发送）
- `email-validator` - 邮箱格式验证

**认证与安全**:
- `pyjwt` - JWT Token 处理
- `bcrypt` - 密码哈希算法
- `python-multipart` - 表单数据解析

**模板与前端**:
- `jinja2` - 模板引擎

使用 `mise run inst` 安装所有依赖（包括开发依赖）。

---

## 🚀 运行指南

### 1. 环境准备

```bash
# 创建虚拟环境和安装依赖（使用 mise）
mise run venv-create
mise run inst
```

### 2. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填写以下信息：
# - DATABASE_URL（SQLite 数据库路径）
# - SECRET_KEY（JWT 密钥，使用: openssl rand -hex 32）
# - SMTP 邮件配置（Gmail 应用专用密码）
# - FRONTEND_URL（开发时为 http://localhost:8000）
```

### 3. 初始化数据库

```bash
# 创建数据库表
.venv/bin/python -c "from learn_fastapi_auth.database import create_db_and_tables; create_db_and_tables()"
```

### 4. 启动应用

```bash
# 方法 1：直接运行
.venv/bin/python main.py

# 方法 2：使用 uvicorn（需要安装）
.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问应用

打开浏览器访问: http://localhost:8000

---

## 🧪 测试流程

### 完整用户流程测试

1. **注册新用户**
   - 访问 http://localhost:8000/signup
   - 输入邮箱: `husanhe+test1@gmail.com`
   - 输入密码: `Test1234`
   - 点击注册
   - 检查是否显示 "注册成功，请查收验证邮件"

2. **验证邮箱**
   - 打开 Gmail 收件箱
   - 查找验证邮件
   - 点击验证链接
   - 检查是否跳转到成功页面

3. **登录**
   - 访问 http://localhost:8000/signin
   - 输入注册的邮箱和密码
   - 点击登录
   - 检查是否跳转到 /app

4. **访问 App**
   - 检查是否显示用户邮箱
   - 检查文本框内容（应为空）
   - 点击 "Edit" 按钮
   - 输入一些文本
   - 点击 "Save"
   - 刷新页面，检查数据是否保存

5. **登出**
   - 点击 "Logout" 按钮
   - 检查是否跳转到主页
   - 尝试访问 /app，检查是否跳转到登录页

6. **重新登录**
   - 登录同一账户
   - 检查之前保存的数据是否还在

---

## 📝 API 文档与调试

启动应用后，FastAPI 自动生成的交互式 API 文档：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

这两个页面可用于调试 API 端点和查看请求/响应示例。

---

## ✅ 开发前检查清单

在开始编码前，请确认以下准备工作已完成：

- [ ] 理解项目整体架构和核心功能需求
- [ ] 阅读 CLAUDE.md 了解开发工具和命令
- [ ] 准备 Gmail 账户和应用专用密码
- [ ] 理解四个开发阶段（Phase 1-4）的目标和验收标准
- [ ] 明确当前代码库结构（learn_fastapi_auth/ 为主包）
- [ ] 创建 .env 文件并配置必要的环境变量

确认无误后，即可按照 Phase 1-4 的计划开始实现！

---

**文档版本**: v2.0
**最后更新**: 2024-12-07
**维护人**: 项目指导者