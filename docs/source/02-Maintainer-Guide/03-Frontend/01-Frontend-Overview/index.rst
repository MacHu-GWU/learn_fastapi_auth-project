.. _Frontend-Overview:

Frontend Overview
==============================================================================

概述
------------------------------------------------------------------------------
前端基于 **Next.js 16** 构建，采用 App Router 架构，使用 TypeScript 确保类型安全。整体设计遵循组件化、模块化原则，职责清晰。


整体架构
------------------------------------------------------------------------------
用户请求从外到内经过以下层次：

1. **Next.js App Router** (``app/``)

   - 页面路由入口，处理 URL 到组件的映射
   - 使用 Route Groups 按功能模块组织代码

2. **页面组件层**

   - ``(home)/`` - 首页模块
   - ``(auth)/`` - 认证模块 (登录、注册、密码重置等)
   - ``(saas)/`` - SaaS 应用模块 (用户仪表盘)

3. **组件层** (``components/``)

   - ``ui/`` - 通用 UI 原子组件 (Button, Input, Modal 等)
   - ``layout/`` - 布局组件 (Navbar)
   - ``saas/``, ``user/`` - 业务组件

4. **工具层**

   - ``lib/`` - API 请求、Token 管理、OAuth 集成
   - ``hooks/`` - 自定义 React Hooks
   - ``constants/`` - 集中管理的常量
   - ``types/`` - TypeScript 类型定义


目录结构
------------------------------------------------------------------------------

根目录
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 路径
     - 职责
   * - ``app/``
     - Next.js App Router 页面，包含所有路由和页面组件
   * - ``components/``
     - React 组件库，按功能分类
   * - ``lib/``
     - 工具函数库 (API 请求、Token 管理、Firebase OAuth)
   * - ``hooks/``
     - 自定义 React Hooks
   * - ``constants/``
     - 集中管理的常量 (API 端点、路由、错误消息)
   * - ``types/``
     - TypeScript 类型定义
   * - ``config/``
     - 前端配置文件


页面模块 ``app/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
采用 Route Groups 组织，括号目录名不影响 URL 路径：

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 模块
     - 职责
   * - ``(home)/``
     - 首页，展示欢迎信息和 CTA 按钮
   * - ``(auth)/``
     - 认证流程：登录、注册、忘记密码、重置密码、邮箱验证
   * - ``(saas)/``
     - SaaS 应用功能：用户仪表盘、数据管理、账户设置
   * - ``layout.tsx``
     - 根布局，包含 Navbar、Footer、ToastProvider
   * - ``globals.css``
     - 全局样式


组件层 ``components/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
按复用程度和功能域划分：

**通用组件**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 目录
     - 职责
   * - ``ui/``
     - 可复用的原子组件：Button, Input, Modal, Spinner, Toast

**业务组件**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 目录
     - 职责
   * - ``layout/``
     - 布局组件：Navbar
   * - ``saas/``
     - SaaS 业务组件：UserDataCard, EditDataModal
   * - ``user/``
     - 用户相关组件：AccountSettingsCard, ChangePasswordModal


工具层
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 模块
     - 职责
   * - ``lib/api.ts``
     - API 请求封装，自动添加 Authorization header，处理 Token 刷新
   * - ``lib/auth.ts``
     - Token 管理、登录状态检查、表单验证函数
   * - ``lib/firebase.ts``
     - Google OAuth (Firebase) 集成
   * - ``hooks/useToast.tsx``
     - Toast 通知 Hook 和 Context
   * - ``constants/api.ts``
     - API 端点常量
   * - ``constants/routes.ts``
     - 前端路由常量
   * - ``constants/messages.ts``
     - 错误消息映射
   * - ``constants/auth.ts``
     - 认证相关常量 (localStorage 键名、验证规则)


设计模式
------------------------------------------------------------------------------

Route Groups 模式
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
使用 Next.js Route Groups 特性 (目录名带括号) 组织代码。括号不影响 URL，纯粹用于代码分组。每个 Route Group 可以有独立的布局，便于按功能模块管理代码。

组件分层模式
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
组件按复用程度分层：

1. **原子组件** (``ui/``) - 最小粒度、高复用的基础组件
2. **布局组件** (``layout/``) - 页面结构组件
3. **业务组件** (``saas/``, ``user/``) - 特定功能域的复合组件
4. **页面组件** (``app/``) - 组装业务组件，处理路由和数据获取

常量集中管理模式
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
所有硬编码值集中在 ``constants/`` 目录。API 端点、路由路径、错误消息、验证规则等统一管理，便于维护和修改。

API 请求封装模式
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``lib/api.ts`` 封装了统一的 API 请求函数：

- 自动添加 Authorization header
- 自动处理 401 错误并尝试刷新 Token
- 统一的错误处理逻辑


技术栈
------------------------------------------------------------------------------
.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 技术
     - 用途
   * - Next.js 16 (App Router)
     - React 框架，支持服务端渲染和静态生成
   * - TypeScript
     - 类型安全
   * - Tailwind CSS
     - 原子化 CSS 框架
   * - Firebase
     - Google OAuth 认证
