# Frontend Next.js Architecture

本文档介绍项目前端的目录结构设计，帮助开发者快速理解代码组织方式，定位需要修改的文件。

---

## Quick Navigation

| 我想要... | 查看位置 |
|----------|---------|
| 修改首页 | `app/(home)/page.tsx` |
| 修改登录/注册流程 | `app/(auth)/` |
| 修改用户仪表盘 | `app/(saas)/dashboard/page.tsx` |
| 添加新的 API 端点 | `constants/api.ts` |
| 添加新的页面路由 | `constants/routes.ts` |
| 修改错误提示文案 | `constants/messages.ts` |
| 添加通用 UI 组件 | `components/ui/` |

---

## Directory Structure Overview

```
learn_fastapi_auth-project/
│
├── app/                          # Next.js App Router 页面
│   ├── (home)/                   # 🏠 首页模块 (Route Group)
│   │   └── page.tsx              # 首页 → /
│   │
│   ├── (auth)/                   # 🔐 认证模块 (Route Group)
│   │   ├── signin/page.tsx       # 登录页 → /signin
│   │   ├── signup/page.tsx       # 注册页 → /signup
│   │   ├── forgot-password/      # 忘记密码 → /forgot-password
│   │   ├── reset-password/       # 重置密码 → /reset-password
│   │   └── verify-email/         # 邮箱验证 → /verify-email
│   │
│   ├── (saas)/                   # 💼 SAAS 应用模块 (Route Group)
│   │   └── dashboard/page.tsx    # 用户仪表盘 → /dashboard
│   │
│   ├── layout.tsx                # 根布局 (Navbar, Footer, ToastProvider)
│   └── globals.css               # 全局样式
│
├── components/                   # React 组件
│   ├── ui/                       # 通用 UI 原子组件
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   ├── Spinner.tsx
│   │   ├── Toast.tsx
│   │   └── index.ts              # Barrel export
│   │
│   ├── layout/                   # 布局组件
│   │   ├── Navbar.tsx
│   │   └── index.ts
│   │
│   ├── saas/                     # SAAS 业务组件
│   │   ├── UserDataCard.tsx      # 用户数据展示卡片
│   │   ├── EditDataModal.tsx     # 编辑数据弹窗
│   │   └── index.ts
│   │
│   └── user/                     # 用户相关组件
│       ├── AccountSettingsCard.tsx
│       ├── ChangePasswordModal.tsx
│       └── index.ts
│
├── constants/                    # 集中管理的常量
│   ├── api.ts                    # API 端点常量
│   ├── routes.ts                 # 前端路由常量
│   ├── auth.ts                   # 认证相关常量
│   ├── messages.ts               # 错误消息映射
│   └── index.ts                  # 统一导出
│
├── hooks/                        # 自定义 React Hooks
│   └── useToast.tsx              # Toast 通知 Hook + Context
│
├── lib/                          # 工具函数库
│   ├── api.ts                    # API 请求封装 (自动刷新 Token)
│   ├── auth.ts                   # Token 管理、验证函数
│   └── firebase.ts               # Google OAuth (Firebase)
│
├── types/                        # TypeScript 类型定义
│   └── index.ts                  # User, UserData, 各种 Response 类型
│
└── config/                       # 配置文件
    └── config.json               # 环境配置 (Token 过期时间等)
```

---

## Route Groups 说明

目录名带括号 `(groupName)` 是 **Next.js Route Groups** 特性：

| 目录 | URL | 说明 |
|------|-----|------|
| `app/(home)/page.tsx` | `/` | 括号不影响 URL |
| `app/(auth)/signin/page.tsx` | `/signin` | 纯粹用于代码组织 |
| `app/(saas)/dashboard/page.tsx` | `/dashboard` | 同一组可共享布局 |

**优势**：
- 代码按功能模块分组，易于维护
- 每个 Route Group 可以有独立的 `layout.tsx`
- URL 结构保持简洁

---

## Module Responsibilities

### 1. 首页模块 `(home)`

| 文件 | 职责 |
|------|------|
| `page.tsx` | 展示欢迎信息，根据登录状态显示不同 CTA 按钮 |

### 2. 认证模块 `(auth)`

| 页面 | 文件 | 功能 |
|------|------|------|
| 登录 | `signin/page.tsx` | Email/Password 登录 + Google OAuth |
| 注册 | `signup/page.tsx` | 新用户注册 |
| 忘记密码 | `forgot-password/page.tsx` | 发送密码重置邮件 |
| 重置密码 | `reset-password/page.tsx` | 设置新密码 (需 Token) |
| 邮箱验证 | `verify-email/page.tsx` | 验证邮箱链接处理 |

### 3. SAAS 应用模块 `(saas)`

| 页面 | 文件 | 功能 |
|------|------|------|
| 仪表盘 | `dashboard/page.tsx` | 用户数据管理、账户设置 |

**Dashboard 使用的组件**：
- `UserDataCard` - 显示用户文本数据
- `EditDataModal` - 编辑数据弹窗
- `AccountSettingsCard` - 账户设置卡片
- `ChangePasswordModal` - 修改密码弹窗

---

## Constants 常量管理

所有硬编码值集中在 `constants/` 目录：

### `api.ts` - API 端点

```typescript
import { API_ENDPOINTS } from '@/constants';

// 使用
await fetch(API_ENDPOINTS.AUTH.LOGIN, { ... });
await fetch(API_ENDPOINTS.USER.DATA, { ... });
```

**可用端点**：
| 常量 | 值 |
|------|-----|
| `API_ENDPOINTS.AUTH.LOGIN` | `/api/auth/login` |
| `API_ENDPOINTS.AUTH.REGISTER` | `/api/auth/register` |
| `API_ENDPOINTS.AUTH.LOGOUT` | `/api/auth/logout` |
| `API_ENDPOINTS.AUTH.REFRESH` | `/api/auth/refresh` |
| `API_ENDPOINTS.AUTH.VERIFY` | `/api/auth/verify` |
| `API_ENDPOINTS.AUTH.FIREBASE` | `/api/auth/firebase` |
| `API_ENDPOINTS.AUTH.FORGOT_PASSWORD` | `/api/auth/forgot-password` |
| `API_ENDPOINTS.AUTH.RESET_PASSWORD` | `/api/auth/reset-password` |
| `API_ENDPOINTS.AUTH.CHANGE_PASSWORD` | `/api/auth/change-password` |
| `API_ENDPOINTS.USER.ME` | `/api/users/me` |
| `API_ENDPOINTS.USER.DATA` | `/api/user-data` |

### `routes.ts` - 前端路由

```typescript
import { ROUTES } from '@/constants';

// 使用
router.push(ROUTES.DASHBOARD);
<Link href={ROUTES.SIGNIN}>Sign In</Link>
```

**可用路由**：
| 常量 | 值 |
|------|-----|
| `ROUTES.HOME` | `/` |
| `ROUTES.SIGNIN` | `/signin` |
| `ROUTES.SIGNUP` | `/signup` |
| `ROUTES.DASHBOARD` | `/dashboard` |
| `ROUTES.FORGOT_PASSWORD` | `/forgot-password` |
| `ROUTES.RESET_PASSWORD` | `/reset-password` |

### `messages.ts` - 错误消息

```typescript
import { getErrorMessage, getFieldError } from '@/constants';

// API 错误码转用户友好消息
const message = getErrorMessage('LOGIN_BAD_CREDENTIALS');
// → "Invalid email or password. Please check and try again."

// 字段级错误
const fieldError = getFieldError('REGISTER_USER_ALREADY_EXISTS');
// → { field: 'email', message: '...' }
```

### `auth.ts` - 认证常量

```typescript
import { STORAGE_KEYS, VALIDATION, AUTH_EVENTS, REDIRECT_DELAY } from '@/constants';

// localStorage 键名
STORAGE_KEYS.AUTH_TOKEN  // 'auth_token'
STORAGE_KEYS.USER_EMAIL  // 'user_email'

// 验证规则
VALIDATION.EMAIL_REGEX
VALIDATION.PASSWORD_MIN_LENGTH  // 8

// 事件名
AUTH_EVENTS.AUTH_CHANGE  // 'auth-change'

// 重定向延迟
REDIRECT_DELAY.DEFAULT       // 1000ms
REDIRECT_DELAY.REGISTRATION  // 3000ms
```

---

## Component Organization

### UI 组件 (`components/ui/`)

通用、可复用的原子组件：

| 组件 | 用途 | Props |
|------|------|-------|
| `Button` | 按钮 | `variant`, `loading`, `loadingText`, `fullWidth` |
| `Input` | 输入框 | `label`, `error`, `type` |
| `Modal` | 弹窗 | `isOpen`, `onClose`, `title` |
| `Spinner` | 加载动画 | `size` |
| `Toast` | 通知消息 | 通过 `useToast` Hook 使用 |

**导入方式**：
```typescript
import { Button, Input, Modal } from '@/components/ui';
```

### 业务组件 (`components/saas/`, `components/user/`)

特定功能的业务组件：

```typescript
// SAAS 业务组件
import { UserDataCard, EditDataModal } from '@/components/saas';

// 用户相关组件
import { AccountSettingsCard, ChangePasswordModal } from '@/components/user';
```

---

## Lib 工具库

### `lib/auth.ts` - Token 管理

```typescript
import { getToken, setToken, removeToken, isLoggedIn } from '@/lib/auth';
import { validateEmail, validatePassword } from '@/lib/auth';

// Token 操作
setToken(accessToken);    // 保存 Token + 触发 auth-change 事件
const token = getToken(); // 获取 Token
removeToken();            // 清除 Token
isLoggedIn();             // 检查是否登录

// 表单验证
validateEmail('test@example.com');  // true/false
validatePassword('Abc12345');       // true/false (8+ chars, letter + number)
```

### `lib/api.ts` - API 请求

```typescript
import { apiRequest } from '@/lib/api';

// 自动添加 Authorization header
// 自动处理 401 错误并尝试刷新 Token
const response = await apiRequest('/api/user-data', {
  method: 'PUT',
  body: JSON.stringify({ text_value: 'new data' }),
});
```

### `lib/firebase.ts` - Google OAuth

```typescript
import { signInWithGoogle } from '@/lib/firebase';

const idToken = await signInWithGoogle();
// 然后发送到 /api/auth/firebase
```

---

## Feature → Code Mapping

### 添加新页面

1. 确定模块：首页 `(home)` / 认证 `(auth)` / 应用 `(saas)`
2. 在对应目录创建 `new-page/page.tsx`
3. 在 `constants/routes.ts` 添加路由常量
4. 在 `components/layout/Navbar.tsx` 添加导航链接（如需要）

### 添加新 API 调用

1. 在 `constants/api.ts` 添加端点常量
2. 在 `types/index.ts` 定义请求/响应类型
3. 使用 `apiRequest()` 发起请求

### 添加新错误消息

1. 在 `constants/messages.ts` 的 `ERROR_MESSAGES` 添加映射
2. 如果是字段级错误，在 `FIELD_ERROR_MAP` 添加映射

### 修改表单验证规则

1. 在 `constants/auth.ts` 的 `VALIDATION` 修改规则
2. `lib/auth.ts` 的验证函数会自动使用新规则

---

## File Dependency Graph

```
app/
  └── 页面组件
        ├── components/ui/     (UI 原子组件)
        ├── components/saas/   (业务组件)
        ├── components/user/   (用户组件)
        ├── hooks/useToast     (Toast 功能)
        ├── lib/auth           (Token 管理)
        ├── lib/api            (API 请求)
        ├── constants/         (所有常量)
        └── types/             (TypeScript 类型)
```

---

## When to Look Where

| 场景 | 查看位置 |
|------|---------|
| 修改登录逻辑 | `app/(auth)/signin/page.tsx` |
| 修改 Google OAuth | `lib/firebase.ts`, `app/(auth)/signin/page.tsx` |
| 添加新的表单字段 | `types/index.ts`, 对应页面组件 |
| 修改 API 端点路径 | `constants/api.ts` |
| 修改错误提示文案 | `constants/messages.ts` |
| 修改 Token 存储方式 | `lib/auth.ts`, `constants/auth.ts` |
| 添加新的 UI 组件 | `components/ui/`, 更新 `index.ts` |
| 修改导航栏 | `components/layout/Navbar.tsx` |
| 修改全局布局 | `app/layout.tsx` |
| 修改 Dashboard 功能 | `app/(saas)/dashboard/page.tsx`, `components/saas/` |

---

## Tech Stack

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 16.x | React 框架 (App Router) |
| TypeScript | 5.x | 类型安全 |
| Tailwind CSS | 4.x | 样式 |
| Firebase | 11.x | Google OAuth |

---

*Last updated: 2025-01*
