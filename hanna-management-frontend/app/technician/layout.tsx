import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Technician Portal',
  description: 'Technician portal for Hanna - manage installations, check-in/out, and track your work',
};

export default function TechnicianLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
