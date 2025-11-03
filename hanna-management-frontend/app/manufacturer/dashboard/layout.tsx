'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';
import Sidebar from '@/app/components/manufacturer/Sidebar'; // We will create this component

export default function ManufacturerLayout({ children }: { children: React.ReactNode }) {
  const { accessToken, user } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!accessToken || user?.role !== 'manufacturer') {
      router.push('/manufacturer/login'); // Redirect if not a logged-in manufacturer
    }
  }, [accessToken, user, router]);

  return (
    <div className="flex h-screen bg-gray-100">{children}</div>
  );
}