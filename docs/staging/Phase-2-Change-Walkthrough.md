# Phase 2 Code Walkthrough: Frontend Pages

This document explains all code changes made in Phase 2, helping you understand how to implement frontend pages in a FastAPI project.

---

## Overview

Phase 2 adds a complete frontend UI to the authentication system. The key concepts:

1. **Jinja2 Templates** - Server-side HTML rendering
2. **Static Files** - CSS and JavaScript served by FastAPI
3. **Page Router** - Routes that return HTML instead of JSON
4. **Client-side Auth** - JavaScript manages tokens in localStorage

---

## 1. Path Management

**File**: `learn_fastapi_auth/paths.py`

Added two new paths for templates and static files:

```python
# In PathEnum class
dir_templates = dir_package / "templates"
dir_static = dir_package / "static"

# Module-level exports
dir_templates = path_enum.dir_templates
dir_static = path_enum.dir_static
```

**Why**: Centralizing paths makes it easy to reference directories consistently throughout the project.

---

## 2. Application Setup

**File**: `learn_fastapi_auth/app.py`

### New Imports

```python
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .paths import dir_static, dir_templates
from .routers import pages_router
```

### Mount Static Files

```python
app.mount("/static", StaticFiles(directory=str(dir_static)), name="static")
```

This makes all files in `static/` accessible via `/static/` URL prefix. For example:
- `static/css/style.css` -> `http://localhost:8000/static/css/style.css`

### Initialize Templates

```python
templates = Jinja2Templates(directory=str(dir_templates))
```

### Include Page Router

```python
app.include_router(pages_router)
```

**Removed**: The old JSON root route (`@app.get("/")`) since pages_router now handles it.

---

## 3. Page Router

**File**: `learn_fastapi_auth/routers/pages.py`

This module defines routes that return HTML pages:

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(dir_templates))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")
```

**Key Points**:
- `response_class=HTMLResponse` tells FastAPI this returns HTML
- `request: Request` is required for template rendering
- `TemplateResponse(request, "template_name.html")` renders the template

---

## 4. Base Template

**File**: `learn_fastapi_auth/templates/base.html`

The base template defines the common structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>{% block title %}FastAPI Auth{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav class="navbar">
        <!-- Navigation links with IDs for JS manipulation -->
        <a href="/signin" id="signin-link">Sign In</a>
        <a href="/signup" id="signup-link">Create Account</a>
        <span id="user-email" style="display: none;"></span>
        <button id="logout-btn" style="display: none;">Logout</button>
    </nav>

    <main>{% block content %}{% endblock %}</main>
    
    <div id="toast" class="toast"></div>
    
    <script src="/static/js/auth.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

**Key Points**:
- `{% block name %}{% endblock %}` - Defines replaceable sections
- Static files referenced with `/static/` prefix
- Navigation elements have IDs for JavaScript manipulation
- Toast container for notifications
- `auth.js` loaded on every page

---

## 5. Child Templates

**File**: `learn_fastapi_auth/templates/index.html`

```html
{% extends "base.html" %}

{% block title %}Home - FastAPI Auth{% endblock %}

{% block content %}
<section class="hero">
    <h1>Hello World!</h1>
    <p>Welcome to FastAPI User Authentication Project</p>
</section>
{% endblock %}
```

**Key Points**:
- `{% extends "base.html" %}` - Inherits from base template
- `{% block content %}` - Replaces the content block

---

## 6. Form Pages

**File**: `learn_fastapi_auth/templates/signup.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="auth-container">
    <form id="signup-form">
        <input type="email" id="email" required>
        <div class="error-message" id="email-error"></div>
        <!-- More fields... -->
        <button type="submit">Create Account</button>
    </form>
</div>
{% endblock %}

{% block extra_js %}
<script>
document.getElementById('signup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    // Validation and API call...
});
</script>
{% endblock %}
```

**Key Points**:
- Form has `id` for JavaScript access
- Each input has corresponding error div
- JavaScript in `extra_js` block handles form submission
- Form submits via JavaScript (not traditional form POST)

---

## 7. Authentication JavaScript

**File**: `learn_fastapi_auth/static/js/auth.js`

### Token Management

```javascript
const AUTH_TOKEN_KEY = 'auth_token';

function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
}

function isLoggedIn() {
    return !!getToken();
}
```

### Navigation Update

```javascript
function updateNavigation() {
    if (isLoggedIn()) {
        document.getElementById('signin-link').style.display = 'none';
        document.getElementById('signup-link').style.display = 'none';
        document.getElementById('user-email').style.display = 'inline';
        document.getElementById('logout-btn').style.display = 'inline';
    } else {
        // Reverse the above
    }
}
```

### API Helper

```javascript
async function apiRequest(url, options = {}) {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json' };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, { ...options, headers });
    
    if (response.status === 401) {
        removeToken();
        window.location.href = '/signin?error=session_expired';
    }
    
    return response;
}
```

### Toast Notifications

```javascript
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.classList.remove('show'), 3000);
}
```

---

## 8. App Page JavaScript

**File**: `learn_fastapi_auth/static/js/app.js`

### Auth Check on Load

```javascript
document.addEventListener('DOMContentLoaded', async () => {
    if (!isLoggedIn()) {
        window.location.href = '/signin?error=login_required';
        return;
    }
    await loadUserData();
});
```

### Load Data

```javascript
async function loadUserData() {
    const response = await apiRequest('/api/user-data');
    if (response.ok) {
        const data = await response.json();
        displayUserData(data.text_value);
    }
}
```

### Save Data

```javascript
async function saveUserData() {
    const newData = document.getElementById('edit-textarea').value;
    
    const response = await apiRequest('/api/user-data', {
        method: 'PUT',
        body: JSON.stringify({ text_value: newData })
    });
    
    if (response.ok) {
        // Update display, close modal, show success toast
    }
}
```

---

## 9. CSS Styling

**File**: `learn_fastapi_auth/static/css/style.css`

Key CSS patterns used:

### Flexbox Layout

```css
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
```

### Card Component

```css
.auth-container {
    max-width: 400px;
    margin: 40px auto;
    padding: 40px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
```

### Toast Animation

```css
.toast {
    position: fixed;
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.3s ease;
}

.toast.show {
    opacity: 1;
    transform: translateY(0);
}
```

### Modal Overlay

```css
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: none;
}

.modal-overlay.show {
    display: flex;
    justify-content: center;
    align-items: center;
}
```

---

## 10. Tests

**File**: `tests/test_app.py`

Added TestPageRoutes class:

```python
class TestPageRoutes:
    async def test_signup_page(self, client: AsyncClient):
        response = await client.get("/signup")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Create Account" in response.text
```

Updated TestRoot to check for HTML:

```python
async def test_root(self, client: AsyncClient):
    response = await client.get("/")
    assert "Hello World" in response.text
```

---

## Summary

| Concept | Implementation |
|---------|----------------|
| Templates | Jinja2 with `{% extends %}` inheritance |
| Static Files | `app.mount("/static", StaticFiles(...))` |
| Page Routes | APIRouter returning `TemplateResponse` |
| Auth State | localStorage + JavaScript navigation update |
| API Calls | fetch() with Bearer token header |
| Notifications | CSS toast with JS show/hide |
| Modals | CSS overlay with JS toggle |

---

**End of Walkthrough**
