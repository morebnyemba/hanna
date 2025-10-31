'use client';

import Link from 'next/link';

export default function TechnicianDashboardPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-100">
      <h1 className="text-3xl font-bold">Technician Dashboard</h1>
      <p className="mt-4 text-gray-600">This page is under construction.</p>
      <Link href="/" className="mt-6 text-indigo-600 hover:underline">Go back to Home</Link>
    </div>
  );
}