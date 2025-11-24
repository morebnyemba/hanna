"use client";
import { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FiHome, FiBarChart2, FiBox, FiWifi, FiSettings } from 'react-icons/fi';

const navLinks = [
  { href: '/client/dashboard', label: 'Dashboard', icon: FiHome },
  { href: '/client/monitoring', label: 'Monitoring', icon: FiWifi },
  { href: '/client/shop', label: 'Shop', icon: FiBox },
  { href: '/client/settings', label: 'Settings', icon: FiSettings },
];

export default function ClientLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 bg-purple-800 text-white flex flex-col py-6 px-2">
        <h2 className="text-2xl font-semibold mb-8 px-4">Hanna Client</h2>
        <nav className="flex-1 space-y-2">
          {navLinks.map(link => (
            <Link key={link.href + link.label} href={link.href}>
              <span className={`flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors duration-150 ${
                pathname === link.href ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}>
                <link.icon className="w-5 h-5 mr-3" />
                {link.label}
              </span>
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-6 bg-gray-100">{children}</main>
    </div>
  );
}
