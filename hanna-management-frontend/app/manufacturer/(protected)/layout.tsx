'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';
import Sidebar from '@/app/components/manufacturer/Sidebar'; // We will create this component

export default function ManufacturerLayout({ children }: { children: React.ReactNode }) {
  const { accessToken, user, isLoaded, setLoaded } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    // This effect ensures that the store is marked as loaded once it hydrates.
    // The `persist` middleware will rehydrate the store on mount.
    setLoaded();
  }, [setLoaded]);

  useEffect(() => {
    if (isLoaded && (!accessToken || user?.role !== 'manufacturer')) {
      router.push('/manufacturer/login'); // Redirect if not a logged-in manufacturer
    }
  }, [isLoaded, accessToken, user, router]);

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      {children}
    </div>
  );
}