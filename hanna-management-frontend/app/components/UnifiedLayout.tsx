'use client';

import { useState, ReactNode, useEffect } from 'react';
import { FiGrid, FiLogOut, FiTool, FiMenu, FiX, FiShield, FiBox, FiSettings, FiCheckSquare } from 'react-icons/fi';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';

const SidebarLink = ({ href, icon: Icon, children }: { href: string; icon: React.ElementType; children: ReactNode }) => {
  const pathname = usePathname();
  const isActive = pathname.startsWith(href);

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

export default function UnifiedLayout({ children }: { children: ReactNode }) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    logout();
    router.push(`/${user?.role}/login`);
  };

  useEffect(() => {
    if (!user) {
      router.push('/admin/login'); // Default to admin login if no user
    }
  }, [user, router]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-100">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  const renderSidebarLinks = () => {
    if (user?.role === 'manufacturer') {
      return (
        <>
          <SidebarLink href="/manufacturer/dashboard" icon={FiGrid}>Dashboard</SidebarLink>
          <SidebarLink href="/manufacturer/job-cards" icon={FiTool}>Job Cards</SidebarLink>
          <SidebarLink href="/manufacturer/warranty-claims" icon={FiShield}>Warranty Claims</SidebarLink>
          <SidebarLink href="/manufacturer/products" icon={FiBox}>Products</SidebarLink>
          <SidebarLink href="/manufacturer/settings" icon={FiSettings}>Settings</SidebarLink>
          <SidebarLink href="/manufacturer/warranties" icon={FiCheckSquare}>Warranties</SidebarLink>
        </>
      );
    }

    if (user?.role === 'technician') {
      return (
        <>
          <SidebarLink href="/technician/dashboard" icon={FiGrid}>Dashboard</SidebarLink>
          <SidebarLink href="/technician/job-cards" icon={FiTool}>Job Cards</SidebarLink>
        </>
      );
    }

    return null;
  };

  return (
    <div className="flex h-screen bg-gray-100 font-sans">
      {/* Sidebar */}
      <aside className={`z-30 fixed inset-y-0 left-0 w-64 px-2 py-4 overflow-y-auto bg-gray-800 text-white transition-transform duration-300 ease-in-out transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0`}>
        <div className="flex justify-between items-center px-4 mb-6">
          <h2 className="text-2xl font-semibold">Hanna Mgt.</h2>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden text-gray-400 hover:text-white">
            <FiX size={24} />
          </button>
        </div>
        <p className="text-sm text-center text-gray-400 capitalize">{user?.role}</p>
        <nav className="space-y-2">
            {renderSidebarLinks()}
        </nav>
        <div className="absolute bottom-0 w-full left-0 px-2 pb-4">
           <button onClick={handleLogout} className="flex items-center w-full px-4 py-3 text-sm font-medium text-gray-300 rounded-md hover:bg-gray-700 hover:text-white">
             <FiLogOut className="w-5 h-5 mr-3" />
             Logout
           </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-col flex-1 w-full overflow-y-auto max-w-full overflow-x-hidden">
        <header className="z-10 py-4 bg-white shadow-md md:hidden">
          <div className="container flex items-center justify-between h-full px-6 mx-auto text-purple-600">
            <button
              className="p-1 -ml-1 mr-5 rounded-md md:hidden focus:outline-none focus:shadow-outline-purple"
              onClick={() => setSidebarOpen(true)}
              aria-label="Menu"
            >
              <FiMenu size={24} />
            </button>
            <span className="font-semibold">Hanna Mgt.</span>
          </div>
        </header>
        <main className="flex-1 p-2 sm:p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
