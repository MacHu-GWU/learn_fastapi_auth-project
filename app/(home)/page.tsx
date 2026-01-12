'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { isLoggedIn } from '@/lib/auth';
import { ROUTES } from '@/constants';

export default function Home() {
  // Bug fix: Check login state to show appropriate CTA buttons.
  // Without this, logged-in users would see "Create Account / Sign In" buttons,
  // which is confusing since they're already authenticated.
  const [loggedIn, setLoggedIn] = useState(false);
  // `mounted` prevents hydration mismatch: server renders without localStorage access,
  // so we only show auth-dependent UI after client-side mount.
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setLoggedIn(isLoggedIn());
  }, []);

  return (
    <section className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
        Hello World!
      </h1>
      <p className="text-lg text-gray-600 mb-8">
        Welcome to FastAPI User Authentication Project
      </p>
      {/* Only render buttons after mount to avoid hydration mismatch,
          then show different CTAs based on login state */}
      {mounted && (
        <div className="flex gap-4">
          {loggedIn ? (
            <Link
              href={ROUTES.DASHBOARD}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Go to Dashboard
            </Link>
          ) : (
            <>
              <Link
                href={ROUTES.SIGNUP}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Create Account
              </Link>
              <Link
                href={ROUTES.SIGNIN}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
              >
                Sign In
              </Link>
            </>
          )}
        </div>
      )}
    </section>
  );
}
