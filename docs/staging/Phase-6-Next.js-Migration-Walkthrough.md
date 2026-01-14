# Phase 6: Next.js Migration Walkthrough

This document records the actual implementation details of migrating the frontend from HTML/JS/CSS to Next.js + Tailwind CSS.

## Migration Overview

| Aspect | Before | After |
|--------|--------|-------|
| Framework | Vanilla HTML/JS/CSS | Next.js 16 + React 19 |
| Styling | Plain CSS | Tailwind CSS 4 |
| Language | JavaScript | TypeScript |
| Rendering | Server-side (Jinja2) | Client-side SPA with SSR |
| Location | `learn_fastapi_auth/static/` + `templates/` | Root directory |

## Files Created

### Project Configuration (Root Level)

| File | Purpose |
|------|---------|
| `package.json` | Node.js project manifest with dependencies |
| `package-lock.json` | Locked dependency versions |
| `tsconfig.json` | TypeScript configuration with path aliases |
| `next.config.ts` | Next.js configuration with API rewrites |
| `postcss.config.mjs` | PostCSS configuration for Tailwind |
| `eslint.config.mjs` | ESLint configuration |
| `next-env.d.ts` | Next.js TypeScript declarations |

### Core Libraries (`lib/`)

| File | Purpose | Original Source |
|------|---------|-----------------|
| `lib/auth.ts` | Token management (localStorage), validation utilities | `static/js/auth.js` |
| `lib/api.ts` | API request wrapper with auto token refresh | `static/js/app.js` (apiRequest function) |
| `lib/errors.ts` | Error code to message mapping | `static/js/errors.js` |
| `lib/firebase.ts` | Firebase client initialization, Google OAuth | `static/js/firebase.js` |

### Type Definitions (`types/`)

| File | Purpose |
|------|---------|
| `types/index.ts` | TypeScript interfaces for User, UserData, API responses |

### UI Components (`components/ui/`)

| File | Purpose |
|------|---------|
| `components/ui/Button.tsx` | Reusable button with loading state and variants |
| `components/ui/Input.tsx` | Form input with label and error display |
| `components/ui/Modal.tsx` | Modal dialog with backdrop and close button |
| `components/ui/Toast.tsx` | Toast notification container |
| `components/ui/Spinner.tsx` | Loading spinner animation |
| `components/ui/index.ts` | Barrel export for all UI components |

### Layout Components (`components/layout/`)

| File | Purpose |
|------|---------|
| `components/layout/Navbar.tsx` | Navigation bar with auth state awareness |
| `components/layout/index.ts` | Barrel export for layout components |

### Hooks (`hooks/`)

| File | Purpose |
|------|---------|
| `hooks/useToast.tsx` | Toast notification context and hook |

### Pages (`app/`)

| File | Purpose | Original Template |
|------|---------|-------------------|
| `app/layout.tsx` | Root layout with Navbar, ToastProvider, footer | `templates/base.html` |
| `app/globals.css` | Global styles with Tailwind imports | `static/css/style.css` |
| `app/page.tsx` | Home page with hero section | `templates/home.html` |
| `app/signin/page.tsx` | Sign in with email/password and Google OAuth | `templates/signin.html` |
| `app/signup/page.tsx` | User registration form | `templates/signup.html` |
| `app/dashboard/page.tsx` | User data CRUD and password change | `templates/dashboard.html` |
| `app/forgot-password/page.tsx` | Password reset request form | `templates/forgot_password.html` |
| `app/reset-password/page.tsx` | Password reset with token | `templates/reset_password.html` |
| `app/verify-email/page.tsx` | Email verification status page | `templates/verify_email.html` |

### Static Assets (`public/`)

| File | Purpose |
|------|---------|
| `public/favicon.ico` | Browser favicon |
| `public/file.svg` | Next.js default icon |
| `public/globe.svg` | Next.js default icon |
| `public/next.svg` | Next.js logo |
| `public/vercel.svg` | Vercel logo |
| `public/window.svg` | Next.js default icon |

## Backend Modifications

### `learn_fastapi_auth/app.py`

Added CORS middleware to allow requests from the Next.js development server:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### `mise.toml`

Updated task definitions:

| Task | Command | Description |
|------|---------|-------------|
| `run` | Starts both servers | FastAPI (8000) + Next.js (3000) |
| `run-backend` | `.venv/bin/python main.py` | FastAPI only |
| `run-frontend` | `npm run dev` | Next.js only |

## Key Implementation Details

### 1. API Proxy Configuration

`next.config.ts` configures API rewrites to proxy `/api/*` requests to the FastAPI backend:

```typescript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: process.env.NODE_ENV === 'development'
        ? 'http://127.0.0.1:8000/api/:path*'
        : (process.env.NEXT_PUBLIC_API_URL || '') + '/api/:path*',
    },
  ];
}
```

### 2. Token Management

`lib/auth.ts` stores the access token in localStorage (same as the original JS implementation):

```typescript
const AUTH_TOKEN_KEY = 'auth_token';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}
```

### 3. Auto Token Refresh

`lib/api.ts` automatically refreshes expired access tokens using the refresh token (stored in HttpOnly cookie):

```typescript
export async function apiRequest<T = unknown>(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  // Add Authorization header
  // On 401 response, try to refresh token via /api/auth/refresh
  // Retry original request with new token
}
```

### 4. Google OAuth Flow

`lib/firebase.ts` initializes Firebase client and provides Google sign-in:

```typescript
export async function signInWithGoogle(): Promise<string> {
  const auth = getFirebaseAuth();
  const provider = new GoogleAuthProvider();
  const result = await signInWithPopup(auth, provider);
  return await result.user.getIdToken();
}
```

The ID token is then sent to `/api/auth/google` for backend verification.

### 5. Hydration Warning Suppression

`app/layout.tsx` uses `suppressHydrationWarning` on `<html>` and `<body>` to prevent errors from browser extensions that modify the DOM:

```tsx
<html lang="en" suppressHydrationWarning>
  <body className="..." suppressHydrationWarning>
```

### 6. Suspense for useSearchParams

Pages using `useSearchParams()` (reset-password, verify-email) are wrapped in `<Suspense>` to avoid hydration issues:

```tsx
export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
```

## Directory Structure

```
learn_fastapi_auth-project/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx                # Root layout
│   ├── globals.css               # Global styles
│   ├── page.tsx                  # Home page
│   ├── signin/page.tsx
│   ├── signup/page.tsx
│   ├── dashboard/page.tsx
│   ├── forgot-password/page.tsx
│   ├── reset-password/page.tsx
│   └── verify-email/page.tsx
├── components/
│   ├── layout/                   # Layout components
│   │   ├── Navbar.tsx
│   │   └── index.ts
│   └── ui/                       # Reusable UI components
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Modal.tsx
│       ├── Spinner.tsx
│       ├── Toast.tsx
│       └── index.ts
├── hooks/
│   └── useToast.tsx              # Toast context and hook
├── lib/                          # TypeScript utilities
│   ├── api.ts                    # API request wrapper
│   ├── auth.ts                   # Token management
│   ├── errors.ts                 # Error messages
│   └── firebase.ts               # Firebase client
├── types/
│   └── index.ts                  # TypeScript interfaces
├── public/                       # Static assets
├── learn_fastapi_auth/           # Python backend package
├── tests/                        # Python tests
├── docs/                         # Documentation
│
├── package.json                  # Node.js dependencies
├── pyproject.toml                # Python dependencies
├── next.config.ts                # Next.js configuration
├── tsconfig.json                 # TypeScript config
├── postcss.config.mjs            # PostCSS/Tailwind config
├── mise.toml                     # Task runner
├── .env                          # Environment variables
└── CLAUDE.md                     # Claude Code instructions
```

## Running the Application

### Development Mode

```bash
# Start both frontend and backend
mise run run

# Or start them separately
mise run run-backend    # FastAPI at http://localhost:8000
mise run run-frontend   # Next.js at http://localhost:3000
```

### Production Build

```bash
npm run build
npm run start
```

## Feature Parity Checklist

| Feature | Status |
|---------|--------|
| Home page | Implemented |
| User registration | Implemented |
| Email/password sign in | Implemented |
| Google OAuth sign in | Implemented |
| Email verification | Implemented |
| Forgot password | Implemented |
| Reset password | Implemented |
| Dashboard with user data | Implemented |
| Edit user data | Implemented |
| Change password | Implemented |
| Auto token refresh | Implemented |
| Toast notifications | Implemented |
| Responsive navbar | Implemented |
| OAuth user password restriction | Implemented |

## Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| next | 16.1.1 | React framework |
| react | 19.2.3 | UI library |
| react-dom | 19.2.3 | React DOM renderer |
| firebase | ^12.7.0 | Google OAuth client |
| zod | ^4.3.5 | Runtime type validation |

### Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| typescript | ^5 | TypeScript compiler |
| tailwindcss | ^4 | Utility-first CSS |
| @tailwindcss/postcss | ^4 | PostCSS plugin |
| eslint | ^9 | Linting |
| eslint-config-next | 16.1.1 | Next.js ESLint rules |

## Design Decision: Root-Level Structure

Initially, the Next.js frontend was placed in a `frontend/` subdirectory. This was later migrated to the root level for the following reasons:

1. **Simpler tooling**: Single `mise.toml`, single `.env`, single `CLAUDE.md`
2. **Better Claude Code workflow**: No need to manage multiple project contexts
3. **Cleaner commands**: `npm run dev` instead of `cd frontend && npm run dev`
4. **No conflicts**: Removed `/lib/` from `.gitignore` (legacy Python artifact not used by modern tools)

The Python backend remains in `learn_fastapi_auth/` which clearly distinguishes it from the frontend code at root level.
