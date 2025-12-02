'use client';

import { useEffect } from 'react';
import { FiAlertTriangle, FiRefreshCw } from 'react-icons/fi';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log sanitized error info - only message and digest, not full stack trace
    console.error('Retailer Branch Login Error:', error.message, error.digest ? `(digest: ${error.digest})` : '');
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-700 via-emerald-800 to-emerald-900">
      <div role="alert" className="bg-white/10 backdrop-blur-lg rounded-3xl shadow-2xl overflow-hidden border border-white/20 max-w-md mx-4 p-8">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-500/20 mb-4">
            <FiAlertTriangle className="h-8 w-8 text-red-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Something went wrong!</h2>
          <p className="text-white/70 mb-6">
            We encountered an error while loading the Branch Portal login page.
          </p>
          <button
            onClick={() => reset()}
            className="inline-flex items-center px-6 py-3 border border-transparent rounded-xl shadow-sm text-sm font-medium text-emerald-700 bg-white hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white/50 transition-all duration-300"
          >
            <FiRefreshCw className="mr-2 h-4 w-4" />
            Try again
          </button>
        </div>
      </div>
    </div>
  );
}
