/**
 * Authentication utilities for FastAPI Auth project.
 * Handles token storage and auth state management.
 */

import { STORAGE_KEYS, VALIDATION, AUTH_EVENTS } from '@/constants';

// =============================================================================
// Token Management
// =============================================================================

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
  // Bug fix: Dispatch custom event so Navbar can update immediately after login.
  // Without this, Navbar only checks auth state on mount, so after OAuth login
  // and redirect, it would still show "Sign In" until page refresh.
  window.dispatchEvent(new Event(AUTH_EVENTS.AUTH_CHANGE));
}

export function removeToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.USER_EMAIL);
}

export function getUserEmail(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(STORAGE_KEYS.USER_EMAIL);
}

export function setUserEmail(email: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEYS.USER_EMAIL, email);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

// =============================================================================
// Form Validation Helpers
// =============================================================================

export function validateEmail(email: string): boolean {
  return VALIDATION.EMAIL_REGEX.test(email);
}

export function validatePassword(password: string): boolean {
  // At least 8 characters, contains letter and number
  return (
    password.length >= VALIDATION.PASSWORD_MIN_LENGTH &&
    VALIDATION.PASSWORD_LETTER_REGEX.test(password) &&
    VALIDATION.PASSWORD_NUMBER_REGEX.test(password)
  );
}
