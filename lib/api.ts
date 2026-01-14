/**
 * API request utilities for FastAPI Auth project.
 */

import { getToken, removeToken } from './auth';
import { API_ENDPOINTS, ROUTES } from '@/constants';

/**
 * Make an authenticated API request.
 * Automatically adds Authorization header and handles 401 errors.
 */
export async function apiRequest(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (response.status === 401) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      const newToken = getToken();
      if (newToken) {
        (headers as Record<string, string>)['Authorization'] = `Bearer ${newToken}`;
      }
      return fetch(url, {
        ...options,
        headers,
        credentials: 'include',
      });
    }

    removeToken();
    if (typeof window !== 'undefined') {
      window.location.href = `${ROUTES.SIGNIN}?error=session_expired`;
    }
  }

  return response;
}

/**
 * Try to refresh the access token using the refresh token cookie.
 */
async function tryRefreshToken(): Promise<boolean> {
  try {
    const response = await fetch(API_ENDPOINTS.AUTH.REFRESH, {
      method: 'POST',
      credentials: 'include',
    });

    if (response.ok) {
      const data = await response.json();
      if (data.access_token) {
        const { setToken } = await import('./auth');
        setToken(data.access_token);
        return true;
      }
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }
  return false;
}
