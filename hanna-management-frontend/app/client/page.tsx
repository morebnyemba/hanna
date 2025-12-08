'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';

export default function ClientPage() {
  const router = useRouter();
  const { user } = useAuthStore();

  useEffect(() => {
    if (user) {
      router.push('/client/dashboard');
    } else {
      router.push('/client/login');
    }
  }, [user, router]);

  return (
    <div className="flex h-screen items-center justify-center bg-gray-100">
      <p className="text-gray-500">Redirecting...</p>
    </div>
  );
}
