'use client';

import { useState, ReactNode, useEffect } from 'react';
import { FiHome, FiBarChart2, FiBox, FiWifi, FiSettings, FiLogOut, FiMenu, FiX, FiTool, FiShield, FiSun } from 'react-icons/fi';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';

const SidebarLink = ({ href, icon: Icon, children }: { href: string; icon: React.ElementType; children: ReactNode }) => {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link href={href}>
      <span className={`flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors duration-150 ${
        isActive
          ? 'bg-gray-700 text-white'
          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
      }`}>
        <Icon className="w-5 h-5 mr-3" />
        {children}
      </span>
    </Link>
  );
};

export default function ClientLayout({ children }: { children: ReactNode }) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    logout();
    router.push('/client/login');
  };

  useEffect(() => {
    if (!user) {
      router.push('/client/login');
    }
  }, [user, router]);

  useEffect(() => {
    // Close sidebar on navigation - intentional for UX
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSidebarOpen(false);
  }, [pathname]);

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-100">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-100 font-sans">
      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`z-30 fixed inset-y-0 left-0 w-64 px-2 py-4 bg-purple-800 text-white transition-transform duration-300 ease-in-out transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0 flex flex-col`}>
        <div className="flex justify-between items-center px-4 mb-6 shrink-0">
          <h2 className="text-2xl font-semibold">Hanna Client</h2>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden text-gray-400 hover:text-white">
            <FiX size={24} />
          </button>
        </div>
        <nav className="space-y-2 flex-1 overflow-y-auto pr-1">
          <SidebarLink href="/client/dashboard" icon={FiHome}>Dashboard</SidebarLink>
          <SidebarLink href="/client/my-installation" icon={FiSun}>My Installation</SidebarLink>
          <SidebarLink href="/client/monitoring" icon={FiWifi}>Monitoring</SidebarLink>
          <SidebarLink href="/client/orders" icon={FiBarChart2}>My Orders</SidebarLink>
          <SidebarLink href="/client/shop" icon={FiBox}>My Shop</SidebarLink>
          <SidebarLink href="/client/warranties" icon={FiShield}>My Warranties</SidebarLink>
          <SidebarLink href="/client/service-requests" icon={FiTool}>Service Requests</SidebarLink>
          <SidebarLink href="/client/settings" icon={FiSettings}>Settings</SidebarLink>
        </nav>
        <div className="mt-4 px-2 pt-2 border-t border-purple-700">
           <button onClick={handleLogout} className="flex items-center w-full px-4 py-3 text-sm font-medium text-gray-300 rounded-md hover:bg-gray-700 hover:text-white">
             <FiLogOut className="w-5 h-5 mr-3" />
             Logout
           </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-col flex-1 w-full overflow-y-auto">
        <header className="z-10 py-4 bg-purple-700 shadow-md">
          <div className="container flex items-center justify-between h-full px-6 mx-auto">
            <button
              className="p-1 -ml-1 mr-5 rounded-md md:hidden focus:outline-none text-white"
              onClick={() => setSidebarOpen(true)}
              aria-label="Menu"
            >
              <FiMenu size={24} />
            </button>
            <span className="font-semibold text-white md:hidden">Hanna Client</span>
            <div className="flex-1"></div>
            <div className="flex items-center gap-2">
              <span className="text-white text-sm">Welcome, {user.username}</span>
            </div>
          </div>
        </header>
        <main className="flex-1 p-2 sm:p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
