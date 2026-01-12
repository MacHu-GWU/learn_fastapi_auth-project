import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Remove console.log in production builds
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  async rewrites() {
    // Only use rewrites in local development
    // In production (Vercel), the Python serverless functions handle /api/* directly
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://127.0.0.1:8000/api/:path*',
        },
        {
          source: '/auth/:path*',
          destination: 'http://127.0.0.1:8000/auth/:path*',
        },
        {
          source: '/health',
          destination: 'http://127.0.0.1:8000/health',
        },
        {
          source: '/docs',
          destination: 'http://127.0.0.1:8000/docs',
        },
        {
          source: '/openapi.json',
          destination: 'http://127.0.0.1:8000/openapi.json',
        },
      ];
    }
    return [];
  },
};

export default nextConfig;
