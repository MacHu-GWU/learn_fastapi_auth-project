/**
 * Centralized error message handling for FastAPI Auth project.
 * Converts API error codes to user-friendly messages.
 */

// =============================================================================
// Error Message Mapping
// =============================================================================

/**
 * Map of API error codes to user-friendly error messages.
 * Keys are the error codes returned by the backend API (detail field).
 * Values are the translated, user-friendly messages.
 */
const ERROR_MESSAGES = {
    // Authentication errors
    'LOGIN_BAD_CREDENTIALS': 'Invalid email or password. Please check and try again.',
    'LOGIN_USER_NOT_VERIFIED': 'Please verify your email before signing in. Check your inbox for the verification link.',

    // Registration errors
    'REGISTER_USER_ALREADY_EXISTS': 'An account with this email already exists. Please sign in or use a different email.',
    'REGISTER_INVALID_PASSWORD': 'Password does not meet requirements. Please use at least 8 characters with letters and numbers.',

    // Verification errors
    'VERIFY_USER_BAD_TOKEN': 'Verification link is invalid or has expired. Please request a new verification email.',
    'VERIFY_USER_ALREADY_VERIFIED': 'Your email is already verified. You can sign in now.',

    // Password reset errors
    'RESET_PASSWORD_BAD_TOKEN': 'Password reset link is invalid or has expired. Please request a new reset link.',
    'RESET_PASSWORD_INVALID_PASSWORD': 'New password does not meet requirements. Please use at least 8 characters with letters and numbers.',

    // Change password errors
    'CHANGE_PASSWORD_INVALID_CURRENT': 'Current password is incorrect. Please try again.',

    // User management errors
    'UPDATE_USER_EMAIL_ALREADY_EXISTS': 'This email is already in use by another account.',
    'UPDATE_USER_INVALID_PASSWORD': 'Invalid password provided.',

    // Token errors
    'TOKEN_EXPIRED': 'Your session has expired. Please sign in again.',
    'TOKEN_INVALID': 'Invalid session. Please sign in again.',

    // Network and server errors
    'NETWORK_ERROR': 'Network connection failed. Please check your internet and try again.',
    'SERVER_ERROR': 'Server encountered an error. Please try again later.',
    'TIMEOUT_ERROR': 'Request timed out. Please try again.',

    // Rate limiting
    'RATE_LIMIT_EXCEEDED': 'Too many attempts. Please wait a moment before trying again.',

    // CSRF errors
    'CSRF_TOKEN_MISSING': 'Security validation failed. Please refresh the page and try again.',
    'CSRF_TOKEN_INVALID': 'Security validation failed. Please refresh the page and try again.',

    // Generic fallback
    'UNKNOWN_ERROR': 'An unexpected error occurred. Please try again.'
};

// =============================================================================
// HTTP Status Code Messages
// =============================================================================

/**
 * Map of HTTP status codes to user-friendly messages.
 * Used as fallback when specific error code is not available.
 */
const HTTP_STATUS_MESSAGES = {
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
    504: 'Request timed out. Please try again.'
};

// =============================================================================
// Error Message Functions
// =============================================================================

/**
 * Get a user-friendly error message from an API error code.
 *
 * @param {string} errorCode - The error code from the API response (e.g., 'LOGIN_BAD_CREDENTIALS')
 * @param {string} fallback - Optional fallback message if error code is not found
 * @returns {string} User-friendly error message
 *
 * @example
 * const message = getErrorMessage('LOGIN_BAD_CREDENTIALS');
 * // Returns: 'Invalid email or password. Please check and try again.'
 *
 * @example
 * const message = getErrorMessage('UNKNOWN_CODE', 'Something went wrong');
 * // Returns: 'Something went wrong'
 */
function getErrorMessage(errorCode, fallback = null) {
    if (!errorCode) {
        return fallback || ERROR_MESSAGES['UNKNOWN_ERROR'];
    }

    // Check if we have a specific message for this error code
    if (ERROR_MESSAGES[errorCode]) {
        return ERROR_MESSAGES[errorCode];
    }

    // If not found, return fallback or generic message
    return fallback || ERROR_MESSAGES['UNKNOWN_ERROR'];
}

/**
 * Get a user-friendly message for an HTTP status code.
 *
 * @param {number} statusCode - The HTTP status code
 * @param {string} fallback - Optional fallback message
 * @returns {string} User-friendly error message
 *
 * @example
 * const message = getHttpErrorMessage(401);
 * // Returns: 'Authentication required. Please sign in.'
 */
function getHttpErrorMessage(statusCode, fallback = null) {
    if (HTTP_STATUS_MESSAGES[statusCode]) {
        return HTTP_STATUS_MESSAGES[statusCode];
    }

    // Generic fallback based on status code range
    if (statusCode >= 400 && statusCode < 500) {
        return fallback || 'Request error. Please check your input and try again.';
    }
    if (statusCode >= 500) {
        return fallback || 'Server error. Please try again later.';
    }

    return fallback || ERROR_MESSAGES['UNKNOWN_ERROR'];
}

/**
 * Extract and format error message from an API response.
 * Handles various API response formats:
 * - { detail: "ERROR_CODE" }
 * - { detail: "Some message" }
 * - { detail: { message: "..." } }
 * - { message: "..." }
 * - Plain error object from fetch
 *
 * @param {Response|Object|Error} responseOrError - The API response or error object
 * @param {number} statusCode - Optional HTTP status code
 * @returns {Promise<string>} User-friendly error message
 *
 * @example
 * try {
 *     const response = await fetch('/api/auth/login', {...});
 *     if (!response.ok) {
 *         const message = await getApiErrorMessage(response);
 *         showToast(message, 'error');
 *     }
 * } catch (error) {
 *     const message = await getApiErrorMessage(error);
 *     showToast(message, 'error');
 * }
 */
async function getApiErrorMessage(responseOrError, statusCode = null) {
    // Handle fetch network errors
    if (responseOrError instanceof TypeError) {
        // Network error (no internet, DNS failure, etc.)
        return ERROR_MESSAGES['NETWORK_ERROR'];
    }

    // Handle generic Error objects
    if (responseOrError instanceof Error) {
        if (responseOrError.name === 'AbortError') {
            return ERROR_MESSAGES['TIMEOUT_ERROR'];
        }
        return ERROR_MESSAGES['NETWORK_ERROR'];
    }

    // Handle Response objects
    if (responseOrError instanceof Response) {
        statusCode = responseOrError.status;
        try {
            const data = await responseOrError.json();
            return extractErrorFromData(data, statusCode);
        } catch (e) {
            // Response body is not JSON
            return getHttpErrorMessage(statusCode);
        }
    }

    // Handle pre-parsed JSON data
    if (typeof responseOrError === 'object' && responseOrError !== null) {
        return extractErrorFromData(responseOrError, statusCode);
    }

    // Handle string error codes directly
    if (typeof responseOrError === 'string') {
        return getErrorMessage(responseOrError);
    }

    return ERROR_MESSAGES['UNKNOWN_ERROR'];
}

/**
 * Extract error message from parsed API response data.
 * Internal helper function.
 *
 * @param {Object} data - Parsed JSON response data
 * @param {number} statusCode - HTTP status code
 * @returns {string} User-friendly error message
 */
function extractErrorFromData(data, statusCode) {
    // Handle { detail: "ERROR_CODE" } format (fastapi-users style)
    if (data.detail) {
        if (typeof data.detail === 'string') {
            // Check if it's a known error code
            const message = getErrorMessage(data.detail, null);
            if (message !== ERROR_MESSAGES['UNKNOWN_ERROR']) {
                return message;
            }
            // If not a known code, it might be a custom message from backend
            // Only use it if it looks like a user-friendly message (contains spaces)
            if (data.detail.includes(' ')) {
                return data.detail;
            }
            // Otherwise fall back to HTTP status message
            return statusCode ? getHttpErrorMessage(statusCode) : ERROR_MESSAGES['UNKNOWN_ERROR'];
        }
        // Handle { detail: { message: "..." } } format
        if (typeof data.detail === 'object' && data.detail.message) {
            return data.detail.message;
        }
    }

    // Handle { message: "..." } format
    if (data.message) {
        return data.message;
    }

    // Handle { error: "..." } format
    if (data.error) {
        return typeof data.error === 'string' ? data.error : ERROR_MESSAGES['UNKNOWN_ERROR'];
    }

    // Fall back to HTTP status message
    if (statusCode) {
        return getHttpErrorMessage(statusCode);
    }

    return ERROR_MESSAGES['UNKNOWN_ERROR'];
}

/**
 * Check if an error code represents a field-specific error.
 * These errors should be shown inline next to the relevant field.
 *
 * @param {string} errorCode - The error code to check
 * @returns {Object|null} Object with field name and message, or null if not field-specific
 *
 * @example
 * const fieldError = getFieldError('REGISTER_USER_ALREADY_EXISTS');
 * // Returns: { field: 'email', message: 'An account with this email...' }
 *
 * const fieldError = getFieldError('NETWORK_ERROR');
 * // Returns: null (not field-specific)
 */
function getFieldError(errorCode) {
    const fieldErrorMap = {
        'REGISTER_USER_ALREADY_EXISTS': {
            field: 'email',
            message: ERROR_MESSAGES['REGISTER_USER_ALREADY_EXISTS']
        },
        'REGISTER_INVALID_PASSWORD': {
            field: 'password',
            message: ERROR_MESSAGES['REGISTER_INVALID_PASSWORD']
        },
        'CHANGE_PASSWORD_INVALID_CURRENT': {
            field: 'current-password',
            message: ERROR_MESSAGES['CHANGE_PASSWORD_INVALID_CURRENT']
        },
        'UPDATE_USER_EMAIL_ALREADY_EXISTS': {
            field: 'email',
            message: ERROR_MESSAGES['UPDATE_USER_EMAIL_ALREADY_EXISTS']
        }
    };

    return fieldErrorMap[errorCode] || null;
}
