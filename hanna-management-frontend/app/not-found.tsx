'use client';

import Link from 'next/link';
import { FiHome, FiTool } from 'react-icons/fi';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full text-center">
        {/* Construction Icon */}
        <div className="mb-8 relative">
          <div className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-gradient-to-r from-yellow-400 to-orange-500 shadow-2xl animate-pulse">
            <FiTool className="w-16 h-16 text-white" />
          </div>
          {/* Animated circles */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-40 h-40 border-4 border-yellow-300 rounded-full animate-ping opacity-20"></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-48 border-4 border-orange-300 rounded-full animate-ping opacity-10"></div>
        </div>

        {/* Message */}
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-4">
          Under Construction
        </h1>
        <h2 className="text-2xl md:text-3xl font-semibold text-orange-600 mb-6">
          🚧 We're Building This Page 🚧
        </h2>
        <p className="text-lg text-gray-700 mb-4 leading-relaxed">
          This part of the website is currently under construction.
        </p>
        <p className="text-gray-600 mb-8">
          Our team is working hard to bring you an amazing experience. Please check back soon!
        </p>

        {/* Divider */}
        <div className="w-24 h-1 bg-gradient-to-r from-yellow-400 to-orange-500 mx-auto mb-8 rounded-full"></div>

        {/* Call to Action */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/"
            className="inline-flex items-center justify-center px-8 py-4 text-base font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl hover:from-indigo-500 hover:to-purple-500 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
          >
            <FiHome className="w-5 h-5 mr-2" />
            Go to Homepage
          </Link>
          <Link
            href="/client/shop"
            className="inline-flex items-center justify-center px-8 py-4 text-base font-semibold text-gray-700 bg-white rounded-xl hover:bg-gray-50 border-2 border-gray-300 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
          >
            Visit Our Shop
          </Link>
        </div>

        {/* Status Message */}
        <div className="mt-12 p-6 bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/50">
          <div className="flex items-start gap-4 text-left">
            <div className="flex-shrink-0 mt-1">
              <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse"></div>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">Development Status</h3>
              <p className="text-sm text-gray-600">
                We're actively developing new features and improvements. Stay tuned for updates!
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-sm text-gray-500">
          <p>If you believe this is an error, please contact support.</p>
        </div>
      </div>
    </div>
  );
}
