/**
 * Utility functions for API error handling and response normalization
 */

interface ApiError {
  response?: {
    data?: unknown;
  };
  message?: string;
}

/**
 * Flattens Django REST Framework field errors into a readable string.
 * Handles shapes like { sku: ["already exists"], detail: "Not found" }
 * and { non_field_errors: ["..."] }.
 */
function formatFieldErrors(data: Record<string, unknown>): string | null {
  const parts: string[] = [];
  for (const [field, value] of Object.entries(data)) {
    const text = Array.isArray(value) ? value.join(' ') : String(value);
    if (!text) continue;
    parts.push(field === 'non_field_errors' || field === 'detail' ? text : `${field}: ${text}`);
  }
  return parts.length > 0 ? parts.join(' • ') : null;
}

/**
 * Extracts error message from API response
 * @param error - The error object from API call
 * @param fallbackMessage - Default message if no error message found
 * @returns Formatted error message
 */
export function extractErrorMessage(error: unknown, fallbackMessage: string = 'An error occurred'): string {
  const apiError = error as ApiError;
  const data = apiError.response?.data;

  if (typeof data === 'string' && data) return data;

  if (data && typeof data === 'object') {
    const record = data as Record<string, unknown>;
    if (typeof record.error === 'string' && record.error) return record.error;
    if (typeof record.message === 'string' && record.message) return record.message;
    const fieldErrors = formatFieldErrors(record);
    if (fieldErrors) return fieldErrors;
  }

  return apiError.message || fallbackMessage;
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
