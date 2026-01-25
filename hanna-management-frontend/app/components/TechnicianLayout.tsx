'use client';

import { useState, ReactNode, useEffect } from 'react';
import { FiGrid, FiLogOut, FiTool, FiMenu, FiX, FiBarChart2, FiChevronLeft, FiChevronRight, FiArchive, FiList, FiCheckSquare, FiCamera, FiClock } from 'react-icons/fi';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';
import BarcodeScannerButton from './BarcodeScannerButton';

const SidebarLink = ({ href, icon: Icon, children, isCollapsed }: { href: string; icon: React.ElementType; children: ReactNode; isCollapsed: boolean }) => {
  const pathname = usePathname();
  const isActive = pathname.startsWith(href);

  return (
    <Link href={href}>
      <span className={`flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors duration-150 ${
        isActive
          ? 'bg-green-700 text-white'
          : 'text-gray-300 hover:bg-green-700 hover:text-white'
      } ${isCollapsed ? 'justify-center md:justify-center' : ''}`}>
        <Icon className={`w-5 h-5 ${isCollapsed ? 'md:mr-0 mr-3' : 'mr-3'}`} />
        <span className={isCollapsed ? 'md:hidden' : ''}>{children}</span>
      </span>
    </Link>
  );
};

export default function TechnicianLayout({ children }: { children: ReactNode }) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    logout();
    router.push('/technician/login');
  };

  useEffect(() => {
    if (!user) {
      router.push('/technician/login');
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
      <aside className={`z-30 fixed inset-y-0 left-0 w-64 px-2 py-4 overflow-y-auto bg-green-800 text-white transition-all duration-300 ease-in-out transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0 ${isSidebarCollapsed ? 'md:w-16' : 'md:w-64'}`}>
        <div className="flex items-center justify-between px-4 mb-6">
          <h2 className={`text-2xl font-semibold ${isSidebarCollapsed ? 'hidden md:block' : ''}`}>Hanna Tech</h2>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden text-gray-400 hover:text-white">
            <FiX size={24} />
          </button>
          <button onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)} className="hidden md:block text-gray-400 hover:text-white ml-auto">
            {isSidebarCollapsed ? <FiChevronRight size={24} /> : <FiChevronLeft size={24} />}
          </button>
        </div>
        <p className={`text-sm text-center text-gray-400 capitalize mb-4 ${isSidebarCollapsed ? 'hidden md:block' : ''}`}>Technician</p>
        <nav className="space-y-2">
          <SidebarLink href="/technician/dashboard" icon={FiGrid} isCollapsed={isSidebarCollapsed}>Dashboard</SidebarLink>
          <SidebarLink href="/technician/analytics" icon={FiBarChart2} isCollapsed={isSidebarCollapsed}>Analytics</SidebarLink>
          <SidebarLink href="/technician/installations" icon={FiTool} isCollapsed={isSidebarCollapsed}>Installations</SidebarLink>
          <SidebarLink href="/technician/checklists" icon={FiCheckSquare} isCollapsed={isSidebarCollapsed}>Checklists</SidebarLink>
          <SidebarLink href="/technician/job-cards" icon={FiArchive} isCollapsed={isSidebarCollapsed}>Job Cards</SidebarLink>
          <SidebarLink href="/technician/photos" icon={FiCamera} isCollapsed={isSidebarCollapsed}>Photos</SidebarLink>
          <SidebarLink href="/technician/check-in-out" icon={FiList} isCollapsed={isSidebarCollapsed}>Check-In/Out</SidebarLink>
          <SidebarLink href="/technician/installation-history" icon={FiClock} isCollapsed={isSidebarCollapsed}>Installation History</SidebarLink>
        </nav>
        <div className="absolute bottom-0 w-full left-0 px-2 pb-4">
           <button onClick={handleLogout} className={`flex items-center w-full px-4 py-3 text-sm font-medium text-gray-300 rounded-md hover:bg-green-700 hover:text-white ${isSidebarCollapsed ? 'md:justify-center' : ''}`}>
             <FiLogOut className={`w-5 h-5 ${isSidebarCollapsed ? 'md:mr-0 mr-3' : 'mr-3'}`} />
             <span className={isSidebarCollapsed ? 'md:hidden' : ''}>Logout</span>
           </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-col flex-1 w-full overflow-y-auto max-w-full overflow-x-hidden">
        <header className="z-10 py-4 bg-green-700 shadow-md">
          <div className="container flex items-center justify-between h-full px-6 mx-auto">
            <button
              className="p-1 -ml-1 mr-5 rounded-md md:hidden focus:outline-none text-white"
              onClick={() => setSidebarOpen(true)}
              aria-label="Menu"
            >
              <FiMenu size={24} />
            </button>
            <span className="font-semibold text-white md:hidden">Hanna Tech</span>
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
