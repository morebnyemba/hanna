'use client';

import { useState, ReactNode } from 'react';
import { FiHome, FiUsers, FiShield, FiGitMerge, FiSettings, FiLogOut, FiMenu, FiX, FiPackage, FiBox, FiList, FiArchive } from 'react-icons/fi';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';
import SidebarDropdown from './SidebarDropdown';

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

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const { logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/admin/login');
  };

  return (
    <div className="flex h-screen bg-gray-100 font-sans">
      {/* Sidebar */}
      <aside className={`z-30 flex-shrink-0 w-64 px-2 py-4 overflow-y-auto bg-gray-800 text-white transition-transform duration-300 ease-in-out ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0`}>
        <div className="flex justify-between items-center px-4 mb-6">
          <h2 className="text-2xl font-semibold">Hanna Admin</h2>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden text-gray-400 hover:text-white">
            <FiX size={24} />
          </button>
        </div>
        <nav className="space-y-2">
          <SidebarLink href="/admin/dashboard" icon={FiHome}>Dashboard</SidebarLink>
          <SidebarLink href="/admin/customers" icon={FiUsers}>Customers</SidebarLink>
          <SidebarDropdown title="Products" icon={FiPackage}>
            <SidebarLink href="/admin/products" icon={FiBox}>Products</SidebarLink>
            <SidebarLink href="/admin/product-categories" icon={FiList}>Categories</SidebarLink>
            <SidebarLink href="/admin/serialized-items" icon={FiArchive}>Serialized Items</SidebarLink>
          </SidebarDropdown>
          <SidebarDropdown title="Warranty" icon={FiShield}>
            <SidebarLink href="/admin/warranty-claims" icon={FiShield}>Warranty Claims</SidebarLink>
          </SidebarDropdown>
          <SidebarLink href="/admin/flows" icon={FiGitMerge}>Flows</SidebarLink>
          <SidebarLink href="/admin/settings" icon={FiSettings}>Settings</SidebarLink>
        </nav>
        <div className="absolute bottom-0 w-full left-0 px-2 pb-4">
           <button onClick={handleLogout} className="flex items-center w-full px-4 py-3 text-sm font-medium text-gray-300 rounded-md hover:bg-gray-700 hover:text-white">
             <FiLogOut className="w-5 h-5 mr-3" />
             Logout
           </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-col flex-1 w-full overflow-y-auto">
        <header className="z-10 py-4 bg-white shadow-md md:hidden">
          <div className="container flex items-center justify-between h-full text-purple-600">
            <button
              className="p-1 -ml-1 mr-5 rounded-md md:hidden focus:outline-none focus:shadow-outline-purple"
              onClick={() => setSidebarOpen(true)}
              aria-label="Menu"
            >
              <FiMenu size={24} />
            </button>
            <span className="font-semibold">Hanna Admin</span>
          </div>
        </header>
        <main className="flex-1 p-2 sm:p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
