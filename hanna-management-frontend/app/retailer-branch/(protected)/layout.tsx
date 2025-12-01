import RetailerBranchLayout from '@/app/components/RetailerBranchLayout';
import { ReactNode } from 'react';

export default function RetailerBranchProtectedLayout({ children }: { children: ReactNode }) {
  return <RetailerBranchLayout>{children}</RetailerBranchLayout>;
}
