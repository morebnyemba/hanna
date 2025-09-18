// c:\Users\Administrator\Desktop\HANNA\whatsapp-crm-frontend\src\context\AuthContext.jsx
import React, { createContext, useContext, useEffect, useCallback } from 'react';
import { useAtom } from 'jotai';
import { toast } from 'sonner';
import { jwtDecode } from 'jwt-decode';

import apiClient from '@/lib/api'; // Import the central axios client
import { authService } from '../services/auth';
import {
  userAtom,
  accessTokenAtom,
  refreshTokenAtom,
  isAuthenticatedAtom,
  isLoadingAuthAtom,
} from '../atoms/authAtoms';

const AuthContext = createContext(null);

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useAtom(userAtom);
  const [accessToken, setAccessToken] = useAtom(accessTokenAtom);
  const [, setRefreshToken] = useAtom(refreshTokenAtom);
  const [isAuthenticated] = useAtom(isAuthenticatedAtom);
  const [isLoading, setIsLoading] = useAtom(isLoadingAuthAtom);

  // Sync jotai state with localStorage on initial load
  useEffect(() => {
    const token = authService.getAccessToken();
    if (token) {
      try {
        const decodedUser = jwtDecode(token);
        if (decodedUser.exp * 1000 > Date.now()) {
          // atomWithStorage should handle this, but we can be explicit
          setAccessToken(token);
          setRefreshToken(authService.getRefreshToken());
          setUser(decodedUser);
        } else {
          // Token is expired. Clear state.
          authService.logout(false);
          setAccessToken(null);
          setRefreshToken(null);
          setUser(null);
        }
      } catch (e) {
        console.error("Invalid token on app load.", e);
        authService.logout(false);
        setAccessToken(null);
        setRefreshToken(null);
        setUser(null);
      }
    }
    setIsLoading(false);
  }, [setAccessToken, setRefreshToken, setUser, setIsLoading]);

  const login = async (username, password) => {
    const result = await authService.login(username, password);
    if (result.success) {
      // Update jotai atoms after successful login
      setAccessToken(authService.getAccessToken());
      setRefreshToken(authService.getRefreshToken());
      setUser(result.user);
      // Explicitly set the header on the client for immediate use
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${authService.getAccessToken()}`;
      return { success: true, user: result.user };
    } else {
      // The LoginPage will handle showing the error message.
      return { success: false, error: result.error };
    }
  };

  const logout = useCallback(async (options = {}) => {
    const { showInfoToast = true } = options;
    await authService.logout(true); // true to notify backend

    // Clear jotai atoms
    setAccessToken(null); // This will trigger isAuthenticatedAtom to be false
    setRefreshToken(null); // This will clear the refresh token
    setUser(null); // This will clear user data

    // Also remove the default header from the client
    delete apiClient.defaults.headers.common['Authorization'];

    if (showInfoToast) {
      toast.info("You have been logged out.");
    }
  }, [setAccessToken, setRefreshToken, setUser]);

  // Listen for unrecoverable auth errors from the API interceptor
  useEffect(() => {
    const handleAuthError = () => {
      // Check if a token exists. This prevents running logout if the user is already logged out
      // and some background process fails.
      if (authService.getAccessToken()) {
        toast.error("Your session has expired. Please log in again.");
        logout({ showInfoToast: false });
      }
    };

    window.addEventListener('auth-error', handleAuthError);
    return () => window.removeEventListener('auth-error', handleAuthError);
  }, [logout]);

  const value = {
    user,
    isAuthenticated,
    isLoadingAuth: isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
