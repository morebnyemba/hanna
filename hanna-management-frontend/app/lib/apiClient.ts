import axios from 'axios';
import { useAuthStore } from '@/app/store/authStore';

// Helper function to get CSRF token from cookies
function getCsrfToken(): string | null {
  let csrfToken = null;
  if (typeof document !== 'undefined' && document.cookie) {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith('csrftoken=')) {
        csrfToken = decodeURIComponent(cookie.substring('csrftoken='.length));
        break;
      }
    }
  }
  return csrfToken;
}

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable sending cookies for session-based auth
});

// Use an interceptor to add the auth token and CSRF token to every request
apiClient.interceptors.request.use(
  (config) => {
    // Add CSRF token for POST/PUT/PATCH/DELETE requests
    const csrfToken = getCsrfToken();
    if (csrfToken && ['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() || '')) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    
    // Zustand's `getState` allows us to access the store outside of a React component.
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for centralized error handling and pagination normalization
apiClient.interceptors.response.use(
  (response) => {
    // Automatically handle paginated responses from Django REST Framework
    // If the response has 'results' field (pagination), normalize it
    if (response.data && typeof response.data === 'object' && 'results' in response.data) {
      // Store the original response data with pagination info
      response.data._pagination = {
        count: response.data.count,
        next: response.data.next,
        previous: response.data.previous,
      };
      // For backward compatibility, keep the results structure
      // but also ensure direct array access works
      if (!Array.isArray(response.data)) {
        // Don't override, just keep as-is with results property
      }
    }
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // Handle unauthorized errors, e.g., by logging out the user.
      // This prevents you from having to write this logic in every component.
      console.error("Unauthorized request, logging out.");
      useAuthStore.getState().logout();
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;