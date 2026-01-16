'use client';

import { useState, ReactNode, useEffect } from 'react';
import { FiGrid, FiLogOut, FiMenu, FiX, FiDownload, FiUpload, FiBox, FiPlus, FiList, FiCamera, FiChevronLeft, FiChevronRight, FiTruck, FiUsers, FiCalendar, FiTrendingUp } from 'react-icons/fi';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';
import BarcodeScannerButton from './BarcodeScannerButton';
import { useHydration } from '@/app/hooks/useHydration';

const SidebarLink = ({ href, icon: Icon, children, isCollapsed }: { href: string; icon: React.ElementType; children: ReactNode; isCollapsed: boolean }) => {
  const pathname = usePathname();
  const isActive = pathname.startsWith(href);

  return (
    <Link href={href}>
      <span className={`flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors duration-150 ${
        isActive
          ? 'bg-emerald-700 text-white'
          : 'text-gray-300 hover:bg-emerald-700 hover:text-white'
      } ${isCollapsed ? 'justify-center md:justify-center' : ''}`}>
        <Icon className={`w-5 h-5 ${isCollapsed ? 'md:mr-0 mr-3' : 'mr-3'}`} />
        <span className={isCollapsed ? 'md:hidden' : ''}>{children}</span>
      </span>
    </Link>
  );
};

export default function RetailerBranchLayout({ children }: { children: ReactNode }) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const isHydrated = useHydration();
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    logout();
    router.push('/retailer-branch/login');
  };

  useEffect(() => {
    if (isHydrated && !user) {
      router.push('/retailer-branch/login');
    }
  }, [user, router, isHydrated]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  // Show loading state during hydration or when user is not authenticated
  if (!isHydrated || !user) {
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
      <aside className={`z-30 fixed inset-y-0 left-0 w-64 px-2 py-4 bg-emerald-800 text-white transition-all duration-300 ease-in-out transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0 ${isSidebarCollapsed ? 'md:w-16' : 'md:w-64'} flex flex-col`}>
        <div className="flex items-center justify-between px-4 mb-6 shrink-0">
          <h2 className={`text-2xl font-semibold ${isSidebarCollapsed ? 'hidden md:block' : ''}`}>Branch</h2>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden text-gray-400 hover:text-white">
            <FiX size={24} />
          </button>
          <button onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)} className="hidden md:block text-gray-400 hover:text-white ml-auto">
            {isSidebarCollapsed ? <FiChevronRight size={24} /> : <FiChevronLeft size={24} />}
          </button>
        </div>
        <p className={`text-sm text-center text-gray-300 capitalize mb-4 ${isSidebarCollapsed ? 'hidden md:block' : ''}`}>Branch Portal</p>
        <nav className="space-y-2 flex-1 overflow-y-auto pr-1">
          <SidebarLink href="/retailer-branch/dashboard" icon={FiGrid} isCollapsed={isSidebarCollapsed}>Dashboard</SidebarLink>
          <SidebarLink href="/retailer-branch/order-dispatch" icon={FiTruck} isCollapsed={isSidebarCollapsed}>Order Dispatch</SidebarLink>
          <SidebarLink href="/retailer-branch/installer-allocation" icon={FiUsers} isCollapsed={isSidebarCollapsed}>Installer Allocation</SidebarLink>
          <SidebarLink href="/retailer-branch/installer-calendar" icon={FiCalendar} isCollapsed={isSidebarCollapsed}>Installer Calendar</SidebarLink>
          <SidebarLink href="/retailer-branch/performance-metrics" icon={FiTrendingUp} isCollapsed={isSidebarCollapsed}>Performance Metrics</SidebarLink>
          <SidebarLink href="/retailer-branch/check-in-out" icon={FiDownload} isCollapsed={isSidebarCollapsed}>Check-In / Out</SidebarLink>
          <SidebarLink href="/retailer-branch/inventory" icon={FiBox} isCollapsed={isSidebarCollapsed}>Inventory</SidebarLink>
          <SidebarLink href="/retailer-branch/add-serial" icon={FiPlus} isCollapsed={isSidebarCollapsed}>Add Serial Number</SidebarLink>
          <SidebarLink href="/retailer-branch/history" icon={FiList} isCollapsed={isSidebarCollapsed}>History</SidebarLink>
        </nav>
        <div className="mt-4 px-2 pt-2 border-t border-emerald-700">
           <button onClick={handleLogout} className={`flex items-center w-full px-4 py-3 text-sm font-medium text-gray-300 rounded-md hover:bg-emerald-700 hover:text-white ${isSidebarCollapsed ? 'md:justify-center' : ''}`}>
             <FiLogOut className={`w-5 h-5 ${isSidebarCollapsed ? 'md:mr-0 mr-3' : 'mr-3'}`} />
             <span className={isSidebarCollapsed ? 'md:hidden' : ''}>Logout</span>
           </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-col flex-1 w-full overflow-y-auto max-w-full overflow-x-hidden">
        <header className="z-10 py-4 bg-emerald-700 shadow-md">
          <div className="container flex items-center justify-between h-full px-6 mx-auto">
            <button
              className="p-1 -ml-1 mr-5 rounded-md md:hidden focus:outline-none text-white"
              onClick={() => setSidebarOpen(true)}
              aria-label="Menu"
            >
              <FiMenu size={24} />
            </button>
            <span className="font-semibold text-white md:hidden">Branch Portal</span>
            <div className="flex-1"></div>
            <div className="flex items-center gap-2">
              <BarcodeScannerButton />
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
