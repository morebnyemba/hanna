import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Customer Management',
  description: 'View and manage customer profiles, interactions, and history',
};

export default function CustomersLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
