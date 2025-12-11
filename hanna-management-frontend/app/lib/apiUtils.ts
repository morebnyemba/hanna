/**
 * Utility functions for API error handling
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
