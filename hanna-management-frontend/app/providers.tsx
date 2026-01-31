'use client';

import { ReactNode } from 'react';

/**
 * Client-side provider wrapper for the application
 * This component ensures that client-side features like Zustand store persistence
 * are properly initialized on app load and page reloads
 */
export function Providers({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
