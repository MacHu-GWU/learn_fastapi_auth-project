'use client';

import { Button } from '@/components/ui';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/constants';

interface AccountSettingsCardProps {
  isOAuthUser: boolean;
  onChangePassword: () => void;
}

export function AccountSettingsCard({ isOAuthUser, onChangePassword }: AccountSettingsCardProps) {
  const { showToast } = useToast();

  const handleChangePassword = () => {
    if (isOAuthUser) {
      showToast(getErrorMessage('OAUTH_USER_NO_PASSWORD'), 'info');
      return;
    }
    onChangePassword();
  };

  return (
    <div className="bg-surface rounded-xl border border-default p-6">
      <h2 className="text-xl font-semibold text-primary mb-2">Account Settings</h2>
      <p className="text-secondary mb-4">Manage your account security settings.</p>
      <Button variant="secondary" onClick={handleChangePassword}>
        Change Password
      </Button>
    </div>
  );
}
