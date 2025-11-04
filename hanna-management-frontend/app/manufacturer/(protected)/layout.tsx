'use client';

import Sidebar from '@/app/components/manufacturer/Sidebar'; // We will create this component

export default function ManufacturerLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      {children}
    </div>
  );
}