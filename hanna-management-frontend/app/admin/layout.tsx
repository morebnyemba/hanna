import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Admin Portal',
  description: 'Admin management portal for Hanna system - manage users, settings, analytics, and system configuration',
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
