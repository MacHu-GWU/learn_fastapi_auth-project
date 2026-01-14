'use client';

import Link from 'next/link';
import { useEffect, useState, useRef } from 'react';
import { isLoggedIn, getUserEmail, removeToken, getToken } from '@/lib/auth';
import { useToast } from '@/hooks/useToast';
import { useRouter } from 'next/navigation';
import { API_ENDPOINTS, ROUTES, AUTH_EVENTS, REDIRECT_DELAY, getErrorMessage } from '@/constants';
import { apiRequest } from '@/lib/api';
import { ChangePasswordModal, SetPasswordModal } from '@/components/user';
import type { User } from '@/types';

/**
 * Abbreviates an email address to a fixed-width format.
 */
function abbreviateEmail(email: string): string {
  const [localPart, domain] = email.split('@');
  if (!domain) return email;

  const abbreviatePart = (part: string): string => {
    if (part.length <= 8) return part;
    const first4 = part.slice(0, 4);
    const last4 = part.slice(-4);
    return `${first4}***${last4}`;
  };

  return `${abbreviatePart(localPart)}@${abbreviatePart(domain)}`;
}

export function Navbar() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [changePasswordModalOpen, setChangePasswordModalOpen] = useState(false);
  const [setPasswordModalOpen, setSetPasswordModalOpen] = useState(false);
  const [userInfo, setUserInfo] = useState<User | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { showToast } = useToast();
  const router = useRouter();

  const loadUserInfo = async () => {
    try {
      const response = await apiRequest(API_ENDPOINTS.USER.ME);
      if (response.ok) {
        const data: User = await response.json();
        setUserInfo(data);
      }
    } catch (error) {
      console.error('Error loading user info:', error);
    }
  };

  useEffect(() => {
    setMounted(true);
    setLoggedIn(isLoggedIn());
    setEmail(getUserEmail());

    if (isLoggedIn()) {
      loadUserInfo();
    }

    const handleAuthChange = () => {
      const nowLoggedIn = isLoggedIn();
      setLoggedIn(nowLoggedIn);
      setEmail(getUserEmail());
      if (nowLoggedIn) {
        loadUserInfo();
      } else {
        setUserInfo(null);
      }
    };

    window.addEventListener(AUTH_EVENTS.AUTH_CHANGE, handleAuthChange);
    return () => window.removeEventListener(AUTH_EVENTS.AUTH_CHANGE, handleAuthChange);
  }, []);

  const handlePasswordAction = () => {
    setDropdownOpen(false);
    if (userInfo?.is_oauth_user) {
      setSetPasswordModalOpen(true);
    } else {
      setChangePasswordModalOpen(true);
    }
  };

  const handleSetPasswordSuccess = () => {
    loadUserInfo();
  };

  const handleLogout = async () => {
    setDropdownOpen(false);
    try {
      const token = getToken();
      if (token) {
        await fetch(API_ENDPOINTS.AUTH.LOGOUT, {
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
    setUserInfo(null);
    showToast('Successfully logged out', 'success');
    setTimeout(() => {
      router.push(ROUTES.HOME);
    }, REDIRECT_DELAY.DEFAULT);
  };

  if (!mounted) {
    return (
      <nav className="bg-surface border-b border-default">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link href={ROUTES.HOME} className="text-xl font-bold text-brand">
            FastAPI Auth
          </Link>
          <div className="flex items-center gap-4" />
        </div>
      </nav>
    );
  }

  return (
    <>
      <nav className="bg-surface border-b border-default">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link href={ROUTES.HOME} className="text-xl font-bold text-brand hover:text-brand-hover transition-colors">
            FastAPI Auth
          </Link>

          <div className="flex items-center gap-4">
            {loggedIn ? (
              <>
                <Link
                  href={ROUTES.DASHBOARD}
                  className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover transition-colors text-sm font-medium"
                >
                  App
                </Link>
                <div
                  ref={dropdownRef}
                  className="relative"
                  onMouseEnter={() => setDropdownOpen(true)}
                  onMouseLeave={() => setDropdownOpen(false)}
                >
                  <button
                    className="px-3 py-2 border border-subtle text-primary rounded-lg hover:bg-elevated transition-colors text-sm font-medium font-mono cursor-pointer flex items-center gap-2"
                  >
                    {email ? abbreviateEmail(email) : 'Account'}
                    <svg
                      className={`w-4 h-4 transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  <div
                    className={`absolute right-0 mt-1 w-56 bg-surface rounded-lg shadow-lg border border-default py-1 z-50 transition-all duration-200 ${
                      dropdownOpen
                        ? 'opacity-100 visible translate-y-0'
                        : 'opacity-0 invisible -translate-y-2'
                    }`}
                  >
                    {email && (
                      <div className="px-4 py-2 border-b border-default">
                        <p className="text-sm text-muted">Signed in as</p>
                        <p className="text-sm font-medium text-primary truncate">{email}</p>
                      </div>
                    )}

                    <button
                      onClick={handlePasswordAction}
                      className="w-full px-4 py-2 text-left text-sm text-primary hover:bg-elevated transition-colors flex items-center gap-3 cursor-pointer"
                    >
                      <svg className="w-4 h-4 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                      </svg>
                      {userInfo?.is_oauth_user ? 'Set password' : 'Change password'}
                    </button>

                    <div className="border-t border-default my-1"></div>

                    <button
                      onClick={handleLogout}
                      className="w-full px-4 py-2 text-left text-sm text-primary hover:bg-elevated transition-colors flex items-center gap-3 cursor-pointer"
                    >
                      <svg className="w-4 h-4 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      Sign out
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                <Link
                  href={ROUTES.SIGNIN}
                  className="text-secondary hover:text-primary transition-colors text-sm font-medium"
                >
                  Sign In
                </Link>
                <Link
                  href={ROUTES.SIGNUP}
                  className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover transition-colors text-sm font-medium"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      <ChangePasswordModal
        isOpen={changePasswordModalOpen}
        onClose={() => setChangePasswordModalOpen(false)}
      />

      <SetPasswordModal
        isOpen={setPasswordModalOpen}
        onClose={() => setSetPasswordModalOpen(false)}
        onSuccess={handleSetPasswordSuccess}
      />
    </>
  );
}
