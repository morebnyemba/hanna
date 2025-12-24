import type { Metadata } from 'next';
import AdminLayout from '@/app/components/AdminLayout';
import { ReactNode } from 'react';

export const metadata: Metadata = {
  title: {
    default: 'Admin Dashboard',
    template: '%s | Admin',
  },
  description: 'Admin dashboard - Manage system operations, users, analytics, and configurations',
};

export default function AdminProtectedLayout({ children }: { children: ReactNode }) {
  return <AdminLayout>{children}</AdminLayout>;
}
