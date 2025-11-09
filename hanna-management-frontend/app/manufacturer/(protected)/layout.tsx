import UnifiedLayout from '@/app/components/UnifiedLayout';
import { ReactNode } from 'react';

export default function ManufacturerLayout({ children }: { children: ReactNode }) {
  return <UnifiedLayout>{children}</UnifiedLayout>;
}