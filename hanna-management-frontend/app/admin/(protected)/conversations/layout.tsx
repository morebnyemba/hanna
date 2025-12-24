import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Conversations',
  description: 'Manage WhatsApp conversations, messages, and customer communications',
};

export default function ConversationsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
