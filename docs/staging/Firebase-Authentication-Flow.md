# Firebase Authentication Flow

This document explains how Firebase OAuth login works in this project, from token verification to user session management.

## Overview

Firebase acts as a middleman between your app and OAuth providers (Google, Apple, etc.). After Firebase verification, the backend creates a local user record and issues its own JWT for subsequent authentication.

```
+-----------+     +----------+     +----------------+     +-----------+
|  Frontend | --> | Firebase | --> | OAuth Provider | --> |  Backend  |
|  (App)    |     |  Auth    |     | (Google/Apple) |     | (FastAPI) |
+-----------+     +----------+     +----------------+     +-----------+
      |                |                   |                    |
      |  1. User clicks "Sign in with Google"                   |
      |--------------->|                   |                    |
      |                |  2. Redirect to   |                    |
      |                |     Google login  |                    |
      |                |------------------>|                    |
      |                |                   |                    |
      |                |  3. User logs in, |                    |
      |                |     Google returns|                    |
      |                |     auth code     |                    |
      |                |<------------------|                    |
      |                |                   |                    |
      |  4. Firebase returns ID Token (JWT)                     |
      |<---------------|                   |                    |
      |                                                         |
      |  5. Frontend sends ID Token to your backend             |
      |-------------------------------------------------------->|
      |                                                         |
      |                    6. Backend verifies token with       |
      |                       Firebase Admin SDK                |
      |                                                         |
      |  7. Backend creates/finds local user, returns your JWT  |
      |<--------------------------------------------------------|
```

## Code Flow Explanation

### Step 1: Frontend Sends Firebase ID Token

After user signs in with Google/Apple via Firebase JS SDK, the frontend calls:

```
POST /api/auth/firebase
Content-Type: application/json

{
    "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

### Step 2: Backend Verifies Token

In [auth_routes.py](../../learn_fastapi_auth/routers/auth_routes.py) `firebase_login` function:

```python
# Verify Firebase token (line 270-271)
decoded_token = verify_firebase_token(data.id_token)
user_info = get_user_info_from_token(decoded_token)
```

The `verify_firebase_token` function:
1. Checks the token signature using Firebase's public keys
2. Verifies the token hasn't expired
3. Verifies the token was issued for your Firebase project

### Step 3: Extract User Information

The `user_info` object contains:

| Field | Description | Example |
|-------|-------------|---------|
| `firebase_uid` | Unique Firebase user ID | `"abc123xyz"` |
| `email` | User's email from OAuth provider | `"user@gmail.com"` |
| `email_verified` | Whether provider verified email | `True` |
| `name` | Display name (may be None for Apple) | `"John Doe"` |
| `picture` | Profile picture URL (may be None) | `"https://..."` |
| `provider` | OAuth provider identifier | `"google.com"` |

**Where does the email come from?**

Google provides the user's email to Firebase during OAuth. Firebase includes it in the ID Token claims.

### Step 4: Find or Create User

The backend uses a three-step lookup strategy:

```python
# Step 1: Find by firebase_uid
result = await session.execute(
    select(User).where(User.firebase_uid == firebase_uid)
)
user = result.scalar_one_or_none()

if user is None:
    # Step 2: Find by email (user may have registered with password first)
    result = await session.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        # Case A: Found by email → Link Firebase UID to existing user
        user.firebase_uid = firebase_uid
    else:
        # Case B: Not found → Create new user
        user = User(
            email=email,
            hashed_password=hashed_password,  # Random password
            is_verified=True,  # Firebase verified the email
            firebase_uid=firebase_uid,
        )
```

**Why create a "virtual password"?**

The `fastapi-users` library requires `hashed_password` to be non-empty. Since OAuth users don't need a password, we generate a random one:

```python
# Generate random password (user will never use it)
random_password = secrets.token_urlsafe(32)  # e.g., "x7_kL9mN2pQ..."

# Hash and store
password_helper = PasswordHelper()
hashed_password = password_helper.hash(random_password)
```

This password:
- User **doesn't know** (randomly generated)
- User **doesn't need** (they use Google login)
- Only exists to satisfy database schema requirements

### Step 5: Issue Your Own JWT

After finding/creating the user, the backend issues its own JWT:

```python
# Generate your own JWT access token
jwt_strategy = get_jwt_strategy()
access_token = await jwt_strategy.write_token(user)

# Create refresh token and set as HttpOnly cookie
refresh_token_str = await create_refresh_token(
    session, user.id, one.env.refresh_token_lifetime
)
```

## Subsequent Authentication

**Key Point: Firebase Token is only used once (during login). All subsequent requests use your own JWT.**

```
┌─────────────────────────────────────────────────────────┐
│  Token Lifecycle:                                       │
│                                                         │
│  Login:  Firebase Token ──verify──> Your JWT            │
│                                ↓                        │
│  After:  Your JWT ──verify──> Access API                │
│          (Firebase Token is no longer used)             │
└─────────────────────────────────────────────────────────┘
```

### How the App Knows User is Logged In

Subsequent API requests include the JWT in the Authorization header:

```
GET /api/users/me
Authorization: Bearer <your_jwt>
```

FastAPI's `current_active_user` dependency validates the JWT:

```python
@router.get("/api/users/me")
async def get_current_user(
    user: User = Depends(current_active_user),  # Validates JWT
):
    return user
```

This works identically for both:
- Password-based login users
- Firebase OAuth login users

## Summary Table

| Step | What Happens | Code Location |
|------|--------------|---------------|
| 1 | Frontend sends Firebase ID Token | Request body |
| 2 | Verify Firebase Token | `auth_routes.py:270` |
| 3 | Extract user info (including email) | `auth_routes.py:271` |
| 4 | Find or create User record | `auth_routes.py:294-336` |
| 5 | Generate your own JWT | `auth_routes.py:338-340` |
| 6 | Set Refresh Token cookie | `auth_routes.py:355-356` |
| 7 | Subsequent requests use your JWT | `current_active_user` dependency |

## Related Files

- [learn_fastapi_auth/auth/firebase.py](../../learn_fastapi_auth/auth/firebase.py) - Firebase token verification
- [learn_fastapi_auth/routers/auth_routes.py](../../learn_fastapi_auth/routers/auth_routes.py) - Login endpoint
- [learn_fastapi_auth/one/one_04_webapp.py](../../learn_fastapi_auth/one/one_04_webapp.py) - Firebase Admin SDK initialization
