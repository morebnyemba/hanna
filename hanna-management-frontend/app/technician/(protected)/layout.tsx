import UnifiedLayout from '@/app/components/UnifiedLayout';
import { ReactNode } from 'react';

export default function TechnicianLayout({ children }: { children: ReactNode }) {
  return <UnifiedLayout>{children}</UnifiedLayout>;
}

