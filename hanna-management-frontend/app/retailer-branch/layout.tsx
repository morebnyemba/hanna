import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Retailer Branch Portal',
  description: 'Retailer branch portal for Hanna - manage branch inventory, orders, and dispatch',
};

export default function RetailerBranchLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
