import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 text-center p-8">
      <div className="max-w-2xl">
        <h1 className="text-5xl font-bold text-gray-900">Welcome to Hanna</h1>
        <p className="mt-4 text-lg text-gray-600">
          The intelligent CRM platform designed to streamline your customer interactions,
          manage warranties, and empower your business with powerful analytics.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link href="/dashboard" className="px-6 py-3 font-semibold text-white bg-indigo-600 rounded-md hover:bg-indigo-700">
            Admin Dashboard
          </Link>
          <Link href="/login" className="px-6 py-3 font-semibold text-indigo-700 bg-indigo-100 rounded-md hover:bg-indigo-200">
            Login
          </Link>
        </div>
        <div className="mt-16 text-sm text-gray-500">
          <p>Are you a manufacturer or technician? Access your dedicated portal below.</p>
          <div className="mt-4 flex justify-center gap-4">
            {/* These links are placeholders for future login pages */}
            <Link href="/manufacturer/login" className="text-indigo-600 hover:underline">
              Manufacturer Portal
            </Link>
            <span>&bull;</span>
            <Link href="/technician/login" className="text-indigo-600 hover:underline">
              Technician Portal
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}