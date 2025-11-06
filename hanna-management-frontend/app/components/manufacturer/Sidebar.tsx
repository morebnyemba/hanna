'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { FiGrid, FiLogOut, FiTool, FiMenu, FiX } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

const SidebarLink = ({ href, icon, children }: { href: string; icon: React.ReactNode; children: React.ReactNode }) => {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link href={href} className={`flex items-center px-4 py-3 text-gray-200 hover:bg-gray-700 rounded-md transition-colors ${isActive ? 'bg-gray-700' : ''}`}>
      {icon}
      <span className="ml-3">{children}</span>
    </Link>
  );
};

export default function Sidebar() {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const { logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/manufacturer/login');
  };

  return (
    <>
      {/* Mobile header */}
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

      {/* Sidebar */}
      <aside className={`z-30 flex-shrink-0 w-64 px-2 py-4 overflow-y-auto bg-gray-800 text-white transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex justify-between items-center px-4 mb-6">
          <h2 className="text-2xl font-bold text-center">Hanna Mgt.</h2>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden text-gray-400 hover:text-white">
            <FiX size={24} />
          </button>
        </div>
        <p className="text-sm text-center text-gray-400">Manufacturer</p>
        <nav className="flex-1 p-4 space-y-2">
          <SidebarLink href="/manufacturer/dashboard" icon={<FiGrid className="h-5 w-5" />}>
            Dashboard
          </SidebarLink>
          <SidebarLink href="/manufacturer/job-cards" icon={<FiTool className="h-5 w-5" />}>
            Job Cards
          </SidebarLink>
        </nav>
        <div className="p-4 border-t border-gray-700">
          <button onClick={handleLogout} className="w-full flex items-center px-4 py-3 text-gray-200 hover:bg-gray-700 rounded-md transition-colors">
            <FiLogOut className="h-5 w-5" />
            <span className="ml-3">Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
