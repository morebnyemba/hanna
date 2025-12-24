import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Retailer Portal',
  description: 'Retailer portal for Hanna - manage branches, inventory, and orders',
};

export default function RetailerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
