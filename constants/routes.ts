/**
 * Centralized route constants for frontend navigation.
 * All internal routes should be referenced from here.
 */

export const ROUTES = {
  // Home module
  HOME: '/',

  // Auth module
  SIGNIN: '/signin',
  SIGNUP: '/signup',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',

  // User module (future expansion)
  PROFILE: '/profile',

  // SAAS app module
  DASHBOARD: '/dashboard',
} as const;

// Type helper for routes
export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];
