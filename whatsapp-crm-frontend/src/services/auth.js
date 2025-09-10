import { jwtDecode } from 'jwt-decode';
import apiClient from '@/lib/api'; // Use the central axios client

const ACCESS_TOKEN_KEY = 'accessToken';
const REFRESH_TOKEN_KEY = 'refreshToken';

export const authService = {
  // Token Management
  storeTokens(accessToken, refreshToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
  },
  clearTokens() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem('user'); // Also clear user from jotai/storage
  },
  getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),

  // API Calls
  async login(username, password) {
    try {
      // Use the central apiClient. The interceptor is now safe for this call.
      const response = await apiClient.post('/crm-api/auth/token/', { username, password });
      const { access, refresh } = response.data;
      this.storeTokens(access, refresh);
      const user = jwtDecode(access);
      return { success: true, user };
    } catch (error) {
      // The interceptor in apiClient will toast errors, but we still need to return failure.
      const errorMessage = error.response?.data?.detail || 'Login failed. Please check credentials.';
      return { success: false, error: errorMessage };
    }
  },

  async logout(notifyBackend = true) {
    const refreshToken = this.getRefreshToken();
    if (notifyBackend && refreshToken) {
      try {
        // Use apiClient for consistency.
        await apiClient.post('/crm-api/auth/token/blacklist/', { refresh: refreshToken });
      } catch (error) {
        // Don't block client-side logout if the backend call fails.
        console.warn("Failed to blacklist token on server.", error);
      }
    }
    this.clearTokens();
  },

  // refreshTokenInternal is no longer needed here.
  // The interceptor in `lib/api.js` handles all token refreshing automatically.
};