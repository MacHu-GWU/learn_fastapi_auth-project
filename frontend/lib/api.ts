/**
 * API request utilities for FastAPI Auth project.
 */

import { getToken, removeToken } from './auth';

// =============================================================================
// Types
// =============================================================================

export interface ApiResponse<T = unknown> {
  data: T | null;
  error: string | null;
  status: number;
}

// =============================================================================
// API Request Function
// =============================================================================

/**
 * Make an authenticated API request.
 * Automatically adds Authorization header and handles 401 errors.
 */
export async function apiRequest<T = unknown>(
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
    credentials: 'include', // Important: send cookies for refresh token
  });

  if (response.status === 401) {
    // Token expired or invalid - try to refresh
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      // Retry the request with new token
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

    // Refresh failed, redirect to signin
    removeToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/signin?error=session_expired';
    }
  }

  return response;
}

/**
 * Try to refresh the access token using the refresh token cookie.
 */
async function tryRefreshToken(): Promise<boolean> {
  try {
    const response = await fetch('/api/auth/refresh', {
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

// =============================================================================
// Convenience Functions
// =============================================================================

/**
 * GET request helper
 */
export async function apiGet<T = unknown>(url: string): Promise<ApiResponse<T>> {
  try {
    const response = await apiRequest(url);
    const status = response.status;

    if (response.ok) {
      const data = await response.json();
      return { data: data as T, error: null, status };
    } else {
      const errorData = await response.json().catch(() => ({}));
      return { data: null, error: errorData.detail || 'Request failed', status };
    }
  } catch (error) {
    return { data: null, error: 'Network error', status: 0 };
  }
}

/**
 * POST request helper
 */
export async function apiPost<T = unknown>(
  url: string,
  body?: unknown
): Promise<ApiResponse<T>> {
  try {
    const response = await apiRequest(url, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
    const status = response.status;

    if (response.ok) {
      const data = await response.json();
      return { data: data as T, error: null, status };
    } else {
      const errorData = await response.json().catch(() => ({}));
      return { data: null, error: errorData.detail || 'Request failed', status };
    }
  } catch (error) {
    return { data: null, error: 'Network error', status: 0 };
  }
}

/**
 * PUT request helper
 */
export async function apiPut<T = unknown>(
  url: string,
  body?: unknown
): Promise<ApiResponse<T>> {
  try {
    const response = await apiRequest(url, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
    const status = response.status;

    if (response.ok) {
      const data = await response.json();
      return { data: data as T, error: null, status };
    } else {
      const errorData = await response.json().catch(() => ({}));
      return { data: null, error: errorData.detail || 'Request failed', status };
    }
  } catch (error) {
    return { data: null, error: 'Network error', status: 0 };
  }
}
