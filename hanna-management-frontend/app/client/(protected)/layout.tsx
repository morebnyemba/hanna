import ClientLayout from '@/app/components/ClientLayout';
import { ReactNode } from 'react';

export default function ClientProtectedLayout({ children }: { children: ReactNode }) {
  return <ClientLayout>{children}</ClientLayout>;
}
