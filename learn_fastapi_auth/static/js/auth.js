/**
 * Authentication utilities for FastAPI Auth project.
 * Handles token storage, navigation updates, and common auth operations.
 */

const AUTH_TOKEN_KEY = 'auth_token';
const USER_EMAIL_KEY = 'user_email';

// =============================================================================
// Token Management
// =============================================================================

function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
}

function removeToken() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(USER_EMAIL_KEY);
}

function getUserEmail() {
    return localStorage.getItem(USER_EMAIL_KEY);
}

function setUserEmail(email) {
    localStorage.setItem(USER_EMAIL_KEY, email);
}

function isLoggedIn() {
    return !!getToken();
}

// =============================================================================
// Navigation Updates
// =============================================================================

function updateNavigation() {
    const signinLink = document.getElementById('signin-link');
    const signupLink = document.getElementById('signup-link');
    const userEmailSpan = document.getElementById('user-email');
    const appLink = document.getElementById('app-link');
    const logoutBtn = document.getElementById('logout-btn');

    if (isLoggedIn()) {
        // User is logged in
        if (signinLink) signinLink.style.display = 'none';
        if (signupLink) signupLink.style.display = 'none';
        if (userEmailSpan) {
            userEmailSpan.style.display = 'inline';
            userEmailSpan.textContent = getUserEmail() || 'User';
        }
        if (appLink) appLink.style.display = 'inline';
        if (logoutBtn) logoutBtn.style.display = 'inline';
    } else {
        // User is not logged in
        if (signinLink) signinLink.style.display = 'inline';
        if (signupLink) signupLink.style.display = 'inline';
        if (userEmailSpan) userEmailSpan.style.display = 'none';
        if (appLink) appLink.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'none';
    }
}

// =============================================================================
// Logout Handler
// =============================================================================

async function handleLogout() {
    const token = getToken();

    if (token) {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
        } catch (error) {
            console.error('Logout API error:', error);
        }
    }

    removeToken();
    showToast('Successfully logged out', 'success');
    setTimeout(() => {
        window.location.href = '/';
    }, 1000);
}

// =============================================================================
// Toast Notifications
// =============================================================================

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;

    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// =============================================================================
// API Helpers
// =============================================================================

async function apiRequest(url, options = {}) {
    const token = getToken();

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (response.status === 401) {
        // Token expired or invalid
        removeToken();
        window.location.href = '/signin?error=session_expired';
        return null;
    }

    return response;
}

// =============================================================================
// Loading State Helpers
// =============================================================================

/**
 * Set a button to loading state.
 * Stores original HTML in data attribute for later restoration.
 *
 * @param {HTMLButtonElement} button - The button element
 * @param {string} loadingText - Text to show while loading (default: 'Loading...')
 */
function setButtonLoading(button, loadingText = 'Loading...') {
    if (!button) return;

    // Store original HTML if not already stored (supports buttons with icons)
    if (!button.dataset.originalHtml) {
        button.dataset.originalHtml = button.innerHTML;
    }

    button.disabled = true;
    button.classList.add('loading');
    button.innerHTML = `<span class="spinner"></span> ${loadingText}`;
}

/**
 * Reset a button from loading state to its original state.
 *
 * @param {HTMLButtonElement} button - The button element
 * @param {string} html - Optional HTML to set (defaults to original HTML)
 */
function resetButton(button, html = null) {
    if (!button) return;

    button.disabled = false;
    button.classList.remove('loading');
    // Restore original HTML (including icons) or use provided HTML
    button.innerHTML = html || button.dataset.originalHtml || 'Submit';
}

/**
 * Show a full-page loading overlay.
 *
 * @param {string} message - Loading message to display
 * @returns {HTMLElement} The loading overlay element
 */
function showPageLoading(message = 'Loading...') {
    // Remove existing overlay if any
    hidePageLoading();

    const overlay = document.createElement('div');
    overlay.id = 'page-loading-overlay';
    overlay.className = 'page-loading';
    overlay.innerHTML = `
        <span class="spinner spinner-lg spinner-primary"></span>
        <span class="page-loading-text">${message}</span>
    `;
    document.body.appendChild(overlay);
    return overlay;
}

/**
 * Hide the full-page loading overlay.
 */
function hidePageLoading() {
    const overlay = document.getElementById('page-loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * Show skeleton loading placeholders in a container.
 *
 * @param {HTMLElement} container - Container element
 * @param {number} lines - Number of skeleton lines to show
 */
function showSkeleton(container, lines = 3) {
    if (!container) return;

    container.innerHTML = '';
    for (let i = 0; i < lines; i++) {
        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton skeleton-text';
        container.appendChild(skeleton);
    }
}

/**
 * Add loading class to an element to show content loading indicator.
 *
 * @param {HTMLElement} element - The element to mark as loading
 */
function setContentLoading(element) {
    if (element) {
        element.classList.add('content-loading');
    }
}

/**
 * Remove loading class from an element.
 *
 * @param {HTMLElement} element - The element to unmark
 */
function clearContentLoading(element) {
    if (element) {
        element.classList.remove('content-loading');
    }
}

// =============================================================================
// Form Validation Helpers
// =============================================================================

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    // At least 8 characters, contains letter and number
    return password.length >= 8 && /[a-zA-Z]/.test(password) && /[0-9]/.test(password);
}

function showFieldError(inputId, message) {
    const input = document.getElementById(inputId);
    const errorDiv = document.getElementById(`${inputId}-error`);

    if (input) input.classList.add('error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

function clearFieldError(inputId) {
    const input = document.getElementById(inputId);
    const errorDiv = document.getElementById(`${inputId}-error`);

    if (input) input.classList.remove('error');
    if (errorDiv) errorDiv.style.display = 'none';
}

function clearAllErrors() {
    document.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
    document.querySelectorAll('.error-message').forEach(el => el.style.display = 'none');
}

// =============================================================================
// Initialize
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Update navigation based on auth state
    updateNavigation();

    // Setup logout button handler
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Check for URL parameters (e.g., after email verification)
    const urlParams = new URLSearchParams(window.location.search);
    const verified = urlParams.get('verified');
    const error = urlParams.get('error');

    if (verified === 'success') {
        showToast('Email verified successfully! Please sign in.', 'success');
    } else if (error === 'session_expired') {
        showToast('Your session has expired. Please sign in again.', 'error');
    }
});
