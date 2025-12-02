'use client';

import { useEffect } from 'react';
import { FiAlertTriangle, FiRefreshCw, FiHome } from 'react-icons/fi';
import Link from 'next/link';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log sanitized error info - only message and digest, not full stack trace
    console.error('Application Error:', error.message, error.digest ? `(digest: ${error.digest})` : '');
  }, [error]);

  return (
    <html lang="en">
      <body>
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-800 via-gray-900 to-black">
          <div role="alert" className="bg-white/10 backdrop-blur-lg rounded-3xl shadow-2xl overflow-hidden border border-white/20 max-w-md mx-4 p-8">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-500/20 mb-4">
                <FiAlertTriangle className="h-8 w-8 text-red-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Something went wrong!</h2>
              <p className="text-white/70 mb-6">
                An unexpected error occurred. Please try again or return to the homepage.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={() => reset()}
                  className="inline-flex items-center justify-center px-6 py-3 border border-transparent rounded-xl shadow-sm text-sm font-medium text-gray-900 bg-white hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white/50 transition-all duration-300"
                >
                  <FiRefreshCw className="mr-2 h-4 w-4" />
                  Try again
                </button>
                <Link
                  href="/"
                  className="inline-flex items-center justify-center px-6 py-3 border border-white/30 rounded-xl shadow-sm text-sm font-medium text-white hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white/50 transition-all duration-300"
                >
                  <FiHome className="mr-2 h-4 w-4" />
                  Go home
                </Link>
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
