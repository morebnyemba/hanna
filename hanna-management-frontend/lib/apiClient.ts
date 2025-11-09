import axios from 'axios';
import { useAuthStore } from '@/app/store/authStore';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Use an interceptor to add the auth token to every request
apiClient.interceptors.request.use(
  (config) => {
    console.log('Request:', JSON.stringify(config, null, 2));
    // Zustand's `getState` allows us to access the store outside of a React component.
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request Error:', JSON.stringify(error, null, 2));
    return Promise.reject(error);
  }
);

// You can also add a response interceptor for centralized error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log('Response:', JSON.stringify(response.data, null, 2));
    return response;
  },
  (error) => {
    console.error('Response Error:', JSON.stringify(error, null, 2));
    if (error.response) {
      console.error('Response Error Data:', JSON.stringify(error.response.data, null, 2));
    }
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