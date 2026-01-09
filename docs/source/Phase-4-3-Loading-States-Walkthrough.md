# Phase 4-3: Loading States - Code Walkthrough

本文档详细解释加载状态功能的代码实现，帮助你理解并学会手写这些代码。

---

## 目录

1. [概念理解](#1-概念理解)
2. [CSS 实现](#2-css-实现)
3. [JavaScript 工具函数](#3-javascript-工具函数)
4. [实际应用](#4-实际应用)
5. [最佳实践](#5-最佳实践)

---

## 1. 概念理解

### 什么是 Loading State？

Loading State（加载状态）是用户界面在等待异步操作完成时的视觉反馈。它告诉用户：
- 系统正在处理请求
- 请稍等片刻
- 不要重复点击

### 为什么需要它？

1. **用户体验**：没有反馈，用户不知道点击是否成功
2. **防止重复提交**：禁用按钮避免多次请求
3. **减少焦虑**：动画让等待感觉更短

### 常见的加载状态类型

| 类型 | 用途 | 示例 |
|------|------|------|
| 按钮 Spinner | 表单提交 | "Saving..." 带旋转图标 |
| 页面遮罩 | 全局加载 | 白色半透明背景 + 大 spinner |
| 骨架屏 | 内容加载 | 灰色闪烁的占位条 |
| 内容 Loading | 局部刷新 | 区域中心的 spinner |

---

## 2. CSS 实现

### 文件：`learn_fastapi_auth/static/css/style.css`

### 2.1 基础 Spinner

```css
.spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid currentColor;
    border-radius: 50%;
    border-top-color: transparent;
    animation: spin 0.8s linear infinite;
    vertical-align: middle;
    margin-right: 6px;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}
```

**解释**：

1. **`border: 2px solid currentColor`**：
   - `currentColor` 继承父元素的文字颜色
   - 这样 spinner 会自动匹配按钮文字颜色

2. **`border-top-color: transparent`**：
   - 顶部边框透明，形成"缺口"
   - 旋转时产生 spinner 效果

3. **`animation: spin 0.8s linear infinite`**：
   - 0.8 秒一圈，匀速，无限循环

4. **`vertical-align: middle`**：
   - 与文字垂直居中对齐

### 2.2 Spinner 颜色变体

```css
.spinner-white {
    border-color: #fff;
    border-top-color: transparent;
}

.spinner-primary {
    border-color: #007bff;
    border-top-color: transparent;
}

.spinner-dark {
    border-color: #333;
    border-top-color: transparent;
}
```

**用途**：
- `.spinner-white`：用在蓝色/深色按钮内
- `.spinner-primary`：用在白色背景上
- `.spinner-dark`：用在浅色背景上

### 2.3 大号 Spinner

```css
.spinner-lg {
    width: 32px;
    height: 32px;
    border-width: 3px;
}
```

用于页面级别的加载，更醒目。

### 2.4 页面加载遮罩

```css
.page-loading {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 3000;
}

.page-loading-text {
    margin-top: 15px;
    color: #666;
    font-size: 1rem;
}
```

**解释**：

1. **`position: fixed` + 四边为 0**：
   - 覆盖整个视窗

2. **`background: rgba(255, 255, 255, 0.9)`**：
   - 半透明白色背景，可以看到底下内容

3. **`z-index: 3000`**：
   - 高于其他元素（modal 是 1500，toast 是 2000）

4. **`display: flex` + `justify-content/align-items: center`**：
   - 内容居中

### 2.5 骨架屏 (Skeleton)

```css
.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
}

.skeleton-text {
    height: 1em;
    margin-bottom: 0.5em;
}

.skeleton-text:last-child {
    width: 60%;
}

@keyframes shimmer {
    0% {
        background-position: 200% 0;
    }
    100% {
        background-position: -200% 0;
    }
}
```

**解释**：

1. **渐变背景**：
   - 三段颜色：亮-暗-亮
   - 形成"光带"效果

2. **`background-size: 200% 100%`**：
   - 背景宽度是元素的 2 倍
   - 动画移动背景位置产生"闪烁"

3. **`shimmer` 动画**：
   - 从右向左移动背景
   - 产生光芒扫过的效果

4. **`:last-child` 的 60% 宽度**：
   - 最后一行更短，看起来更自然

### 2.6 按钮加载状态

```css
.btn.loading {
    pointer-events: none;
    opacity: 0.8;
}
```

**解释**：

1. **`pointer-events: none`**：
   - 禁用所有鼠标事件
   - 比 `disabled` 更彻底

2. **`opacity: 0.8`**：
   - 轻微变暗，暗示"不可用"

---

## 3. JavaScript 工具函数

### 文件：`learn_fastapi_auth/static/js/auth.js`

### 3.1 设置按钮加载状态

```javascript
function setButtonLoading(button, loadingText = 'Loading...') {
    if (!button) return;

    // Store original text if not already stored
    if (!button.dataset.originalText) {
        button.dataset.originalText = button.textContent;
    }

    button.disabled = true;
    button.classList.add('loading');
    button.innerHTML = `<span class="spinner"></span> ${loadingText}`;
}
```

**解释**：

1. **参数检查**：`if (!button) return;` 防止空指针

2. **保存原始文本**：
   ```javascript
   button.dataset.originalText = button.textContent;
   ```
   - 存储在 `data-original-text` 属性中
   - 以便恢复时使用

3. **禁用按钮**：`button.disabled = true`

4. **添加 loading 类**：用于 CSS 样式

5. **更新内容**：
   ```javascript
   button.innerHTML = `<span class="spinner"></span> ${loadingText}`;
   ```
   - 使用模板字符串
   - 插入 spinner 元素 + 加载文本

### 3.2 重置按钮状态

```javascript
function resetButton(button, text = null) {
    if (!button) return;

    button.disabled = false;
    button.classList.remove('loading');
    button.textContent = text || button.dataset.originalText || 'Submit';
}
```

**解释**：

1. **恢复启用状态**：`button.disabled = false`

2. **移除 loading 类**

3. **恢复文本**：
   - 优先使用传入的 `text`
   - 否则使用保存的原始文本
   - 最后降级为 'Submit'

### 3.3 页面加载遮罩

```javascript
function showPageLoading(message = 'Loading...') {
    // Remove existing overlay if any
    hidePageLoading();

    const overlay = document.createElement('div');
    overlay.id = 'page-loading-overlay';
    overlay.className = 'page-loading';
    overlay.innerHTML = `
        <span class="spinner spinner-lg spinner-primary"></span>
        <span class="page-loading-text">${message}</span>
    `;
    document.body.appendChild(overlay);
    return overlay;
}

function hidePageLoading() {
    const overlay = document.getElementById('page-loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}
```

**解释**：

1. **先移除已有的**：避免重复创建

2. **动态创建元素**：
   - 使用 `document.createElement`
   - 设置 ID、类名、内容

3. **添加到 body**：`document.body.appendChild(overlay)`

4. **返回元素**：方便后续操作

5. **移除遮罩**：使用 `element.remove()` 直接删除

### 3.4 骨架屏加载

```javascript
function showSkeleton(container, lines = 3) {
    if (!container) return;

    container.innerHTML = '';
    for (let i = 0; i < lines; i++) {
        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton skeleton-text';
        container.appendChild(skeleton);
    }
}
```

**解释**：

1. **清空容器**：`container.innerHTML = ''`

2. **循环创建骨架条**：
   - 每条是一个 `<div class="skeleton skeleton-text">`
   - 添加到容器中

---

## 4. 实际应用

### 4.1 表单提交示例

```javascript
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // 验证表单...
    if (hasError) return;

    // 开始加载状态
    setButtonLoading(submitBtn, 'Signing In...');

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            // 处理成功...
        } else {
            // 处理错误...
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    } finally {
        // 无论成功失败，都重置按钮
        resetButton(submitBtn);
    }
});
```

**关键点**：

1. **在验证通过后**才设置加载状态
2. **在 `finally` 中**重置按钮（确保执行）

### 4.2 数据加载示例

```javascript
async function loadUserData() {
    const dataDisplay = document.getElementById('data-display');

    // 显示骨架屏
    if (dataDisplay) {
        showSkeleton(dataDisplay, 4);
    }

    try {
        const response = await apiRequest('/api/user-data');

        if (response.ok) {
            const data = await response.json();
            displayUserData(data.text_value);
        } else {
            displayUserData(''); // 清除骨架
        }
    } catch (error) {
        displayUserData(''); // 清除骨架
    }
}
```

**关键点**：

1. **先显示骨架**，再发请求
2. **成功和失败**都要更新显示内容

---

## 5. 最佳实践

### 5.1 何时使用加载状态

| 场景 | 推荐方式 |
|------|---------|
| 按钮提交 | 按钮 spinner + 禁用 |
| 首次加载数据 | 骨架屏 |
| 刷新数据 | 内容 loading 或小 spinner |
| 关键操作 | 页面遮罩 |

### 5.2 加载状态的持续时间

- **最短显示时间**：如果请求很快，考虑至少显示 300ms
- **超时处理**：超过 10 秒应该显示错误或重试按钮

### 5.3 代码组织

```javascript
// 好的做法：使用工具函数
setButtonLoading(button, 'Saving...');
// ...
resetButton(button);

// 不好的做法：重复代码
button.disabled = true;
button.innerHTML = '<span class="spinner"></span> Saving...';
// ...
button.disabled = false;
button.textContent = 'Save';
```

### 5.4 无障碍考虑

```html
<!-- 为屏幕阅读器添加提示 -->
<button aria-busy="true" aria-label="正在保存">
    <span class="spinner"></span> Saving...
</button>
```

---

## 总结：实现清单

1. **CSS**：
   - 基础 spinner 动画
   - 颜色和大小变体
   - 骨架屏 shimmer 效果
   - 页面遮罩样式

2. **JavaScript**：
   - `setButtonLoading()` / `resetButton()`
   - `showPageLoading()` / `hidePageLoading()`
   - `showSkeleton()`

3. **应用**：
   - 所有表单使用统一的工具函数
   - 数据加载使用骨架屏
   - `finally` 中重置状态

---

## 关键知识点

1. **CSS 动画**：
   - `@keyframes` 定义动画
   - `animation` 应用动画
   - `transform: rotate()` 旋转

2. **渐变背景动画**：
   - `linear-gradient` 创建渐变
   - `background-position` 移动产生动画

3. **数据属性**：
   - `element.dataset.xxx` 存取自定义数据
   - 用于保存/恢复按钮原始文本

4. **DOM 操作**：
   - `document.createElement()` 创建元素
   - `element.remove()` 删除元素

---

**文档完成于**: 2025-01
