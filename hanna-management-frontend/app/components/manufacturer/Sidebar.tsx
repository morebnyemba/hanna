'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { FiGrid, FiLogOut, FiShield } from 'react-icons/fi';
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
  const { logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/manufacturer/login');
  };

  return (
    <aside className="w-64 bg-gray-800 text-white flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-2xl font-bold text-center">Hanna Mgt.</h2>
        <p className="text-sm text-center text-gray-400">Manufacturer</p>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        <SidebarLink href="/manufacturer/dashboard" icon={<FiGrid className="h-5 w-5" />}>
          Dashboard
        </SidebarLink>
        {/* Add more links here as you build out features, e.g., for warranty claims */}
      </nav>
      <div className="p-4 border-t border-gray-700">
        <button onClick={handleLogout} className="w-full flex items-center px-4 py-3 text-gray-200 hover:bg-gray-700 rounded-md transition-colors">
          <FiLogOut className="h-5 w-5" />
          <span className="ml-3">Logout</span>
        </button>
      </div>
    </aside>
  );
}