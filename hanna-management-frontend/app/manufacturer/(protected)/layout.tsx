'use client';

import { useState, ReactNode } from 'react';
import Sidebar from '@/app/components/manufacturer/Sidebar';
import { useAuthStore } from '@/app/store/authStore';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { FiMenu } from 'react-icons/fi';

export default function ManufacturerLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore();
  const router = useRouter();
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!user) {
      router.push('/manufacturer/login');
    }
  }, [user, router]);

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-100">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar isSidebarOpen={isSidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="relative flex flex-col flex-1 w-full overflow-y-auto">
        <header className="md:hidden z-10 py-4 bg-white shadow-md">
            <div className="container flex items-center justify-between h-full px-6 mx-auto text-purple-600">
                <button
                    className="p-1 -ml-1 mr-5 rounded-md focus:outline-none focus:shadow-outline-purple"
                    onClick={() => setSidebarOpen(true)}
                    aria-label="Menu"
                >
                    <FiMenu size={24} />
                </button>
                <span className="font-semibold">Hanna Mgt.</span>
            </div>
        </header>
        <main className="flex-1 p-4 sm:p-6">
          {children}
        </main>
      </div>
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black opacity-50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}
    </div>
  );
}
