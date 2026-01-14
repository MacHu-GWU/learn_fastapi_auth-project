'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { isLoggedIn } from '@/lib/auth';
import { ROUTES } from '@/constants';

export default function Home() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setLoggedIn(isLoggedIn());
  }, []);

  return (
    <div className="min-h-[calc(100vh-140px)] flex flex-col">
      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center px-4 py-16">
        <div className="max-w-3xl mx-auto text-center">
          {/* Terminal-style badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 mb-8 rounded-full border border-[#1F2937] bg-[#111827]">
            <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
            <span className="text-sm font-mono text-[#94A3B8]">
              Production-ready SaaS Template
            </span>
          </div>

          {/* Main headline */}
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
            <span className="text-gradient">Ship faster</span>
            <br />
            <span className="text-[#F1F5F9]">with auth solved</span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-[#94A3B8] mb-10 max-w-xl mx-auto leading-relaxed">
            A minimal, production-ready authentication template.
            <br className="hidden md:block" />
            Fork it. Build on it. Ship it.
          </p>

          {/* CTA Buttons */}
          {mounted && (
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              {loggedIn ? (
                <Link
                  href={ROUTES.DASHBOARD}
                  className="group inline-flex items-center gap-2 px-6 py-3 bg-[#3B82F6] text-white rounded-lg hover:bg-[#2563EB] transition-colors font-medium glow-primary"
                >
                  Go to Dashboard
                  <svg
                    className="w-4 h-4 group-hover:translate-x-0.5 transition-transform"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </Link>
              ) : (
                <>
                  <Link
                    href={ROUTES.SIGNUP}
                    className="group inline-flex items-center gap-2 px-6 py-3 bg-[#3B82F6] text-white rounded-lg hover:bg-[#2563EB] transition-colors font-medium glow-primary"
                  >
                    Get Started
                    <svg
                      className="w-4 h-4 group-hover:translate-x-0.5 transition-transform"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </Link>
                  <Link
                    href={ROUTES.SIGNIN}
                    className="inline-flex items-center gap-2 px-6 py-3 border border-[#374151] text-[#F1F5F9] rounded-lg hover:bg-[#111827] transition-colors font-medium"
                  >
                    Sign In
                  </Link>
                </>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Feature highlights */}
      <section className="px-4 py-12 border-t border-[#1F2937]">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="p-5 rounded-lg border border-[#1F2937] bg-[#111827] hover:border-[#374151] transition-colors">
              <div className="w-10 h-10 rounded-lg bg-[#3B82F6]/10 flex items-center justify-center mb-4">
                <svg className="w-5 h-5 text-[#3B82F6]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="font-semibold text-[#F1F5F9] mb-2">Auth Built-in</h3>
              <p className="text-sm text-[#94A3B8] leading-relaxed">
                Email/password + Google OAuth. JWT refresh. Email verification. Ready to go.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-5 rounded-lg border border-[#1F2937] bg-[#111827] hover:border-[#374151] transition-colors">
              <div className="w-10 h-10 rounded-lg bg-[#10B981]/10 flex items-center justify-center mb-4">
                <svg className="w-5 h-5 text-[#10B981]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="font-semibold text-[#F1F5F9] mb-2">Security First</h3>
              <p className="text-sm text-[#94A3B8] leading-relaxed">
                CSRF protection. Rate limiting. Secure token handling. Production hardened.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-5 rounded-lg border border-[#1F2937] bg-[#111827] hover:border-[#374151] transition-colors">
              <div className="w-10 h-10 rounded-lg bg-[#3B82F6]/10 flex items-center justify-center mb-4">
                <svg className="w-5 h-5 text-[#3B82F6]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
              </div>
              <h3 className="font-semibold text-[#F1F5F9] mb-2">Modern Stack</h3>
              <p className="text-sm text-[#94A3B8] leading-relaxed">
                Next.js + FastAPI + TypeScript. Deploy to Vercel in minutes.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
