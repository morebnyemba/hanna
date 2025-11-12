import AdminLayout from '@/app/components/AdminLayout';
import { ReactNode } from 'react';

export default function AdminProtectedLayout({ children }: { children: ReactNode }) {
  return <AdminLayout>{children}</AdminLayout>;
}
