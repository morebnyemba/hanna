import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Shop',
  description: 'Hanna Digital Shop - Browse and purchase solar products, inverters, batteries, and more',
  keywords: ['solar shop', 'solar products', 'inverters', 'batteries', 'solar panels', 'Zimbabwe'],
  openGraph: {
    title: 'Hanna Digital Shop',
    description: 'Browse and purchase quality solar products',
    type: 'website',
  },
};

export default function ShopLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
