import ManufacturerLayout from '@/app/components/ManufacturerLayout';
import { ReactNode } from 'react';

export default function ManufacturerProtectedLayout({ children }: { children: ReactNode }) {
  return <ManufacturerLayout>{children}</ManufacturerLayout>;
}