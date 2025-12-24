import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Manufacturer Portal',
  description: 'Manufacturer portal for Hanna - manage products, warranties, claims, and analytics',
};

export default function ManufacturerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
