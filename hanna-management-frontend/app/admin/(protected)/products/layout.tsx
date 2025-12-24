import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Products',
  description: 'Manage product catalog, inventory, pricing, and categories',
};

export default function ProductsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
