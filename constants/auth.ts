/**
 * Authentication-related constants.
 */

// localStorage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  USER_EMAIL: 'user_email',
} as const;

// Validation rules
export const VALIDATION = {
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PASSWORD_MIN_LENGTH: 8,
  PASSWORD_LETTER_REGEX: /[a-zA-Z]/,
  PASSWORD_NUMBER_REGEX: /[0-9]/,
} as const;

// Auth event names
export const AUTH_EVENTS = {
  AUTH_CHANGE: 'auth-change',
} as const;

// Redirect delay (ms)
export const REDIRECT_DELAY = {
  DEFAULT: 1000,
  LONG: 2000,
  REGISTRATION: 3000,
} as const;
