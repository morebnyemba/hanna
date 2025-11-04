'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';
import Sidebar from '@/app/components/manufacturer/Sidebar'; // We will create this component
import { useHydration } from '@/hooks/useHydration';

export default function ManufacturerLayout({ children }: { children: React.ReactNode }) {
  const { accessToken, user } = useAuthStore();
  const router = useRouter();
  const isHydrated = useHydration();

  useEffect(() => {
    // Only run this check if the store has been hydrated.
    if (isHydrated && (!accessToken || user?.role !== 'manufacturer')) {
      router.push('/manufacturer/login'); // Redirect if not a logged-in manufacturer
    }
  }, [isHydrated, accessToken, user, router]);

  // While the auth store is loading from localStorage, show a loading screen.
  // This prevents the redirect from happening before the user's auth state is confirmed.
  if (!isHydrated) {
    return <div className="flex h-screen w-full items-center justify-center bg-gray-100">Loading...</div>;
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      {children}
    </div>
  );
}