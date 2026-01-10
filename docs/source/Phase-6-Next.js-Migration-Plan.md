# Phase 6: Next.js + Tailwind CSS Migration Plan

本文档描述将前端从纯 HTML/JS/CSS 迁移到 Next.js + Tailwind CSS 的计划。

---

## 1. Migration Overview

### 1.1 What Changes

| 组件 | 现状 | 迁移后 |
|-----|-----|-------|
| **Frontend Framework** | Jinja2 + 纯 HTML/JS/CSS | Next.js 13+ (App Router) |
| **Styling** | 自定义 CSS | Tailwind CSS |
| **Language** | JavaScript | TypeScript |
| **Deployment** | 单一服务器 | FastAPI (后端) + Vercel (前端) |
| **API Communication** | 同域请求 | 跨域请求 (CORS) |

### 1.2 What Stays the Same

- FastAPI 后端代码（`app.py`, `auth/`, `models.py` 等）
- 数据库模型和 Schema
- 所有 API 端点（`/api/auth/*`, `/api/users/*`, `/api/user-data`）
- 认证逻辑（JWT、Refresh Token、Firebase OAuth）
- 安全机制（CSRF、Rate Limiting）

### 1.3 Benefits

1. **更好的开发体验**：TypeScript 类型安全、热重载
2. **组件复用**：React 组件化架构
3. **现代 UI**：Tailwind CSS 快速开发
4. **SEO 友好**：Next.js SSR/SSG
5. **独立部署**：前后端可独立扩展
6. **Vercel 集成**：自动部署、边缘网络

---

## 2. Architecture Design

### 2.1 Deployment Architecture

```
                    ┌─────────────────┐
                    │     Client      │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │   Vercel (CDN)  │           │  FastAPI Server │
    │   Next.js App   │ ────────> │  (API Backend)  │
    │   Frontend      │  /api/*   │  Port 8000      │
    └─────────────────┘           └─────────────────┘
```

### 2.2 Development Architecture

开发时使用 Next.js rewrites 代理 API 请求到本地 FastAPI：

```javascript
// next.config.js
const nextConfig = {
  rewrites: async () => [
    {
      source: '/api/:path*',
      destination: process.env.NODE_ENV === 'development'
        ? 'http://127.0.0.1:8000/api/:path*'
        : process.env.NEXT_PUBLIC_API_URL + '/api/:path*',
    },
  ],
}
```

### 2.3 Project Structure

```
learn_fastapi_auth-project/
├── learn_fastapi_auth/          # FastAPI 后端 (保持不变)
│   ├── app.py
│   ├── auth/
│   ├── models.py
│   └── ...
├── frontend/                    # 新建: Next.js 前端
│   ├── app/
│   │   ├── layout.tsx          # Root layout (导航栏)
│   │   ├── page.tsx            # 首页 /
│   │   ├── globals.css         # Tailwind base styles
│   │   ├── signin/
│   │   │   └── page.tsx        # 登录页
│   │   ├── signup/
│   │   │   └── page.tsx        # 注册页
│   │   ├── dashboard/
│   │   │   └── page.tsx        # 用户主页 (原 /app)
│   │   ├── forgot-password/
│   │   │   └── page.tsx
│   │   ├── reset-password/
│   │   │   └── page.tsx
│   │   └── verify-email/
│   │       └── page.tsx
│   ├── components/
│   │   ├── ui/                 # 通用 UI 组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Toast.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── Spinner.tsx
│   │   ├── auth/               # 认证相关组件
│   │   │   ├── SignInForm.tsx
│   │   │   ├── SignUpForm.tsx
│   │   │   ├── GoogleSignInButton.tsx
│   │   │   └── PasswordResetForm.tsx
│   │   └── layout/
│   │       ├── Navbar.tsx
│   │       └── Footer.tsx
│   ├── lib/
│   │   ├── api.ts              # API 请求封装
│   │   ├── auth.ts             # Token 管理
│   │   ├── errors.ts           # 错误消息映射
│   │   └── firebase.ts         # Firebase 客户端配置
│   ├── hooks/
│   │   ├── useAuth.ts          # 认证 hook
│   │   └── useToast.ts         # Toast hook
│   ├── types/
│   │   └── index.ts            # TypeScript 类型定义
│   ├── public/
│   │   └── favicon.ico
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── postcss.config.js
├── docs/
└── tests/
```

---

## 3. Backend Modifications Required

### 3.1 CORS Configuration

需要修改 `app.py` 添加 CORS 支持：

```python
from fastapi.middleware.cors import CORSMiddleware

# 在 app 创建后添加
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",           # Next.js dev server
        "https://your-app.vercel.app",     # Vercel production
    ],
    allow_credentials=True,                # 允许发送 cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3.2 Refresh Token Cookie Settings

由于前后端分离，需要调整 cookie 设置：

```python
# refresh_token.py
def get_refresh_token_cookie_settings(lifetime_seconds: Optional[int] = None) -> dict:
    actual_lifetime = lifetime_seconds if lifetime_seconds is not None else config.refresh_token_lifetime
    return {
        "key": config.refresh_token_cookie_name,
        "httponly": True,
        "secure": True,  # 生产环境必须 True
        "samesite": "none",  # 跨域需要设为 none
        "max_age": actual_lifetime,
        "path": "/api/auth",
        "domain": config.cookie_domain,  # 新增: 需要配置
    }
```

### 3.3 New Config Fields

```python
# config.py
@dataclasses.dataclass
class Config:
    # ... existing fields ...

    # CORS settings
    cors_origins: list[str] = dataclasses.field()
    cookie_domain: str = dataclasses.field()

# from_env()
cors_origins=os.environ.get(
    "CORS_ORIGINS", "http://localhost:3000"
).split(","),
cookie_domain=os.environ.get("COOKIE_DOMAIN", ""),
```

### 3.4 Remove Frontend Serving

可以移除或保留以下内容（保留可作为 fallback）：

```python
# 可选择移除
- routers/pages.py (HTML 页面路由)
- templates/ 目录
- static/ 目录
- Jinja2Templates 配置
```

---

## 4. Frontend Implementation Details

### 4.1 Package Dependencies

```json
{
  "dependencies": {
    "next": "14.x",
    "react": "18.x",
    "react-dom": "18.x",
    "typescript": "5.x",
    "tailwindcss": "3.x",
    "autoprefixer": "10.x",
    "postcss": "8.x",
    "firebase": "10.x",
    "zod": "3.x"
  },
  "devDependencies": {
    "@types/node": "20.x",
    "@types/react": "18.x",
    "@types/react-dom": "18.x"
  }
}
```

### 4.2 Core Files Migration

| 原文件 | 新文件 | 说明 |
|-------|-------|------|
| `static/js/auth.js` | `lib/auth.ts` + `lib/api.ts` | TypeScript 重写 |
| `static/js/errors.js` | `lib/errors.ts` | 错误消息映射 |
| `static/js/app.js` | `app/dashboard/page.tsx` | 集成到 React 组件 |
| `static/css/style.css` | Tailwind classes | 用 Tailwind 重写样式 |
| `templates/base.html` | `app/layout.tsx` | Root layout |
| `templates/signin.html` | `app/signin/page.tsx` | React 组件 |
| `templates/signup.html` | `app/signup/page.tsx` | React 组件 |
| `templates/app.html` | `app/dashboard/page.tsx` | React 组件 |

### 4.3 Authentication Flow

```typescript
// lib/auth.ts
const AUTH_TOKEN_KEY = 'auth_token';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}
```

```typescript
// lib/api.ts
export async function apiRequest<T>(
  url: string,
  options: RequestInit = {}
): Promise<T | null> {
  const token = getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',  // 重要：发送 cookies
  });

  if (response.status === 401) {
    removeToken();
    window.location.href = '/signin?error=session_expired';
    return null;
  }

  return response.json();
}
```

### 4.4 Toast Context

```typescript
// hooks/useToast.ts
import { createContext, useContext, useState } from 'react';

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
}
```

### 4.5 Protected Routes

```typescript
// components/auth/AuthGuard.tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isLoggedIn } from '@/lib/auth';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    if (!isLoggedIn()) {
      router.push('/signin?error=login_required');
    }
  }, [router]);

  if (!isLoggedIn()) {
    return null; // or loading spinner
  }

  return <>{children}</>;
}
```

---

## 5. Step-by-Step Migration Plan

### Phase 6.1: Setup & Infrastructure

1. **创建 Next.js 项目**
   ```bash
   cd learn_fastapi_auth-project
   npx create-next-app@latest frontend --typescript --tailwind --app --src-dir=false
   ```

2. **配置文件**
   - 复制并修改 `next.config.js` (API rewrites)
   - 配置 `tailwind.config.js` (自定义颜色)
   - 设置 `tsconfig.json` (path aliases)

3. **后端 CORS 配置**
   - 修改 `app.py` 添加 CORS middleware
   - 修改 cookie 设置支持跨域

### Phase 6.2: Core Library Migration

1. **迁移 auth.js → lib/auth.ts**
   - Token 管理函数
   - TypeScript 类型定义

2. **迁移 errors.js → lib/errors.ts**
   - 错误消息映射
   - 导出类型安全的函数

3. **创建 lib/api.ts**
   - API 请求封装
   - 自动 token 注入
   - 401 处理

4. **配置 Firebase (lib/firebase.ts)**
   - Firebase 客户端初始化
   - Google OAuth 配置

### Phase 6.3: UI Components

1. **基础 UI 组件 (components/ui/)**
   - Button (with loading state)
   - Input (with error state)
   - Toast
   - Modal
   - Spinner

2. **布局组件 (components/layout/)**
   - Navbar (认证状态感知)
   - Footer

3. **表单组件 (components/auth/)**
   - SignInForm
   - SignUpForm
   - GoogleSignInButton
   - ForgotPasswordForm
   - ResetPasswordForm
   - ChangePasswordModal

### Phase 6.4: Pages Migration

1. **首页 (app/page.tsx)**
   - 简单着陆页

2. **认证页面**
   - app/signin/page.tsx
   - app/signup/page.tsx
   - app/forgot-password/page.tsx
   - app/reset-password/page.tsx
   - app/verify-email/page.tsx

3. **受保护页面**
   - app/dashboard/page.tsx (原 /app)

### Phase 6.5: Integration & Testing

1. **集成测试**
   - 完整认证流程测试
   - Google OAuth 测试
   - Token 刷新测试

2. **跨域测试**
   - Cookie 传递测试
   - CORS 配置验证

3. **性能优化**
   - 代码分割
   - 图片优化

### Phase 6.6: Deployment

1. **Vercel 部署**
   - 连接 GitHub 仓库
   - 配置环境变量
   - 设置自定义域名

2. **后端配置更新**
   - 更新 CORS origins
   - 更新 cookie domain

---

## 6. Environment Variables

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
```

### Backend (.env)

```env
# Existing vars...

# New CORS settings
CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app
COOKIE_DOMAIN=.your-domain.com

# Updated cookie settings for cross-origin
REFRESH_TOKEN_COOKIE_SECURE=True
REFRESH_TOKEN_COOKIE_SAMESITE=none
```

---

## 7. Risk Assessment & Mitigation

### 7.1 Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Cross-origin cookie issues | High | Medium | 仔细测试 SameSite/Secure 设置 |
| Firebase token 验证失败 | High | Low | 保持 Firebase 配置不变 |
| CORS 配置错误 | Medium | Medium | 开发环境完整测试 |
| Session 丢失 | Medium | Low | 保持 localStorage 策略 |
| 性能下降 | Low | Low | 使用 Next.js 优化功能 |

### 7.2 Rollback Plan

如果迁移失败，可以：
1. 保留原有 templates/ 和 static/ 目录
2. 在 `app.py` 中恢复 Jinja2 页面路由
3. 移除 CORS middleware

---

## 8. Verification Checklist

### 功能验证

- [ ] 用户注册
- [ ] 邮箱验证
- [ ] 用户登录
- [ ] Google OAuth 登录
- [ ] Token 刷新
- [ ] 忘记密码
- [ ] 重置密码
- [ ] 修改密码
- [ ] 用户数据 CRUD
- [ ] 登出
- [ ] 登出所有设备

### 安全验证

- [ ] CORS 只允许指定域名
- [ ] Cookie 跨域正常传递
- [ ] HTTPS 强制启用 (生产)
- [ ] CSRF 保护有效
- [ ] Rate limiting 有效

### 用户体验验证

- [ ] Loading 状态正确显示
- [ ] 错误消息友好
- [ ] Toast 通知正常
- [ ] 响应式布局
- [ ] 深色/浅色模式 (可选)

---

## 9. Decision Points

在开始执行前，请确认以下决策：

### Q1: 项目结构

**选项 A**: 前端代码放在 `frontend/` 子目录（推荐）
- 优点：清晰分离，独立管理
- 缺点：需要分别管理两个 package.json

**选项 B**: 前端代码放在项目根目录
- 优点：简单
- 缺点：与 Python 项目文件混合

### Q2: 原有前端保留策略

**选项 A**: 完全移除 templates/ 和 static/
- 优点：干净
- 缺点：无法回滚

**选项 B**: 保留但不再维护（推荐）
- 优点：可作为备份
- 缺点：增加代码量

### Q3: Admin 后台

**选项 A**: 保持 SQLAdmin（不迁移）（推荐）
- 优点：无需额外工作
- 缺点：需要访问后端 URL

**选项 B**: 迁移到 Next.js 自定义 admin
- 优点：统一技术栈
- 缺点：大量额外工作

### Q4: UI 风格

**选项 A**: 使用 esc_mini_tools 的暗色主题
- 优点：现代感强
- 缺点：需要全面重新设计

**选项 B**: 保持现有浅色主题（推荐）
- 优点：迁移工作量小
- 缺点：风格可能不够现代

---

## 10. Estimated Effort

| Phase | 主要工作 | 预计文件数 |
|-------|---------|-----------|
| 6.1 Setup | 项目初始化、配置 | 5-8 |
| 6.2 Core Libs | auth, api, errors | 4-5 |
| 6.3 UI Components | Button, Input, Toast 等 | 8-12 |
| 6.4 Pages | 7 个页面迁移 | 7-10 |
| 6.5 Testing | 集成测试、修复 | - |
| 6.6 Deployment | Vercel 配置 | 2-3 |

---

**文档版本**: 1.0
**创建日期**: 2025-01-10
**状态**: 待审阅
