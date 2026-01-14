'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { API_ENDPOINTS, ROUTES } from '@/constants';

type VerificationState = 'loading' | 'success' | 'already_verified' | 'error';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const [state, setState] = useState<VerificationState>('loading');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setState('error');
      setErrorMessage('Invalid or missing verification token.');
      return;
    }

    verifyEmail(token);
  }, [searchParams]);

  const verifyEmail = async (token: string) => {
    try {
      const response = await fetch(API_ENDPOINTS.AUTH.VERIFY, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });

      if (response.ok) {
        setState('success');
      } else {
        const data = await response.json();
        if (data.detail === 'VERIFY_USER_ALREADY_VERIFIED') {
          setState('already_verified');
        } else {
          setState('error');
          setErrorMessage('The verification link is invalid or has expired. Please request a new verification email.');
        }
      }
    } catch (error) {
      console.error('Verification error:', error);
      setState('error');
      setErrorMessage('Network error. Please try again.');
    }
  };

  if (state === 'loading') {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center px-4">
        <div className="text-secondary">Verifying your email...</div>
      </div>
    );
  }

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center px-4 text-center">
      {state === 'success' && (
        <>
          <div className="text-6xl text-accent mb-4">&#10003;</div>
          <h1 className="text-3xl font-bold text-primary mb-4">Email Verified!</h1>
          <p className="text-secondary mb-8">
            Your email has been successfully verified. You can now sign in to your account.
          </p>
          <Link
            href={ROUTES.SIGNIN}
            className="px-6 py-3 bg-brand text-white rounded-lg hover:bg-brand-hover transition-colors font-medium"
          >
            Sign In
          </Link>
        </>
      )}

      {state === 'already_verified' && (
        <>
          <div className="text-6xl text-accent mb-4">&#10003;</div>
          <h1 className="text-3xl font-bold text-primary mb-4">Already Verified</h1>
          <p className="text-secondary mb-8">
            Your email is already verified. You can sign in to your account.
          </p>
          <Link
            href={ROUTES.SIGNIN}
            className="px-6 py-3 bg-brand text-white rounded-lg hover:bg-brand-hover transition-colors font-medium"
          >
            Sign In
          </Link>
        </>
      )}

      {state === 'error' && (
        <>
          <div className="text-6xl text-red-500 mb-4">&#10007;</div>
          <h1 className="text-3xl font-bold text-primary mb-4">Verification Failed</h1>
          <p className="text-secondary mb-8">{errorMessage}</p>
          <Link
            href={ROUTES.SIGNUP}
            className="px-6 py-3 bg-brand text-white rounded-lg hover:bg-brand-hover transition-colors font-medium"
          >
            Sign Up Again
          </Link>
        </>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="min-h-[60vh] flex items-center justify-center text-secondary">Loading...</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
