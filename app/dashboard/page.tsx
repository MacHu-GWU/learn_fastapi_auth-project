'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Input, Modal } from '@/components/ui';
import { useToast } from '@/hooks/useToast';
import { isLoggedIn, validatePassword } from '@/lib/auth';
import { apiRequest } from '@/lib/api';
import { getErrorMessage, getFieldError } from '@/lib/errors';
import type { User, UserData } from '@/types';

export default function DashboardPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [userData, setUserData] = useState('');
  const [userInfo, setUserInfo] = useState<User | null>(null);

  // Edit modal state
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editText, setEditText] = useState('');
  const [saving, setSaving] = useState(false);

  // Password modal state
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordErrors, setPasswordErrors] = useState<{
    currentPassword?: string;
    newPassword?: string;
    confirmPassword?: string;
  }>({});
  const [changingPassword, setChangingPassword] = useState(false);

  // Check auth and load data
  useEffect(() => {
    if (!isLoggedIn()) {
      router.push('/signin?error=login_required');
      return;
    }

    Promise.all([loadUserInfo(), loadUserData()]).then(() => {
      setLoading(false);
    });
  }, [router]);

  const loadUserInfo = async () => {
    try {
      const response = await apiRequest('/api/users/me');
      if (response.ok) {
        const data: User = await response.json();
        setUserInfo(data);
      }
    } catch (error) {
      console.error('Error loading user info:', error);
    }
  };

  const loadUserData = async () => {
    try {
      const response = await apiRequest('/api/user-data');
      if (response.ok) {
        const data: UserData = await response.json();
        setUserData(data.text_value || '');
      } else {
        const error = await response.json();
        showToast(getErrorMessage(error.detail, 'Failed to load data.'), 'error');
      }
    } catch (error) {
      console.error('Error loading user data:', error);
      showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    }
  };

  // Edit modal handlers
  const openEditModal = () => {
    setEditText(userData);
    setEditModalOpen(true);
  };

  const saveUserData = async () => {
    setSaving(true);
    try {
      const response = await apiRequest('/api/user-data', {
        method: 'PUT',
        body: JSON.stringify({ text_value: editText }),
      });

      if (response.ok) {
        const data: UserData = await response.json();
        setUserData(data.text_value || '');
        setEditModalOpen(false);
        showToast('Data saved successfully!', 'success');
      } else {
        const error = await response.json();
        showToast(getErrorMessage(error.detail, 'Failed to save data.'), 'error');
      }
    } catch (error) {
      console.error('Error saving user data:', error);
      showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    } finally {
      setSaving(false);
    }
  };

  // Password modal handlers
  const openPasswordModal = () => {
    if (userInfo?.is_oauth_user) {
      showToast(getErrorMessage('OAUTH_USER_NO_PASSWORD'), 'info');
      return;
    }
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setPasswordErrors({});
    setPasswordModalOpen(true);
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordErrors({});

    // Validate
    const errors: typeof passwordErrors = {};

    if (!currentPassword) {
      errors.currentPassword = 'Please enter your current password';
    }

    if (!validatePassword(newPassword)) {
      errors.newPassword = 'Password must be at least 8 characters with letters and numbers';
    }

    if (newPassword !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (Object.keys(errors).length > 0) {
      setPasswordErrors(errors);
      return;
    }

    setChangingPassword(true);

    try {
      const response = await apiRequest('/api/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (response.ok) {
        setPasswordModalOpen(false);
        showToast('Password changed successfully!', 'success');
      } else {
        const error = await response.json();
        const errorCode = error.detail;
        const fieldError = getFieldError(errorCode);

        if (fieldError) {
          setPasswordErrors({ [fieldError.field]: fieldError.message });
        } else {
          showToast(getErrorMessage(errorCode, 'Failed to change password.'), 'error');
        }
      }
    } catch (error) {
      console.error('Error changing password:', error);
      showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    } finally {
      setChangingPassword(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Your Personal Data</h1>
        <p className="text-gray-600">This is your private space. Only you can see and edit this content.</p>
      </div>

      {/* User Data Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Text Data</h2>
        <div className={`p-4 rounded-lg mb-4 min-h-[100px] ${userData ? 'bg-gray-50 text-gray-800' : 'bg-gray-100 text-gray-500 italic'}`}>
          {userData || 'No data yet. Click "Edit" to add some content.'}
        </div>
        <Button onClick={openEditModal}>Edit</Button>
      </div>

      {/* Account Settings Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Account Settings</h2>
        <p className="text-gray-600 mb-4">Manage your account security settings.</p>
        <Button variant="secondary" onClick={openPasswordModal}>
          Change Password
        </Button>
      </div>

      {/* Edit Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title="Edit Your Data"
      >
        <textarea
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          placeholder="Enter your text here..."
          className="w-full h-40 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
        />
        <div className="flex justify-end gap-3 mt-4">
          <Button variant="outline" onClick={() => setEditModalOpen(false)}>
            Cancel
          </Button>
          <Button onClick={saveUserData} loading={saving} loadingText="Saving...">
            Save
          </Button>
        </div>
      </Modal>

      {/* Change Password Modal */}
      <Modal
        isOpen={passwordModalOpen}
        onClose={() => setPasswordModalOpen(false)}
        title="Change Password"
      >
        <form onSubmit={handleChangePassword}>
          <Input
            label="Current Password"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="Enter current password"
            error={passwordErrors.currentPassword}
            required
          />
          <Input
            label="New Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Enter new password"
            error={passwordErrors.newPassword}
            required
          />
          <Input
            label="Confirm New Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
            error={passwordErrors.confirmPassword}
            required
          />
          <div className="flex justify-end gap-3 mt-4">
            <Button type="button" variant="outline" onClick={() => setPasswordModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={changingPassword} loadingText="Changing...">
              Change Password
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
