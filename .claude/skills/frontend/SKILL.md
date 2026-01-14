---
name: frontend-developer
description: "Frontend codebase guide for Next.js App Router architecture. Use when working on: pages (home, auth, dashboard), components (ui, layout, saas, user), API integration (lib/api.ts), authentication (lib/auth.ts, Firebase OAuth), constants (api endpoints, routes, messages), TypeScript types. Actions: find files, understand architecture, locate components, navigate codebase."
---

# Frontend Developer Guide

This skill helps developers understand and navigate the frontend codebase architecture.

## When to Use This Skill

Use this skill when you need to:
- Understand the frontend architecture
- Find where specific files or components are located
- Add new pages, components, or API integrations
- Modify authentication flow or UI components

## Quick Reference

| Task | Location |
|------|----------|
| Modify homepage | `app/(home)/page.tsx` |
| Modify login/signup flow | `app/(auth)/` |
| Modify user dashboard | `app/(saas)/dashboard/page.tsx` |
| Add new API endpoint | `constants/api.ts` |
| Add new route | `constants/routes.ts` |
| Modify error messages | `constants/messages.ts` |
| Add UI component | `components/ui/` |
| Modify navbar | `components/layout/Navbar.tsx` |

---

## Architecture Overview

Read the full architecture documentation:

```bash
# View the Frontend Overview documentation
cat docs/source/02-Maintainer-Guide/03-Frontend/01-Frontend-Overview/index.rst
```

### Layer Structure (Outside → Inside)

1. **Next.js App Router** (`app/`)
   - Page routing entry point
   - Route Groups for code organization

2. **Page Components**
   - `(home)/` - Homepage module
   - `(auth)/` - Auth module (signin, signup, password reset, email verification)
   - `(saas)/` - SaaS application module (dashboard)

3. **Component Layer** (`components/`)
   - `ui/` - Reusable atomic components (Button, Input, Modal, Spinner, Toast)
   - `layout/` - Layout components (Navbar)
   - `saas/`, `user/` - Business components

4. **Utility Layer**
   - `lib/` - API requests, token management, OAuth
   - `hooks/` - Custom React hooks
   - `constants/` - Centralized constants
   - `types/` - TypeScript type definitions

---

## Directory Structure

### Root Directories

| Path | Responsibility |
|------|----------------|
| `app/` | Next.js App Router pages and routes |
| `components/` | React component library |
| `lib/` | Utility functions (API, auth, Firebase) |
| `hooks/` | Custom React hooks |
| `constants/` | Centralized constants |
| `types/` | TypeScript types |
| `config/` | Frontend configuration |

### Page Modules (`app/`)

Uses Route Groups (parenthesized directory names don't affect URL):

| Module | Responsibility |
|--------|----------------|
| `(home)/` | Homepage with welcome info and CTA buttons |
| `(auth)/` | Auth flow: signin, signup, forgot-password, reset-password, verify-email |
| `(saas)/` | SaaS features: dashboard, data management, account settings |
| `layout.tsx` | Root layout with Navbar, Footer, ToastProvider |
| `globals.css` | Global styles |

### Component Layer (`components/`)

**UI Components** (`ui/`)
- `Button.tsx` - Button with variants, loading state
- `Input.tsx` - Input with label, error display
- `Modal.tsx` - Modal dialog
- `Spinner.tsx` - Loading spinner
- `Toast.tsx` - Toast notifications

**Business Components**
- `layout/Navbar.tsx` - Navigation bar
- `saas/UserDataCard.tsx` - User data display card
- `saas/EditDataModal.tsx` - Edit data modal
- `user/AccountSettingsCard.tsx` - Account settings
- `user/ChangePasswordModal.tsx` - Password change modal

### Utility Layer

| Module | Responsibility |
|--------|----------------|
| `lib/api.ts` | API request wrapper with auto Authorization header and token refresh |
| `lib/auth.ts` | Token management, login state check, form validation |
| `lib/firebase.ts` | Google OAuth (Firebase) integration |
| `hooks/useToast.tsx` | Toast notification hook and context |
| `constants/api.ts` | API endpoint constants |
| `constants/routes.ts` | Frontend route constants |
| `constants/messages.ts` | Error message mappings |
| `constants/auth.ts` | Auth constants (localStorage keys, validation rules) |

---

## Design Patterns

### Route Groups Pattern
Directory names with parentheses (e.g., `(auth)`) don't affect URL paths. Used purely for code organization. Each Route Group can have its own `layout.tsx`.

### Component Layering
1. **Atomic** (`ui/`) - Smallest, highly reusable base components
2. **Layout** (`layout/`) - Page structure components
3. **Business** (`saas/`, `user/`) - Domain-specific composite components
4. **Page** (`app/`) - Assemble business components, handle routing and data fetching

### Centralized Constants
All hardcoded values in `constants/` directory. API endpoints, routes, error messages, validation rules managed centrally.

### API Request Wrapper
`lib/api.ts` provides unified API request function:
- Auto-adds Authorization header
- Auto-handles 401 errors with token refresh
- Unified error handling

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Next.js 16 (App Router) | React framework with SSR/SSG |
| TypeScript | Type safety |
| Tailwind CSS | Atomic CSS framework |
| Firebase | Google OAuth authentication |

---

## Common Tasks

### Adding a New Page

1. Determine module: `(home)`, `(auth)`, or `(saas)`
2. Create `new-page/page.tsx` in the appropriate directory
3. Add route constant to `constants/routes.ts`
4. Add navbar link in `components/layout/Navbar.tsx` if needed

### Adding a New API Call

1. Add endpoint constant to `constants/api.ts`
2. Define request/response types in `types/index.ts`
3. Use `apiRequest()` from `lib/api.ts`

### Adding a New UI Component

1. Create component in `components/ui/`
2. Export from `components/ui/index.ts`
3. Import via `import { Component } from '@/components/ui'`

### Adding Error Messages

1. Add mapping to `ERROR_MESSAGES` in `constants/messages.ts`
2. For field-level errors, add to `FIELD_ERROR_MAP`
