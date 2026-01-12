/**
 * Centralized API endpoint constants.
 * All API routes should be referenced from here to maintain consistency.
 */

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/auth/login',
    REGISTER: '/api/auth/register',
    LOGOUT: '/api/auth/logout',
    REFRESH: '/api/auth/refresh',
    VERIFY: '/api/auth/verify',
    FIREBASE: '/api/auth/firebase',
    FORGOT_PASSWORD: '/api/auth/forgot-password',
    RESET_PASSWORD: '/api/auth/reset-password',
    CHANGE_PASSWORD: '/api/auth/change-password',
  },
  USER: {
    ME: '/api/users/me',
    DATA: '/api/user-data',
  },
} as const;

// Type helper for API endpoints
export type ApiEndpoint = typeof API_ENDPOINTS;
