/**
 * Type definitions for the FastAPI Auth frontend.
 */

// =============================================================================
// User Types
// =============================================================================

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  created_at: string | null;
  updated_at: string | null;
  is_oauth_user: boolean;
}

export interface UserData {
  text_value: string;
}

// =============================================================================
// Auth Types
// =============================================================================

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface FirebaseLoginResponse {
  access_token: string;
  token_type: string;
  is_new_user: boolean;
}

export interface TokenRefreshResponse {
  access_token: string;
}

export interface MessageResponse {
  message: string;
}

// =============================================================================
// Form Types
// =============================================================================

export interface SignInFormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

export interface SignUpFormData {
  email: string;
  password: string;
  confirmPassword: string;
}

export interface ForgotPasswordFormData {
  email: string;
}

export interface ResetPasswordFormData {
  password: string;
  confirmPassword: string;
}

export interface ChangePasswordFormData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

// =============================================================================
// Toast Types
// =============================================================================

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}
