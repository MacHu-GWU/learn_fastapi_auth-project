/**
 * Authentication utilities for FastAPI Auth project.
 * Handles token storage and auth state management.
 */

const AUTH_TOKEN_KEY = 'auth_token';
const USER_EMAIL_KEY = 'user_email';

// =============================================================================
// Token Management
// =============================================================================

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  window.dispatchEvent(new Event('auth-change'));
}

export function removeToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(USER_EMAIL_KEY);
}

export function getUserEmail(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(USER_EMAIL_KEY);
}

export function setUserEmail(email: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_EMAIL_KEY, email);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

// =============================================================================
// Form Validation Helpers
// =============================================================================

export function validateEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

export function validatePassword(password: string): boolean {
  // At least 8 characters, contains letter and number
  return password.length >= 8 && /[a-zA-Z]/.test(password) && /[0-9]/.test(password);
}
