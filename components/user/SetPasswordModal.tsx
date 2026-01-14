'use client';

import { useState } from 'react';
import { Button, Input, Modal } from '@/components/ui';
import { useToast } from '@/hooks/useToast';
import { validatePassword } from '@/lib/auth';
import { apiRequest } from '@/lib/api';
import { getErrorMessage, API_ENDPOINTS } from '@/constants';

interface SetPasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function SetPasswordModal({ isOpen, onClose, onSuccess }: SetPasswordModalProps) {
  const { showToast } = useToast();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<{
    newPassword?: string;
    confirmPassword?: string;
  }>({});
  const [loading, setLoading] = useState(false);

  const resetForm = () => {
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
      const response = await apiRequest(API_ENDPOINTS.AUTH.SET_PASSWORD, {
        method: 'POST',
        body: JSON.stringify({
          new_password: newPassword,
        }),
      });

      if (response.ok) {
        handleClose();
        showToast('Password set successfully! You can now sign in with email and password.', 'success');
        onSuccess?.();
      } else {
        const error = await response.json();
        const errorCode = error.detail;
        showToast(getErrorMessage(errorCode, 'Failed to set password.'), 'error');
      }
    } catch (error) {
      console.error('Error setting password:', error);
      showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Set Password">
      <p className="text-sm text-gray-600 mb-4">
        Create a password to enable email/password sign in alongside Google.
      </p>
      <form onSubmit={handleSubmit}>
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
          label="Confirm Password"
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
          <Button type="submit" loading={loading} loadingText="Setting...">
            Set Password
          </Button>
        </div>
      </form>
    </Modal>
  );
}
