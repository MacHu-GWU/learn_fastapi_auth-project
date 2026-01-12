'use client';

import { useState } from 'react';
import { Button, Input, Modal } from '@/components/ui';
import { useToast } from '@/hooks/useToast';
import { validatePassword } from '@/lib/auth';
import { apiRequest } from '@/lib/api';
import { getErrorMessage, getFieldError, API_ENDPOINTS } from '@/constants';

interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ChangePasswordModal({ isOpen, onClose }: ChangePasswordModalProps) {
  const { showToast } = useToast();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<{
    currentPassword?: string;
    newPassword?: string;
    confirmPassword?: string;
  }>({});
  const [loading, setLoading] = useState(false);

  const resetForm = () => {
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setErrors({});
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Validate
    const newErrors: typeof errors = {};

    if (!currentPassword) {
      newErrors.currentPassword = 'Please enter your current password';
    }

    if (!validatePassword(newPassword)) {
      newErrors.newPassword = 'Password must be at least 8 characters with letters and numbers';
    }

    if (newPassword !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);

    try {
      const response = await apiRequest(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (response.ok) {
        handleClose();
        showToast('Password changed successfully!', 'success');
      } else {
        const error = await response.json();
        const errorCode = error.detail;
        const fieldError = getFieldError(errorCode);

        if (fieldError) {
          setErrors({ [fieldError.field]: fieldError.message });
        } else {
          showToast(getErrorMessage(errorCode, 'Failed to change password.'), 'error');
        }
      }
    } catch (error) {
      console.error('Error changing password:', error);
      showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Change Password">
      <form onSubmit={handleSubmit}>
        <Input
          label="Current Password"
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          placeholder="Enter current password"
          error={errors.currentPassword}
          required
        />
        <Input
          label="New Password"
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          placeholder="Enter new password"
          error={errors.newPassword}
          required
        />
        <Input
          label="Confirm New Password"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Confirm new password"
          error={errors.confirmPassword}
          required
        />
        <div className="flex justify-end gap-3 mt-4">
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" loading={loading} loadingText="Changing...">
            Change Password
          </Button>
        </div>
      </form>
    </Modal>
  );
}
