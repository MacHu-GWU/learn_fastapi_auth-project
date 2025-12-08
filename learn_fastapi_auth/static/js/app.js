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
    try {
        const response = await apiRequest('/api/user-data');

        if (!response) return; // Redirected due to auth error

        if (response.ok) {
            const data = await response.json();
            currentUserData = data.text_value || '';
            displayUserData(currentUserData);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to load data', 'error');
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        showToast('Failed to load data. Please try again.', 'error');
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

    // ESC key to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeEditModal();
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

    // Disable button and show loading
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner"></span> Saving...';

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
            showToast(error.detail || 'Failed to save data', 'error');
        }
    } catch (error) {
        console.error('Error saving user data:', error);
        showToast('Failed to save data. Please try again.', 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save';
    }
}
