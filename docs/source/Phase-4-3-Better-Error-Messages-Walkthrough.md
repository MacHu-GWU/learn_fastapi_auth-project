# Phase 4.3: Better Error Messages - Code Walkthrough

本文档详细解释 "Better Error Messages" 功能的每一处代码修改，帮助你理解实现原理并学会手写这些代码。

---

## 目录

1. [问题分析](#1-问题分析)
2. [解决方案设计](#2-解决方案设计)
3. [Step 1: 创建错误消息模块](#3-step-1-创建错误消息模块)
4. [Step 2: 在 base.html 中引入模块](#4-step-2-在-basehtml-中引入模块)
5. [Step 3: 更新 signup.html](#5-step-3-更新-signuphtml)
6. [Step 4: 更新 signin.html](#6-step-4-更新-signinhtml)
7. [Step 5: 更新 app.js](#7-step-5-更新-appjs)
8. [Step 6: 更新其他模板](#8-step-6-更新其他模板)
9. [Step 7: 编写测试](#9-step-7-编写测试)
10. [总结](#10-总结)

---

## 1. 问题分析

### 原始问题

在修改前，API 返回的错误信息直接显示给用户，例如：

```javascript
// signin.html 中的原始代码
if (data.detail === 'LOGIN_BAD_CREDENTIALS') {
    showToast('Invalid email or password', 'error');
} else if (data.detail === 'LOGIN_USER_NOT_VERIFIED') {
    showToast('Please verify your email before signing in', 'error');
} else {
    showToast(data.detail || 'Login failed', 'error');
}
```

**问题点**:
1. **代码重复**: 每个页面都要写类似的 `if-else` 判断
2. **维护困难**: 修改一条消息需要找到所有使用它的地方
3. **不一致**: 同一个错误可能在不同地方显示不同的消息
4. **扩展性差**: 添加新错误类型需要修改多个文件

---

## 2. 解决方案设计

### 设计思路

创建一个**集中式的错误消息模块**，提供：

1. **错误码到消息的映射表** (`ERROR_MESSAGES`)
2. **HTTP 状态码的备用消息** (`HTTP_STATUS_MESSAGES`)
3. **获取消息的辅助函数** (`getErrorMessage`, `getHttpErrorMessage`)
4. **字段级错误检测** (`getFieldError`)

### 架构图

```
API Response
     ↓
┌─────────────────┐
│   errors.js     │  ← 集中式错误消息模块
│                 │
│ ERROR_MESSAGES  │
│ getErrorMessage │
│ getFieldError   │
└────────┬────────┘
         ↓
   User-friendly
     Message
```

---

## 3. Step 1: 创建错误消息模块

**文件**: `learn_fastapi_auth/static/js/errors.js`

### 3.1 定义错误消息映射

```javascript
/**
 * API 错误码 → 用户友好消息的映射表
 * Key: 后端 API 返回的错误码 (detail 字段)
 * Value: 翻译后的用户友好消息
 */
const ERROR_MESSAGES = {
    // 认证相关错误
    'LOGIN_BAD_CREDENTIALS': 'Invalid email or password. Please check and try again.',
    'LOGIN_USER_NOT_VERIFIED': 'Please verify your email before signing in. Check your inbox for the verification link.',

    // 注册相关错误
    'REGISTER_USER_ALREADY_EXISTS': 'An account with this email already exists. Please sign in or use a different email.',
    'REGISTER_INVALID_PASSWORD': 'Password does not meet requirements. Please use at least 8 characters with letters and numbers.',

    // 验证相关错误
    'VERIFY_USER_BAD_TOKEN': 'Verification link is invalid or has expired. Please request a new verification email.',
    'VERIFY_USER_ALREADY_VERIFIED': 'Your email is already verified. You can sign in now.',

    // 密码重置错误
    'RESET_PASSWORD_BAD_TOKEN': 'Password reset link is invalid or has expired. Please request a new reset link.',
    'RESET_PASSWORD_INVALID_PASSWORD': 'New password does not meet requirements. Please use at least 8 characters with letters and numbers.',

    // 修改密码错误
    'CHANGE_PASSWORD_INVALID_CURRENT': 'Current password is incorrect. Please try again.',

    // 网络和服务器错误
    'NETWORK_ERROR': 'Network connection failed. Please check your internet and try again.',
    'SERVER_ERROR': 'Server encountered an error. Please try again later.',
    'TIMEOUT_ERROR': 'Request timed out. Please try again.',

    // 通用错误
    'UNKNOWN_ERROR': 'An unexpected error occurred. Please try again.'
};
```

**要点解释**:
- 使用 `const` 声明常量对象，防止意外修改
- Key 与后端返回的 `detail` 字段完全匹配
- Value 是对用户友好的消息，包含：
  - 描述问题是什么
  - 建议用户如何解决

### 3.2 定义 HTTP 状态码消息

```javascript
/**
 * HTTP 状态码 → 用户友好消息
 * 当没有具体错误码时作为备用
 */
const HTTP_STATUS_MESSAGES = {
    400: 'Invalid request. Please check your input and try again.',
    401: 'Authentication required. Please sign in.',
    403: 'Access denied. You do not have permission to perform this action.',
    404: 'The requested resource was not found.',
    429: 'Too many requests. Please wait a moment before trying again.',
    500: 'Server error. Please try again later.',
    502: 'Server is temporarily unavailable. Please try again later.',
    503: 'Service is temporarily unavailable. Please try again later.'
};
```

**为什么需要这个**:
有时 API 只返回 HTTP 状态码，没有具体的错误码，这时需要一个备用方案。

### 3.3 实现 getErrorMessage 函数

```javascript
/**
 * 从 API 错误码获取用户友好消息
 *
 * @param {string} errorCode - API 返回的错误码
 * @param {string} fallback - 可选的备用消息
 * @returns {string} 用户友好的错误消息
 */
function getErrorMessage(errorCode, fallback = null) {
    // 处理空值情况
    if (!errorCode) {
        return fallback || ERROR_MESSAGES['UNKNOWN_ERROR'];
    }

    // 查找映射表
    if (ERROR_MESSAGES[errorCode]) {
        return ERROR_MESSAGES[errorCode];
    }

    // 返回备用消息或通用消息
    return fallback || ERROR_MESSAGES['UNKNOWN_ERROR'];
}
```

**代码解读**:
1. `if (!errorCode)`: 处理 `null`, `undefined`, `''` 等空值
2. `ERROR_MESSAGES[errorCode]`: 在映射表中查找
3. `fallback || ERROR_MESSAGES['UNKNOWN_ERROR']`: 优先使用调用者提供的备用消息

**使用示例**:
```javascript
getErrorMessage('LOGIN_BAD_CREDENTIALS');
// → 'Invalid email or password. Please check and try again.'

getErrorMessage('UNKNOWN_CODE', 'Custom fallback');
// → 'Custom fallback'

getErrorMessage(null);
// → 'An unexpected error occurred. Please try again.'
```

### 3.4 实现 getFieldError 函数

```javascript
/**
 * 检查错误是否应该显示在特定表单字段旁边
 *
 * @param {string} errorCode - 错误码
 * @returns {Object|null} 包含 field 和 message 的对象，或 null
 */
function getFieldError(errorCode) {
    const fieldErrorMap = {
        'REGISTER_USER_ALREADY_EXISTS': {
            field: 'email',
            message: ERROR_MESSAGES['REGISTER_USER_ALREADY_EXISTS']
        },
        'CHANGE_PASSWORD_INVALID_CURRENT': {
            field: 'current-password',
            message: ERROR_MESSAGES['CHANGE_PASSWORD_INVALID_CURRENT']
        }
    };

    return fieldErrorMap[errorCode] || null;
}
```

**设计思想**:
某些错误更适合显示在表单字段旁边（inline），而不是显示为 toast 通知。例如：
- "邮箱已存在" 应该显示在邮箱输入框下方
- "当前密码错误" 应该显示在当前密码输入框下方

---

## 4. Step 2: 在 base.html 中引入模块

**文件**: `learn_fastapi_auth/templates/base.html`

### 修改内容

```html
<!-- 修改前 -->
<script src="/static/js/auth.js"></script>

<!-- 修改后 -->
<script src="/static/js/errors.js"></script>
<script src="/static/js/auth.js"></script>
```

**为什么这样做**:
1. `errors.js` 必须在其他 JS 文件之前加载
2. 其他文件（auth.js, app.js）才能使用 `getErrorMessage` 等函数
3. 放在 `base.html` 中确保所有页面都能使用

---

## 5. Step 3: 更新 signup.html

**文件**: `learn_fastapi_auth/templates/signup.html`

### 修改前

```javascript
if (response.ok) {
    showToast('Registration successful!...', 'success');
    // ...
} else {
    // 原始的 if-else 判断
    if (data.detail === 'REGISTER_USER_ALREADY_EXISTS') {
        showFieldError('email', 'An account with this email already exists');
    } else {
        showToast(data.detail || 'Registration failed', 'error');
    }
}
```

### 修改后

```javascript
if (response.ok) {
    showToast('Registration successful!...', 'success');
    // ...
} else {
    // 使用集中式错误处理
    const errorCode = data.detail;
    const fieldError = getFieldError(errorCode);

    if (fieldError) {
        // 字段级错误 - 显示在表单字段旁边
        showFieldError(fieldError.field, fieldError.message);
    } else {
        // 通用错误 - 显示 toast
        const message = getErrorMessage(errorCode, 'Registration failed. Please try again.');
        showToast(message, 'error');
    }
}
```

### 网络错误处理

```javascript
// 修改前
} catch (error) {
    console.error('Registration error:', error);
    showToast('An error occurred. Please try again.', 'error');
}

// 修改后
} catch (error) {
    console.error('Registration error:', error);
    showToast(getErrorMessage('NETWORK_ERROR'), 'error');
}
```

**代码逻辑流程**:

```
API 返回错误
       ↓
提取 errorCode = data.detail
       ↓
调用 getFieldError(errorCode)
       ↓
   有返回值？
    ↙    ↘
  是      否
   ↓       ↓
显示在   显示为
字段旁   toast
```

---

## 6. Step 4: 更新 signin.html

**文件**: `learn_fastapi_auth/templates/signin.html`

### 登录错误处理

```javascript
// 修改前 - 多个 if-else 分支
if (data.detail === 'LOGIN_BAD_CREDENTIALS') {
    showToast('Invalid email or password', 'error');
} else if (data.detail === 'LOGIN_USER_NOT_VERIFIED') {
    showToast('Please verify your email before signing in', 'error');
} else {
    showToast(data.detail || 'Login failed', 'error');
}

// 修改后 - 一行代码搞定
const errorCode = data.detail;
const message = getErrorMessage(errorCode, 'Login failed. Please try again.');
showToast(message, 'error');
```

### 邮箱验证错误处理

```javascript
// 修改前
if (data.detail === 'VERIFY_USER_ALREADY_VERIFIED') {
    showToast('Email already verified. Please sign in.', 'info');
} else {
    showToast('Verification failed. The link may have expired.', 'error');
}

// 修改后
const errorCode = data.detail;
// 已验证不是真正的错误，使用 info 类型
const toastType = errorCode === 'VERIFY_USER_ALREADY_VERIFIED' ? 'info' : 'error';
const message = getErrorMessage(errorCode, 'Verification failed. The link may have expired.');
showToast(message, toastType);
```

**注意点**:
- `VERIFY_USER_ALREADY_VERIFIED` 不是真正的错误
- 用 `info` 类型显示，而不是 `error` 类型
- 这种情况下仍然需要特殊判断 toast 类型

---

## 7. Step 5: 更新 app.js

**文件**: `learn_fastapi_auth/static/js/app.js`

### 加载数据错误

```javascript
// 修改前
} else {
    const error = await response.json();
    showToast(error.detail || 'Failed to load data', 'error');
}

// 修改后
} else {
    const error = await response.json();
    const message = getErrorMessage(error.detail, 'Failed to load data. Please try again.');
    showToast(message, 'error');
}
```

### 保存数据错误

```javascript
// 修改前
} else {
    const error = await response.json();
    showToast(error.detail || 'Failed to save data', 'error');
}

// 修改后
} else {
    const error = await response.json();
    const message = getErrorMessage(error.detail, 'Failed to save data. Please try again.');
    showToast(message, 'error');
}
```

### 修改密码错误

```javascript
// 修改前 - 使用 if-else
if (error.detail === 'CHANGE_PASSWORD_INVALID_CURRENT') {
    showPasswordFieldError('current-password', 'Current password is incorrect');
} else {
    showToast(error.detail || 'Failed to change password', 'error');
}

// 修改后 - 使用 getFieldError
const errorCode = error.detail;
const fieldError = getFieldError(errorCode);

if (fieldError) {
    showPasswordFieldError(fieldError.field, fieldError.message);
} else {
    const message = getErrorMessage(errorCode, 'Failed to change password. Please try again.');
    showToast(message, 'error');
}
```

---

## 8. Step 6: 更新其他模板

### forgot_password.html

只需更新网络错误处理：

```javascript
// 修改前
showToast('An error occurred. Please try again.', 'error');

// 修改后
showToast(getErrorMessage('NETWORK_ERROR'), 'error');
```

**注意**: 忘记密码页面的成功消息是故意模糊的（安全考虑），不需要修改。

### reset_password.html

```javascript
// 修改前
if (data.detail === 'RESET_PASSWORD_BAD_TOKEN') {
    showToast('Reset link has expired or is invalid...', 'error');
} else if (data.detail === 'RESET_PASSWORD_INVALID_PASSWORD') {
    showToast('Invalid password...', 'error');
} else {
    showToast(data.detail || 'Password reset failed...', 'error');
}

// 修改后
const errorCode = data.detail;
const message = getErrorMessage(errorCode, 'Password reset failed. Please try again.');
showToast(message, 'error');
```

---

## 9. Step 7: 编写测试

**文件**: `learn_fastapi_auth/static/js/errors.test.js`

### 测试 getErrorMessage

```javascript
function testGetErrorMessage() {
    // 测试已知错误码
    assertEqual(
        getErrorMessage('LOGIN_BAD_CREDENTIALS'),
        'Invalid email or password. Please check and try again.',
        'LOGIN_BAD_CREDENTIALS returns correct message'
    );

    // 测试未知错误码 + 备用消息
    assertEqual(
        getErrorMessage('UNKNOWN_CODE', 'Custom fallback'),
        'Custom fallback',
        'Unknown code with fallback returns fallback'
    );

    // 测试空值
    assertEqual(
        getErrorMessage(null),
        'An unexpected error occurred. Please try again.',
        'Null input returns generic message'
    );
}
```

### 测试 getFieldError

```javascript
function testGetFieldError() {
    // 测试字段级错误
    const registerError = getFieldError('REGISTER_USER_ALREADY_EXISTS');
    assertEqual(registerError.field, 'email', 'Has correct field');

    // 测试非字段级错误
    assertNull(
        getFieldError('LOGIN_BAD_CREDENTIALS'),
        'Non-field error returns null'
    );
}
```

### 运行测试

在浏览器控制台中：

```javascript
runAllTests();
```

---

## 10. 总结

### 修改文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `errors.js` | 新建 | 错误消息模块 |
| `errors.test.js` | 新建 | 单元测试 |
| `base.html` | 修改 | 引入 errors.js |
| `signup.html` | 修改 | 使用 getErrorMessage, getFieldError |
| `signin.html` | 修改 | 使用 getErrorMessage |
| `app.js` | 修改 | 使用 getErrorMessage, getFieldError |
| `forgot_password.html` | 修改 | 使用 getErrorMessage |
| `reset_password.html` | 修改 | 使用 getErrorMessage |

### 关键学习点

1. **集中式管理**: 将相关逻辑放在一个模块中，便于维护
2. **映射表模式**: 使用对象作为映射表，用 key 查找 value
3. **备用值模式**: 函数参数支持备用值，增加灵活性
4. **关注点分离**: 字段级错误和 toast 错误分开处理

### 扩展建议

如果需要支持多语言，可以这样扩展：

```javascript
const ERROR_MESSAGES_ZH = {
    'LOGIN_BAD_CREDENTIALS': '邮箱或密码不正确，请检查后重试。',
    // ...
};

const ERROR_MESSAGES_EN = {
    'LOGIN_BAD_CREDENTIALS': 'Invalid email or password. Please check and try again.',
    // ...
};

// 根据用户语言选择
const ERROR_MESSAGES = navigator.language.startsWith('zh')
    ? ERROR_MESSAGES_ZH
    : ERROR_MESSAGES_EN;
```

---

**文档完成**
