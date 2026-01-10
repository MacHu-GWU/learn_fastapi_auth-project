'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button, Input } from '@/components/ui';
import { useToast } from '@/hooks/useToast';
import { validateEmail } from '@/lib/auth';
import { getErrorMessage } from '@/lib/errors';

export default function ForgotPasswordPage() {
  const { showToast } = useToast();

  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      // For security, show the same message regardless of whether email exists
      showToast('If an account exists with this email, you will receive a password reset link.', 'success');
      setEmail('');
    } catch (error) {
      console.error('Forgot password error:', error);
      showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-900 mb-4">Forgot Password</h1>
        <p className="text-center text-gray-600 mb-8">
          Enter your email address and we&apos;ll send you a link to reset your password.
        </p>

        <form onSubmit={handleSubmit}>
          <Input
            label="Email"
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
            error={error}
            required
          />

          <Button
            type="submit"
            fullWidth
            loading={loading}
            loadingText="Sending..."
          >
            Send Reset Link
          </Button>
        </form>

        <p className="text-center mt-6 text-gray-600">
          Remember your password?{' '}
          <Link href="/signin" className="text-blue-600 hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
