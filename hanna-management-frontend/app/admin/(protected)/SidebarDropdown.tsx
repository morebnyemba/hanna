'use client';

import { useState, ReactNode } from 'react';
import { FiChevronDown, FiChevronUp } from 'react-icons/fi';
import { usePathname } from 'next/navigation';

const SidebarDropdown = ({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: ReactNode }) => {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(pathname.startsWith(`/admin/${title.toLowerCase()}`));

  return (
    <div>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-4 py-3 text-sm font-medium text-left text-gray-300 rounded-md hover:bg-gray-700 hover:text-white focus:outline-none"
      >
        <span className="flex items-center">
          <Icon className="w-5 h-5 mr-3" />
          {title}
        </span>
        {isOpen ? <FiChevronUp /> : <FiChevronDown />}
      </button>
      {isOpen && (
        <div className="pl-8 py-2 space-y-2">
          {children}
        </div>
      )}
    </div>
  );
};

export default SidebarDropdown;