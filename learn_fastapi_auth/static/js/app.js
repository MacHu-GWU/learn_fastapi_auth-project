/**
 * App page functionality for FastAPI Auth project.
 * Handles user data display and editing.
 */

// =============================================================================
// Global State
// =============================================================================

let currentUserData = '';

// =============================================================================
// Page Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    // Check if user is logged in
    if (!isLoggedIn()) {
        window.location.href = '/signin?error=login_required';
        return;
    }

    // Load user data
    await loadUserData();

    // Setup event listeners
    setupEventListeners();
});

// =============================================================================
// Data Loading
// =============================================================================

async function loadUserData() {
    const dataDisplay = document.getElementById('data-display');

    // Show skeleton loading while fetching data
    if (dataDisplay) {
        showSkeleton(dataDisplay, 4);
    }

    try {
        const response = await apiRequest('/api/user-data');

        if (!response) return; // Redirected due to auth error

        if (response.ok) {
            const data = await response.json();
            currentUserData = data.text_value || '';
            displayUserData(currentUserData);
        } else {
            const error = await response.json();
            const message = getErrorMessage(error.detail, 'Failed to load data. Please try again.');
            showToast(message, 'error');
            displayUserData(''); // Clear skeleton on error
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        showToast(getErrorMessage('NETWORK_ERROR'), 'error');
        displayUserData(''); // Clear skeleton on error
    }
}

function displayUserData(data) {
    const dataDisplay = document.getElementById('data-display');
    if (!dataDisplay) return;

    if (data) {
        dataDisplay.textContent = data;
        dataDisplay.classList.remove('empty');
    } else {
        dataDisplay.textContent = 'No data yet. Click "Edit" to add some content.';
        dataDisplay.classList.add('empty');
    }
}

// =============================================================================
// Edit Modal
// =============================================================================

function setupEventListeners() {
    const editBtn = document.getElementById('edit-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const saveBtn = document.getElementById('save-btn');
    const modalOverlay = document.getElementById('modal-overlay');

    if (editBtn) {
        editBtn.addEventListener('click', openEditModal);
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeEditModal);
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', saveUserData);
    }

    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                closeEditModal();
            }
        });
    }

    // Change password modal
    const changePasswordBtn = document.getElementById('change-password-btn');
    const passwordCancelBtn = document.getElementById('password-cancel-btn');
    const changePasswordForm = document.getElementById('change-password-form');
    const passwordModalOverlay = document.getElementById('password-modal-overlay');

    if (changePasswordBtn) {
        changePasswordBtn.addEventListener('click', openPasswordModal);
    }

    if (passwordCancelBtn) {
        passwordCancelBtn.addEventListener('click', closePasswordModal);
    }

    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', handleChangePassword);
    }

    if (passwordModalOverlay) {
        passwordModalOverlay.addEventListener('click', (e) => {
            if (e.target === passwordModalOverlay) {
                closePasswordModal();
            }
        });
    }

    // ESC key to close modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeEditModal();
            closePasswordModal();
        }
    });
}

function openEditModal() {
    const modal = document.getElementById('modal-overlay');
    const textarea = document.getElementById('edit-textarea');

    if (modal) modal.classList.add('show');
    if (textarea) {
        textarea.value = currentUserData;
        textarea.focus();
    }
}

function closeEditModal() {
    const modal = document.getElementById('modal-overlay');
    if (modal) modal.classList.remove('show');
}

// =============================================================================
// Save Data
// =============================================================================

async function saveUserData() {
    const textarea = document.getElementById('edit-textarea');
    const saveBtn = document.getElementById('save-btn');

    if (!textarea || !saveBtn) return;

    const newData = textarea.value;

    // Use the loading state utility
    setButtonLoading(saveBtn, 'Saving...');

    try {
        const response = await apiRequest('/api/user-data', {
            method: 'PUT',
            body: JSON.stringify({ text_value: newData })
        });

        if (!response) return; // Redirected due to auth error

        if (response.ok) {
            const data = await response.json();
            currentUserData = data.text_value || '';
            displayUserData(currentUserData);
            closeEditModal();
            showToast('Data saved successfully!', 'success');
        } else {
            const error = await response.json();
            const message = getErrorMessage(error.detail, 'Failed to save data. Please try again.');
            showToast(message, 'error');
        }
    } catch (error) {
        console.error('Error saving user data:', error);
        showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    } finally {
        resetButton(saveBtn);
    }
}

// =============================================================================
// Change Password Modal
// =============================================================================

function openPasswordModal() {
    const modal = document.getElementById('password-modal-overlay');
    if (modal) modal.classList.add('show');
    // Clear form
    const form = document.getElementById('change-password-form');
    if (form) form.reset();
    clearPasswordErrors();
}

function closePasswordModal() {
    const modal = document.getElementById('password-modal-overlay');
    if (modal) modal.classList.remove('show');
    clearPasswordErrors();
}

function clearPasswordErrors() {
    const errorDivs = document.querySelectorAll('#password-modal-overlay .error-message');
    errorDivs.forEach(div => div.style.display = 'none');
    const inputs = document.querySelectorAll('#password-modal-overlay input');
    inputs.forEach(input => input.classList.remove('error'));
}

function showPasswordFieldError(fieldId, message) {
    const input = document.getElementById(fieldId);
    const errorDiv = document.getElementById(`${fieldId}-error`);
    if (input) input.classList.add('error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

async function handleChangePassword(e) {
    e.preventDefault();
    clearPasswordErrors();

    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmNewPassword = document.getElementById('confirm-new-password').value;
    const saveBtn = document.getElementById('password-save-btn');

    // Validate
    let hasError = false;

    if (!currentPassword) {
        showPasswordFieldError('current-password', 'Please enter your current password');
        hasError = true;
    }

    if (!validatePassword(newPassword)) {
        showPasswordFieldError('new-password', 'Password must be at least 8 characters with letters and numbers');
        hasError = true;
    }

    if (newPassword !== confirmNewPassword) {
        showPasswordFieldError('confirm-new-password', 'Passwords do not match');
        hasError = true;
    }

    if (hasError) return;

    // Use the loading state utility
    setButtonLoading(saveBtn, 'Changing...');

    try {
        const response = await apiRequest('/api/auth/change-password', {
            method: 'POST',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        if (!response) return; // Redirected due to auth error

        if (response.ok) {
            closePasswordModal();
            showToast('Password changed successfully!', 'success');
        } else {
            const error = await response.json();
            const errorCode = error.detail;
            const fieldError = getFieldError(errorCode);

            if (fieldError) {
                // Field-specific error - show inline
                showPasswordFieldError(fieldError.field, fieldError.message);
            } else {
                // General error - show toast
                const message = getErrorMessage(errorCode, 'Failed to change password. Please try again.');
                showToast(message, 'error');
            }
        }
    } catch (error) {
        console.error('Error changing password:', error);
        showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    } finally {
        resetButton(saveBtn);
    }
}
