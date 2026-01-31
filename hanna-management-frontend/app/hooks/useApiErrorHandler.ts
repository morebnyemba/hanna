import { useState, useCallback } from 'react';
import { AxiosError } from 'axios';

interface ApiErrorState {
  message: string | null;
  statusCode: number | null;
  details: any;
}

export function useApiErrorHandler() {
  const [error, setError] = useState<ApiErrorState | null>(null);

  const handleError = useCallback((err: any) => {
    if (err instanceof AxiosError) {
      const statusCode = err.response?.status || null;
      const message = err.response?.data?.message 
        || err.response?.data?.detail 
        || err.message 
        || 'An unexpected error occurred';
      
      const details = err.response?.data || null;

      setError({
        message,
        statusCode,
        details,
      });

      // Log for debugging
      console.error('API Error:', {
        statusCode,
        message,
        details,
        url: err.config?.url,
      });
    } else {
      const message = err?.message || 'An unexpected error occurred';
      setError({
        message,
        statusCode: null,
        details: null,
      });

      console.error('Non-Axios Error:', err);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    error,
    handleError,
    clearError,
  };
}

// Helper to extract user-friendly error message
export function getErrorMessage(error: any): string {
  if (!error) return 'An unexpected error occurred';
  
  if (error.response?.data) {
    const data = error.response.data;
    
    // Handle DRF validation errors
    if (typeof data === 'object') {
      // Check for common error fields
      if (data.detail) return data.detail;
      if (data.message) return data.message;
      if (data.error) return data.error;
      
      // Handle field-specific errors
      const fieldErrors = Object.keys(data)
        .filter(key => key !== 'detail' && key !== 'message')
        .map(key => {
          const value = data[key];
          if (Array.isArray(value)) {
            return `${key}: ${value.join(', ')}`;
          }
          return `${key}: ${value}`;
        });
      
      if (fieldErrors.length > 0) {
        return fieldErrors.join('; ');
      }
    }
    
    if (typeof data === 'string') return data;
  }
  
  if (error.message) return error.message;
  
  return 'An unexpected error occurred';
}
