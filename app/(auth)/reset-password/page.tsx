'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button, Input } from '@/components/ui';
import { useToast } from '@/hooks/useToast';
import { validatePassword } from '@/lib/auth';
import { getErrorMessage, API_ENDPOINTS, ROUTES, REDIRECT_DELAY } from '@/constants';

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showToast } = useToast();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ password?: string; confirmPassword?: string }>({});
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const tokenParam = searchParams.get('token');
    if (!tokenParam) {
      showToast('Invalid or missing reset token. Please request a new password reset.', 'error');
      setTimeout(() => {
        router.push(ROUTES.FORGOT_PASSWORD);
      }, REDIRECT_DELAY.LONG);
    } else {
      setToken(tokenParam);
    }
  }, [searchParams, router, showToast]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!token) return;

    // Validate
    const newErrors: typeof errors = {};

    if (!validatePassword(password)) {
      newErrors.password = 'Password must be at least 8 characters with letters and numbers';
    }

    if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(API_ENDPOINTS.AUTH.RESET_PASSWORD, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password }),
      });

      if (response.ok) {
        showToast('Password reset successfully! Redirecting to sign in...', 'success');
        setTimeout(() => {
          router.push(`${ROUTES.SIGNIN}?reset=success`);
        }, REDIRECT_DELAY.LONG);
      } else {
        const data = await response.json();
        const errorCode = data.detail;
        const message = getErrorMessage(errorCode, 'Password reset failed. Please try again.');
        showToast(message, 'error');
      }
    } catch (error) {
      console.error('Reset password error:', error);
      showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-gray-600">Redirecting...</div>
      </div>
    );
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-900 mb-4">Reset Password</h1>
        <p className="text-center text-gray-600 mb-8">
          Enter your new password below.
        </p>

        <form onSubmit={handleSubmit}>
          <Input
            label="New Password"
            type="password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter new password"
            error={errors.password}
            required
          />

          <Input
            label="Confirm New Password"
            type="password"
            name="confirmPassword"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
            error={errors.confirmPassword}
            required
          />

          <Button
            type="submit"
            fullWidth
            loading={loading}
            loadingText="Resetting..."
          >
            Reset Password
          </Button>
        </form>

        <p className="text-center mt-6 text-gray-600">
          <Link href={ROUTES.SIGNIN} className="text-blue-600 hover:underline">
            Back to Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-[60vh] flex items-center justify-center">Loading...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
