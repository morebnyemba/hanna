import RetailerLayout from '@/app/components/RetailerLayout';
import { ReactNode } from 'react';

export default function RetailerProtectedLayout({ children }: { children: ReactNode }) {
  return <RetailerLayout>{children}</RetailerLayout>;
}
