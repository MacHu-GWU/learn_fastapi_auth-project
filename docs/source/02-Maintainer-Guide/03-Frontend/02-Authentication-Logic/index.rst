.. _authentication-logic:

Authentication Logic / 认证逻辑
==============================================================================
本文档详细说明了用户认证系统的设计逻辑，包括邮箱/密码登录与 OAuth 登录的交互关系。


概述
------------------------------------------------------------------------------
系统支持两种登录方式：

1. **邮箱/密码登录**：用户使用邮箱注册并设置密码
2. **OAuth 登录**：用户通过 Google 账号登录（Firebase Authentication）

这两种方式可以共存于同一个用户账号，但需要特殊处理以保证用户体验。


核心问题：用户如何登录与密码管理
------------------------------------------------------------------------------

场景分析
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**场景 1：先邮箱注册，后 Google 登录**

初始状态（邮箱注册后）:

- ``email``: you@gmail.com
- ``hashed_password``: 用户设置的密码
- ``firebase_uid``: NULL
- ``has_set_password``: TRUE

Google OAuth 登录后（系统自动关联同邮箱账号）:

- ``email``: you@gmail.com
- ``hashed_password``: 用户设置的密码（不变）
- ``firebase_uid``: "abc123xyz..."（新增关联）
- ``has_set_password``: TRUE（不变）

结果：

- 用户可以继续用两种方式登录
- 用户可以修改密码（因为 ``has_set_password = TRUE``）

**场景 2：先 Google 登录，后邮箱注册**

Google OAuth 首次登录时自动创建账号:

- ``email``: you@gmail.com
- ``hashed_password``: 随机生成（用户不知道）
- ``firebase_uid``: "abc123xyz..."
- ``has_set_password``: FALSE

结果：

- 用户尝试用同邮箱注册会失败（邮箱已存在）
- 用户只能用 Google 登录
- 用户可以通过 "Set Password" 功能设置密码，之后两种方式都可登录


关键字段：has_set_password
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``has_set_password`` 字段是解决以上问题的核心：

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 值
     - 含义
   * - ``TRUE``
     - 用户已设置自己的密码（可以修改密码）
   * - ``FALSE``
     - 用户只用 OAuth 登录，未设置密码（显示 "Set Password"）

**设置时机：**

- 邮箱注册：``has_set_password = TRUE``
- OAuth 创建新用户：``has_set_password = FALSE``
- 用户使用 "Set Password"：``has_set_password = TRUE``
- 用户使用 "Forgot Password" 重置：``has_set_password = TRUE``


API 端点
------------------------------------------------------------------------------

密码管理相关端点
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - 端点
     - 方法
     - 说明
   * - ``/api/auth/change-password``
     - POST
     - 修改密码（需要当前密码验证）
   * - ``/api/auth/set-password``
     - POST
     - 设置密码（仅 OAuth 用户，无需当前密码）
   * - ``/api/auth/forgot-password``
     - POST
     - 请求密码重置邮件
   * - ``/api/auth/reset-password``
     - POST
     - 通过重置链接设置新密码


关键代码
------------------------------------------------------------------------------

后端：User Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   :caption: learn_fastapi_auth/models.py

    class User(SQLAlchemyBaseUserTableUUID, Base):
        # ... 其他字段 ...

        # Tracks whether user has set their own password
        # True: user registered with email/password OR OAuth user later set a password
        # False: user only signed up via OAuth (has random generated password)
        has_set_password: orm.Mapped[bool] = orm.mapped_column(
            sa.Boolean, default=False, server_default=sa.text("false")
        )

后端：UserRead Schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   :caption: learn_fastapi_auth/schemas.py

    class UserRead(schemas.BaseUser[uuid.UUID]):
        is_oauth_user: bool = False

        @classmethod
        def model_validate(cls, obj, **kwargs):
            """Override to compute is_oauth_user from has_set_password."""
            if hasattr(obj, "has_set_password"):
                data = {
                    # ... 其他字段 ...
                    # is_oauth_user = True 表示用户未设置密码，不能使用 Change Password
                    "is_oauth_user": not obj.has_set_password,
                }
                return super().model_validate(data, **kwargs)
            return super().model_validate(obj, **kwargs)

后端：Set Password 端点
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   :caption: learn_fastapi_auth/routers/auth_routes.py

    @router.post("/api/auth/set-password")
    async def set_password(
        request: Request,
        data: SetPasswordRequest,
        user: User = Depends(current_active_user),
        user_manager=Depends(get_user_manager),
    ):
        """Set password for OAuth users who haven't set one."""
        # Check if user already has a password set
        if user.has_set_password:
            raise HTTPException(
                status_code=400,
                detail="SET_PASSWORD_ALREADY_HAS_PASSWORD",
            )

        # Set the new password
        hashed_password = user_manager.password_helper.hash(data.new_password)
        user.hashed_password = hashed_password
        user.has_set_password = True

        session = user_manager.user_db.session
        session.add(user)
        await session.commit()

        return MessageResponse(message="Password set successfully")

前端：Navbar 逻辑
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: typescript
   :caption: components/layout/Navbar.tsx

    const handlePasswordAction = () => {
      setDropdownOpen(false);
      if (userInfo?.is_oauth_user) {
        // OAuth user without password - show Set Password modal
        setSetPasswordModalOpen(true);
      } else {
        // User with password - show Change Password modal
        setChangePasswordModalOpen(true);
      }
    };


数据库迁移
------------------------------------------------------------------------------

如果是新项目，直接使用 ``create_all`` 即可。

对于已有数据的生产环境，需要手动执行以下 SQL：

.. code-block:: sql

    -- 添加新字段
    ALTER TABLE users ADD COLUMN has_set_password BOOLEAN DEFAULT FALSE;

    -- 为已有邮箱注册用户设置 TRUE（假设没有 firebase_uid 表示邮箱注册）
    UPDATE users SET has_set_password = TRUE WHERE firebase_uid IS NULL;

    -- 验证
    SELECT email, firebase_uid, has_set_password FROM users;


用户体验流程
------------------------------------------------------------------------------

**路径 A：邮箱/密码注册**

1. 用户使用邮箱和密码注册
2. 系统设置 ``has_set_password = TRUE``
3. 用户登录后在右上角下拉菜单看到 "Change password"
4. 修改密码时需要输入当前密码验证

**路径 B：Google OAuth 登录**

1. 用户使用 Google 账号登录
2. 系统自动创建账号，设置 ``has_set_password = FALSE``
3. 用户登录后在右上角下拉菜单看到 "Set password"
4. 设置密码时无需输入当前密码（因为用户不知道随机生成的密码）
5. 设置成功后，系统更新 ``has_set_password = TRUE``
6. 此后用户可以用两种方式登录，密码操作变为 "Change password"

**路径 C：混合场景（先邮箱注册，后 Google 登录）**

1. 用户先用邮箱/密码注册，``has_set_password = TRUE``
2. 后来用同邮箱的 Google 账号登录
3. 系统自动关联 ``firebase_uid``，但 ``has_set_password`` 保持 TRUE
4. 用户始终看到 "Change password"，可以正常修改密码


设计决策
------------------------------------------------------------------------------

**为什么不用 firebase_uid 判断？**

早期实现使用 ``firebase_uid is not None`` 来判断是否为 OAuth 用户。但这有问题：

- 邮箱注册用户后来用 Google 登录（同邮箱）会被关联 firebase_uid
- 此时 ``firebase_uid is not None = True``，但用户明明有密码

**正确的判断逻辑：**

- ``is_oauth_user`` = 用户是否 **没有设置过** 自己的密码
- 而不是 = 用户是否 **有** firebase_uid

**订阅管理影响：**

无论用户用什么方式登录，``user_id`` 始终不变。订阅、支付等数据都关联到 ``user_id``，不受登录方式影响。
