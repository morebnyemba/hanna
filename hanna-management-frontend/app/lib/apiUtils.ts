/**
 * Utility functions for API error handling and response normalization
 */

interface ApiError {
  response?: {
    data?: {
      error?: string;
      message?: string;
    };
  };
  message?: string;
}

/**
 * Extracts error message from API response
 * @param error - The error object from API call
 * @param fallbackMessage - Default message if no error message found
 * @returns Formatted error message
 */
export function extractErrorMessage(error: unknown, fallbackMessage: string = 'An error occurred'): string {
  const apiError = error as ApiError;
  return (
    apiError.response?.data?.error ||
    apiError.response?.data?.message ||
    apiError.message ||
    fallbackMessage
  );
}

/**
 * Normalizes paginated API responses from Django REST Framework
 * Extracts the results array from paginated responses or returns the data as-is
 * @param data - The API response data
 * @returns Normalized array of results
 */
export function normalizePaginatedResponse<T>(data: any): T[] {
  // If data has 'results' property (paginated response), return results
  if (data && typeof data === 'object' && 'results' in data && Array.isArray(data.results)) {
    return data.results as T[];
  }
  
  // If data is already an array, return as-is
  if (Array.isArray(data)) {
    return data as T[];
  }
  
  // If neither, return empty array to prevent errors
  console.warn('API response is not in expected format (not paginated or array):', data);
  return [];
}

/**
 * Extracts pagination metadata from a paginated response
 * @param data - The API response data
 * @returns Pagination metadata or null if not paginated
 */
export function extractPaginationInfo(data: any): { count: number; next: string | null; previous: string | null } | null {
  if (data && typeof data === 'object' && 'count' in data) {
    return {
      count: data.count || 0,
      next: data.next || null,
      previous: data.previous || null,
    };
  }
  return null;
}
