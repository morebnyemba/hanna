/**
 * Re-export of apiClient for backward compatibility
 * 
 * IMPORTANT: This file exists only for backward compatibility with existing imports.
 * All new code should import from '@/app/lib/apiClient' directly.
 * 
 * This re-export allows existing code using '@/lib/apiClient' to continue working
 * without changes while we maintain a single source of truth at '@/app/lib/apiClient'.
 */
export { default } from '@/app/lib/apiClient';
