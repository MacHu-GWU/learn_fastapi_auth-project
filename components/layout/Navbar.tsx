'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { isLoggedIn, getUserEmail, removeToken } from '@/lib/auth';
import { useToast } from '@/hooks/useToast';
import { useRouter } from 'next/navigation';

export function Navbar() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const { showToast } = useToast();
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    setLoggedIn(isLoggedIn());
    setEmail(getUserEmail());

    const handleAuthChange = () => {
      setLoggedIn(isLoggedIn());
      setEmail(getUserEmail());
    };

    window.addEventListener('auth-change', handleAuthChange);
    return () => window.removeEventListener('auth-change', handleAuthChange);
  }, []);

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (token) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          credentials: 'include',
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    }

    removeToken();
    setLoggedIn(false);
    setEmail(null);
    showToast('Successfully logged out', 'success');
    setTimeout(() => {
      router.push('/');
    }, 1000);
  };

  // Don't render auth-dependent content until mounted (avoid hydration mismatch)
  if (!mounted) {
    return (
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-blue-600">
            FastAPI Auth
          </Link>
          <div className="flex items-center gap-4">
            {/* Placeholder for SSR */}
          </div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold text-blue-600">
          FastAPI Auth
        </Link>

        <div className="flex items-center gap-4">
          {loggedIn ? (
            <>
              {email && (
                <span className="text-gray-600 text-sm hidden sm:inline">
                  {email}
                </span>
              )}
              <Link
                href="/dashboard"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                App
              </Link>
              <button
                onClick={handleLogout}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                href="/signin"
                className="text-gray-600 hover:text-gray-900 transition-colors text-sm font-medium"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                Create Account
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
