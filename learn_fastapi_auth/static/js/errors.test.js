/**
 * Unit tests for errors.js
 *
 * This file contains tests for the error message utility functions.
 * It can be run in the browser console or with a JavaScript test runner.
 *
 * To run in browser console:
 * 1. Open any page of the application in browser
 * 2. Open Developer Tools (F12)
 * 3. Copy and paste the runAllTests() function call
 *
 * Usage:
 *   runAllTests();  // Run all tests and show results
 */

// =============================================================================
// Test Utilities
// =============================================================================

/**
 * Simple test assertion function
 */
function assertEqual(actual, expected, testName) {
    if (actual === expected) {
        console.log(`  PASS: ${testName}`);
        return true;
    } else {
        console.error(`  FAIL: ${testName}`);
        console.error(`    Expected: "${expected}"`);
        console.error(`    Actual: "${actual}"`);
        return false;
    }
}

function assertNotEqual(actual, notExpected, testName) {
    if (actual !== notExpected) {
        console.log(`  PASS: ${testName}`);
        return true;
    } else {
        console.error(`  FAIL: ${testName}`);
        console.error(`    Should not be: "${notExpected}"`);
        console.error(`    Actual: "${actual}"`);
        return false;
    }
}

function assertNull(actual, testName) {
    if (actual === null) {
        console.log(`  PASS: ${testName}`);
        return true;
    } else {
        console.error(`  FAIL: ${testName}`);
        console.error(`    Expected: null`);
        console.error(`    Actual: "${actual}"`);
        return false;
    }
}

function assertNotNull(actual, testName) {
    if (actual !== null) {
        console.log(`  PASS: ${testName}`);
        return true;
    } else {
        console.error(`  FAIL: ${testName}`);
        console.error(`    Expected: not null`);
        console.error(`    Actual: null`);
        return false;
    }
}

// =============================================================================
// Tests for getErrorMessage()
// =============================================================================

function testGetErrorMessage() {
    console.log('\n--- Testing getErrorMessage() ---');
    let passed = 0;
    let failed = 0;

    // Test known error codes
    if (assertEqual(
        getErrorMessage('LOGIN_BAD_CREDENTIALS'),
        'Invalid email or password. Please check and try again.',
        'LOGIN_BAD_CREDENTIALS returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getErrorMessage('LOGIN_USER_NOT_VERIFIED'),
        'Please verify your email before signing in. Check your inbox for the verification link.',
        'LOGIN_USER_NOT_VERIFIED returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getErrorMessage('REGISTER_USER_ALREADY_EXISTS'),
        'An account with this email already exists. Please sign in or use a different email.',
        'REGISTER_USER_ALREADY_EXISTS returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getErrorMessage('VERIFY_USER_BAD_TOKEN'),
        'Verification link is invalid or has expired. Please request a new verification email.',
        'VERIFY_USER_BAD_TOKEN returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getErrorMessage('RESET_PASSWORD_BAD_TOKEN'),
        'Password reset link is invalid or has expired. Please request a new reset link.',
        'RESET_PASSWORD_BAD_TOKEN returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getErrorMessage('CHANGE_PASSWORD_INVALID_CURRENT'),
        'Current password is incorrect. Please try again.',
        'CHANGE_PASSWORD_INVALID_CURRENT returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getErrorMessage('NETWORK_ERROR'),
        'Network connection failed. Please check your internet and try again.',
        'NETWORK_ERROR returns correct message'
    )) passed++; else failed++;

    // Test unknown error code with fallback
    if (assertEqual(
        getErrorMessage('UNKNOWN_CODE_XYZ', 'Custom fallback message'),
        'Custom fallback message',
        'Unknown code with fallback returns fallback'
    )) passed++; else failed++;

    // Test unknown error code without fallback
    if (assertEqual(
        getErrorMessage('UNKNOWN_CODE_XYZ'),
        'An unexpected error occurred. Please try again.',
        'Unknown code without fallback returns generic message'
    )) passed++; else failed++;

    // Test null input
    if (assertEqual(
        getErrorMessage(null),
        'An unexpected error occurred. Please try again.',
        'Null input returns generic message'
    )) passed++; else failed++;

    // Test empty string input
    if (assertEqual(
        getErrorMessage(''),
        'An unexpected error occurred. Please try again.',
        'Empty string returns generic message'
    )) passed++; else failed++;

    // Test undefined input
    if (assertEqual(
        getErrorMessage(undefined),
        'An unexpected error occurred. Please try again.',
        'Undefined input returns generic message'
    )) passed++; else failed++;

    console.log(`\ngetErrorMessage: ${passed} passed, ${failed} failed`);
    return { passed, failed };
}

// =============================================================================
// Tests for getHttpErrorMessage()
// =============================================================================

function testGetHttpErrorMessage() {
    console.log('\n--- Testing getHttpErrorMessage() ---');
    let passed = 0;
    let failed = 0;

    // Test common HTTP status codes
    if (assertEqual(
        getHttpErrorMessage(400),
        'Invalid request. Please check your input and try again.',
        '400 returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getHttpErrorMessage(401),
        'Authentication required. Please sign in.',
        '401 returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getHttpErrorMessage(403),
        'Access denied. You do not have permission to perform this action.',
        '403 returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getHttpErrorMessage(404),
        'The requested resource was not found.',
        '404 returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getHttpErrorMessage(429),
        'Too many requests. Please wait a moment before trying again.',
        '429 returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getHttpErrorMessage(500),
        'Server error. Please try again later.',
        '500 returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getHttpErrorMessage(502),
        'Server is temporarily unavailable. Please try again later.',
        '502 returns correct message'
    )) passed++; else failed++;

    if (assertEqual(
        getHttpErrorMessage(503),
        'Service is temporarily unavailable. Please try again later.',
        '503 returns correct message'
    )) passed++; else failed++;

    // Test unknown 4xx status
    if (assertEqual(
        getHttpErrorMessage(418),
        'Request error. Please check your input and try again.',
        '418 (unknown 4xx) returns generic client error message'
    )) passed++; else failed++;

    // Test unknown 5xx status
    if (assertEqual(
        getHttpErrorMessage(599),
        'Server error. Please try again later.',
        '599 (unknown 5xx) returns generic server error message'
    )) passed++; else failed++;

    // Test with fallback
    if (assertEqual(
        getHttpErrorMessage(418, 'Custom fallback'),
        'Custom fallback',
        'Unknown status with fallback returns fallback'
    )) passed++; else failed++;

    console.log(`\ngetHttpErrorMessage: ${passed} passed, ${failed} failed`);
    return { passed, failed };
}

// =============================================================================
// Tests for getFieldError()
// =============================================================================

function testGetFieldError() {
    console.log('\n--- Testing getFieldError() ---');
    let passed = 0;
    let failed = 0;

    // Test field-specific errors
    const registerError = getFieldError('REGISTER_USER_ALREADY_EXISTS');
    if (assertNotNull(registerError, 'REGISTER_USER_ALREADY_EXISTS returns object')) {
        passed++;
        if (assertEqual(
            registerError.field,
            'email',
            'REGISTER_USER_ALREADY_EXISTS has correct field'
        )) passed++; else failed++;
        if (assertNotNull(registerError.message, 'REGISTER_USER_ALREADY_EXISTS has message')) {
            passed++;
        } else {
            failed++;
        }
    } else {
        failed += 3;
    }

    const passwordError = getFieldError('CHANGE_PASSWORD_INVALID_CURRENT');
    if (assertNotNull(passwordError, 'CHANGE_PASSWORD_INVALID_CURRENT returns object')) {
        passed++;
        if (assertEqual(
            passwordError.field,
            'current-password',
            'CHANGE_PASSWORD_INVALID_CURRENT has correct field'
        )) passed++; else failed++;
    } else {
        failed += 2;
    }

    // Test non-field errors
    if (assertNull(
        getFieldError('LOGIN_BAD_CREDENTIALS'),
        'LOGIN_BAD_CREDENTIALS returns null (not field-specific)'
    )) passed++; else failed++;

    if (assertNull(
        getFieldError('NETWORK_ERROR'),
        'NETWORK_ERROR returns null (not field-specific)'
    )) passed++; else failed++;

    if (assertNull(
        getFieldError('UNKNOWN_ERROR'),
        'UNKNOWN_ERROR returns null'
    )) passed++; else failed++;

    if (assertNull(
        getFieldError(null),
        'Null input returns null'
    )) passed++; else failed++;

    console.log(`\ngetFieldError: ${passed} passed, ${failed} failed`);
    return { passed, failed };
}

// =============================================================================
// Tests for extractErrorFromData() (internal function)
// =============================================================================

function testExtractErrorFromData() {
    console.log('\n--- Testing extractErrorFromData() ---');
    let passed = 0;
    let failed = 0;

    // Test { detail: "ERROR_CODE" } format
    if (assertEqual(
        extractErrorFromData({ detail: 'LOGIN_BAD_CREDENTIALS' }, 401),
        'Invalid email or password. Please check and try again.',
        'detail with known error code returns mapped message'
    )) passed++; else failed++;

    // Test { detail: "unknown code" } with status code fallback
    if (assertEqual(
        extractErrorFromData({ detail: 'UNKNOWN_CODE' }, 401),
        'Authentication required. Please sign in.',
        'detail with unknown code falls back to HTTP status message'
    )) passed++; else failed++;

    // Test { detail: "human readable message" }
    if (assertEqual(
        extractErrorFromData({ detail: 'This is a human readable message' }, null),
        'This is a human readable message',
        'detail with spaces is treated as human readable'
    )) passed++; else failed++;

    // Test { message: "..." } format
    if (assertEqual(
        extractErrorFromData({ message: 'Custom message' }, null),
        'Custom message',
        'message field is used when present'
    )) passed++; else failed++;

    // Test { error: "..." } format
    if (assertEqual(
        extractErrorFromData({ error: 'Error text' }, null),
        'Error text',
        'error field is used when present'
    )) passed++; else failed++;

    // Test empty object with status code
    if (assertEqual(
        extractErrorFromData({}, 500),
        'Server error. Please try again later.',
        'Empty object falls back to HTTP status message'
    )) passed++; else failed++;

    console.log(`\nextractErrorFromData: ${passed} passed, ${failed} failed`);
    return { passed, failed };
}

// =============================================================================
// Run All Tests
// =============================================================================

function runAllTests() {
    console.log('=================================================');
    console.log('Running Error Message Module Tests');
    console.log('=================================================');

    const results = [];

    results.push(testGetErrorMessage());
    results.push(testGetHttpErrorMessage());
    results.push(testGetFieldError());
    results.push(testExtractErrorFromData());

    // Summary
    const totalPassed = results.reduce((sum, r) => sum + r.passed, 0);
    const totalFailed = results.reduce((sum, r) => sum + r.failed, 0);

    console.log('\n=================================================');
    console.log('Test Summary');
    console.log('=================================================');
    console.log(`Total: ${totalPassed + totalFailed} tests`);
    console.log(`Passed: ${totalPassed}`);
    console.log(`Failed: ${totalFailed}`);

    if (totalFailed === 0) {
        console.log('\nAll tests passed!');
    } else {
        console.error(`\n${totalFailed} test(s) failed.`);
    }

    return { passed: totalPassed, failed: totalFailed };
}

// Auto-run tests if loaded directly (not as module)
if (typeof window !== 'undefined' && window.location.pathname.includes('test')) {
    document.addEventListener('DOMContentLoaded', () => {
        runAllTests();
    });
}
