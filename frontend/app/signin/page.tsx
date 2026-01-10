'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button, Input } from '@/components/ui';
import { useToast } from '@/hooks/useToast';
import { setToken, setUserEmail, validateEmail } from '@/lib/auth';
import { getErrorMessage } from '@/lib/errors';
import { signInWithGoogle } from '@/lib/firebase';

// Google Icon SVG
function GoogleIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  );
}

function SignInContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showToast } = useToast();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  // Handle email verification from URL params
  useEffect(() => {
    const token = searchParams.get('token');
    const verified = searchParams.get('verified');
    const error = searchParams.get('error');

    if (verified === 'pending' && token) {
      verifyEmail(token);
    } else if (verified === 'success') {
      showToast('Email verified successfully! Please sign in.', 'success');
    } else if (error === 'session_expired') {
      showToast('Your session has expired. Please sign in again.', 'error');
    } else if (error === 'login_required') {
      showToast('Please sign in to continue.', 'info');
    }
  }, [searchParams, showToast]);

  const verifyEmail = async (token: string) => {
    showToast('Verifying your email...', 'info');

    try {
      const response = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });

      if (response.ok) {
        showToast('Email verified successfully! Please sign in.', 'success');
        window.history.replaceState({}, document.title, '/signin?verified=success');
      } else {
        const data = await response.json();
        const errorCode = data.detail;
        const toastType = errorCode === 'VERIFY_USER_ALREADY_VERIFIED' ? 'info' : 'error';
        const message = getErrorMessage(errorCode, 'Verification failed. The link may have expired.');
        showToast(message, toastType as 'info' | 'error');
        window.history.replaceState({}, document.title, '/signin');
      }
    } catch (error) {
      console.error('Verification error:', error);
      showToast(getErrorMessage('NETWORK_ERROR'), 'error');
      window.history.replaceState({}, document.title, '/signin');
    }
  };

  const handleGoogleSignIn = async () => {
    setGoogleLoading(true);

    try {
      const idToken = await signInWithGoogle();

      const response = await fetch('/api/auth/firebase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: idToken }),
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok) {
        setToken(data.access_token);
        // Try to get email from the response or use a placeholder
        setUserEmail(data.email || 'Google User');

        const message = data.is_new_user
          ? 'Account created successfully!'
          : 'Login successful!';
        showToast(message, 'success');

        setTimeout(() => {
          router.push('/dashboard');
        }, 1000);
      } else {
        const errorCode = data.detail;
        const message = getErrorMessage(errorCode, 'Google sign in failed. Please try again.');
        showToast(message, 'error');
      }
    } catch (error: unknown) {
      console.error('Google sign in error:', error);

      const firebaseError = error as { code?: string; message?: string };
      if (firebaseError.code === 'auth/popup-closed-by-user') {
        showToast('Sign in cancelled.', 'info');
      } else if (firebaseError.code === 'auth/network-request-failed') {
        showToast(getErrorMessage('NETWORK_ERROR'), 'error');
      } else {
        showToast('Google sign in failed. Please try again.', 'error');
      }
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Validate
    const newErrors: { email?: string; password?: string } = {};

    if (!validateEmail(email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!password) {
      newErrors.password = 'Please enter your password';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      formData.append('remember_me', rememberMe ? 'true' : 'false');

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok) {
        setToken(data.access_token);
        setUserEmail(email);

        showToast('Login successful!', 'success');
        setTimeout(() => {
          router.push('/dashboard');
        }, 1000);
      } else {
        const errorCode = data.detail;
        const message = getErrorMessage(errorCode, 'Login failed. Please try again.');
        showToast(message, 'error');
      }
    } catch (error) {
      console.error('Login error:', error);
      showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-900 mb-8">Sign In</h1>

        {/* Google Sign In */}
        <Button
          variant="google"
          fullWidth
          onClick={handleGoogleSignIn}
          loading={googleLoading}
          loadingText="Signing in..."
          className="mb-6"
        >
          <GoogleIcon />
          Sign in with Google
        </Button>

        {/* Divider */}
        <div className="flex items-center gap-4 my-6">
          <div className="flex-1 h-px bg-gray-300" />
          <span className="text-gray-500 text-sm">or sign in with email</span>
          <div className="flex-1 h-px bg-gray-300" />
        </div>

        {/* Email/Password Form */}
        <form onSubmit={handleSubmit}>
          <Input
            label="Email"
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
            error={errors.email}
            required
          />

          <Input
            label="Password"
            type="password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Your password"
            error={errors.password}
            required
          />

          <div className="flex items-center mb-6">
            <input
              type="checkbox"
              id="remember-me"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="remember-me" className="ml-2 text-sm text-gray-600">
              Remember me for 30 days
            </label>
          </div>

          <Button
            type="submit"
            fullWidth
            loading={loading}
            loadingText="Signing In..."
          >
            Sign In
          </Button>
        </form>

        {/* Links */}
        <p className="text-center mt-6 text-gray-600">
          <Link href="/forgot-password" className="text-blue-600 hover:underline">
            Forgot your password?
          </Link>
        </p>
        <p className="text-center mt-2 text-gray-600">
          Don&apos;t have an account?{' '}
          <Link href="/signup" className="text-blue-600 hover:underline">
            Create Account
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={<div className="min-h-[60vh] flex items-center justify-center">Loading...</div>}>
      <SignInContent />
    </Suspense>
  );
}
