import TechnicianLayout from '@/app/components/TechnicianLayout';
import { ReactNode } from 'react';

export default function TechnicianProtectedLayout({ children }: { children: ReactNode }) {
  return <TechnicianLayout>{children}</TechnicianLayout>;
}

