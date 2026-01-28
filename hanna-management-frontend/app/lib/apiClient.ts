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

// Token refresh state
let isRefreshing = false;
let failedQueue: Array<{ resolve: (value?: any) => void; reject: (reason?: any) => void }> = [];
let authErrorDispatched = false;

// Function to reset auth error flag (can be called on login)
export const resetAuthErrorFlag = () => {
  authErrorDispatched = false;
};

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

const refreshToken = async (): Promise<string> => {
  const refreshTokenValue = useAuthStore.getState().refreshToken;
  
  if (!refreshTokenValue) {
    throw new Error("Session expired. Please log in again.");
  }

  try {
    const response = await axios.post(
      `${process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw'}/crm-api/auth/token/refresh/`,
      { refresh: refreshTokenValue }
    );

    const { access, refresh: newRefresh } = response.data;
    useAuthStore.getState().setTokens({ access, refresh: newRefresh || refreshTokenValue });
    return access;
  } catch (err) {
    // Refresh failed, log out the user
    useAuthStore.getState().logout();
    throw new Error("Session expired. Please log in again.");
  }
};

// Use an interceptor to add the auth token and CSRF token to every request
apiClient.interceptors.request.use(
  (config) => {
    // Add CSRF token for POST/PUT/PATCH/DELETE requests
    const csrfToken = getCsrfToken();
    console.log('[apiClient] CSRF Token found:', csrfToken ? 'Yes' : 'No');
    console.log('[apiClient] Method:', config.method?.toLowerCase());
    console.log('[apiClient] All cookies:', document.cookie);
    
    if (csrfToken && ['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() || '')) {
      config.headers['X-CSRFToken'] = csrfToken;
      console.log('[apiClient] Added X-CSRFToken header');
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
  async (error) => {
    const originalRequest = error.config;

    // Do not attempt to refresh token for login or refresh endpoints
    if (originalRequest.url?.endsWith('/token/') || originalRequest.url?.endsWith('/token/refresh/')) {
      return Promise.reject(error);
    }

    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      // Check if refresh token exists before attempting refresh
      const storedRefreshToken = useAuthStore.getState().refreshToken;
      
      if (!storedRefreshToken) {
        // No refresh token available, don't attempt refresh
        if (!authErrorDispatched) {
          console.log('No refresh token available - cannot refresh session');
          authErrorDispatched = true;
          // Reset flag after a short delay to allow for future sessions
          setTimeout(() => { authErrorDispatched = false; }, 1000);
        }
        
        // Log out and redirect
        useAuthStore.getState().logout();
        if (typeof window !== 'undefined') {
          window.location.href = '/admin/login';
        }
        return Promise.reject(new Error('Session expired. Please log in again.'));
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return apiClient(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newAccessToken = await refreshToken();
        apiClient.defaults.headers.common['Authorization'] = 'Bearer ' + newAccessToken;
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
        processQueue(null, newAccessToken);
        // Reset auth error flag on successful refresh
        authErrorDispatched = false;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        // Redirect to login on refresh failure
        if (typeof window !== 'undefined') {
          window.location.href = '/admin/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;