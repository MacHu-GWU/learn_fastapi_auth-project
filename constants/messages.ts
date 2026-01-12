/**
 * Centralized error message handling for FastAPI Auth project.
 * Converts API error codes to user-friendly messages.
 */

// =============================================================================
// Error Message Mapping
// =============================================================================

/**
 * Map of API error codes to user-friendly error messages.
 */
export const ERROR_MESSAGES: Record<string, string> = {
  // Authentication errors
  LOGIN_BAD_CREDENTIALS: 'Invalid email or password. Please check and try again.',
  LOGIN_USER_NOT_VERIFIED: 'Please verify your email before signing in. Check your inbox for the verification link.',

  // Registration errors
  REGISTER_USER_ALREADY_EXISTS: 'An account with this email already exists. Please sign in or use a different email.',
  REGISTER_INVALID_PASSWORD: 'Password does not meet requirements. Please use at least 8 characters with letters and numbers.',

  // Verification errors
  VERIFY_USER_BAD_TOKEN: 'Verification link is invalid or has expired. Please request a new verification email.',
  VERIFY_USER_ALREADY_VERIFIED: 'Your email is already verified. You can sign in now.',

  // Password reset errors
  RESET_PASSWORD_BAD_TOKEN: 'Password reset link is invalid or has expired. Please request a new reset link.',
  RESET_PASSWORD_INVALID_PASSWORD: 'New password does not meet requirements. Please use at least 8 characters with letters and numbers.',

  // Change password errors
  CHANGE_PASSWORD_INVALID_CURRENT: 'Current password is incorrect. Please try again.',

  // User management errors
  UPDATE_USER_EMAIL_ALREADY_EXISTS: 'This email is already in use by another account.',
  UPDATE_USER_INVALID_PASSWORD: 'Invalid password provided.',

  // Token errors
  TOKEN_EXPIRED: 'Your session has expired. Please sign in again.',
  TOKEN_INVALID: 'Invalid session. Please sign in again.',

  // Network and server errors
  NETWORK_ERROR: 'Network connection failed. Please check your internet and try again.',
  SERVER_ERROR: 'Server encountered an error. Please try again later.',
  TIMEOUT_ERROR: 'Request timed out. Please try again.',

  // Rate limiting
  RATE_LIMIT_EXCEEDED: 'Too many attempts. Please wait a moment before trying again.',

  // CSRF errors
  CSRF_TOKEN_MISSING: 'Security validation failed. Please refresh the page and try again.',
  CSRF_TOKEN_INVALID: 'Security validation failed. Please refresh the page and try again.',

  // Firebase/OAuth errors
  FIREBASE_AUTH_DISABLED: 'Google sign in is temporarily unavailable. Please use email and password.',
  FIREBASE_NOT_INITIALIZED: 'Google sign in is not properly configured. Please try again later.',
  FIREBASE_TOKEN_INVALID: 'Google sign in failed. Please try again.',
  FIREBASE_EMAIL_REQUIRED: 'Email is required for sign in. Please allow email access.',

  // OAuth user limitations
  OAUTH_USER_NO_PASSWORD: 'You signed in with Google, so there is no password to change. Your account security is managed by Google.',

  // Generic fallback
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.',
};

/**
 * Map of HTTP status codes to user-friendly messages.
 */
export const HTTP_STATUS_MESSAGES: Record<number, string> = {
  400: 'Invalid request. Please check your input and try again.',
  401: 'Authentication required. Please sign in.',
  403: 'Access denied. You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  409: 'This operation conflicts with existing data.',
  422: 'Invalid data provided. Please check your input.',
  429: 'Too many requests. Please wait a moment before trying again.',
  500: 'Server error. Please try again later.',
  502: 'Server is temporarily unavailable. Please try again later.',
  503: 'Service is temporarily unavailable. Please try again later.',
  504: 'Request timed out. Please try again.',
};

// =============================================================================
// Field Error Mapping
// =============================================================================

/**
 * Map of error codes to field-specific errors.
 */
export const FIELD_ERROR_MAP: Record<string, { field: string; message: string }> = {
  REGISTER_USER_ALREADY_EXISTS: {
    field: 'email',
    message: ERROR_MESSAGES.REGISTER_USER_ALREADY_EXISTS,
  },
  REGISTER_INVALID_PASSWORD: {
    field: 'password',
    message: ERROR_MESSAGES.REGISTER_INVALID_PASSWORD,
  },
  CHANGE_PASSWORD_INVALID_CURRENT: {
    field: 'currentPassword',
    message: ERROR_MESSAGES.CHANGE_PASSWORD_INVALID_CURRENT,
  },
  UPDATE_USER_EMAIL_ALREADY_EXISTS: {
    field: 'email',
    message: ERROR_MESSAGES.UPDATE_USER_EMAIL_ALREADY_EXISTS,
  },
};

// =============================================================================
// Error Message Functions
// =============================================================================

/**
 * Get a user-friendly error message from an API error code.
 */
export function getErrorMessage(errorCode: string | null | undefined, fallback: string | null = null): string {
  if (!errorCode) {
    return fallback || ERROR_MESSAGES.UNKNOWN_ERROR;
  }

  if (ERROR_MESSAGES[errorCode]) {
    return ERROR_MESSAGES[errorCode];
  }

  return fallback || ERROR_MESSAGES.UNKNOWN_ERROR;
}

/**
 * Get a user-friendly message for an HTTP status code.
 */
export function getHttpErrorMessage(statusCode: number, fallback: string | null = null): string {
  if (HTTP_STATUS_MESSAGES[statusCode]) {
    return HTTP_STATUS_MESSAGES[statusCode];
  }

  if (statusCode >= 400 && statusCode < 500) {
    return fallback || 'Request error. Please check your input and try again.';
  }
  if (statusCode >= 500) {
    return fallback || 'Server error. Please try again later.';
  }

  return fallback || ERROR_MESSAGES.UNKNOWN_ERROR;
}

/**
 * Check if an error code represents a field-specific error.
 */
export function getFieldError(errorCode: string): { field: string; message: string } | null {
  return FIELD_ERROR_MAP[errorCode] || null;
}
