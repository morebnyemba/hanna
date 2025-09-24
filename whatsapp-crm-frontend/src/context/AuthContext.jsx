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
  const [isLoading, setIsLoading] = useAtom(isLoadingAuthAtom); // Use 'isLoading' everywhere for consistency

  // Sync jotai state with localStorage on initial load
  useEffect(() => {
    const token = authService.getAccessToken();
    const refreshToken = authService.getRefreshToken();
    if (token && refreshToken && token !== 'undefined' && refreshToken !== 'undefined') {
      // Defensive: Check if token is a valid JWT (should have two dots)
      if (typeof token === 'string' && token.split('.').length === 3) {
        try {
          const decodedUser = jwtDecode(token);
          if (decodedUser.exp * 1000 > Date.now()) {
            setAccessToken(token);
            setRefreshToken(refreshToken);
            setUser(decodedUser);
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          } else {
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
      } else {
        // Token is not a valid JWT, clear state
        console.error("Invalid token format on app load.");
        authService.logout(false);
        setAccessToken(null);
        setRefreshToken(null);
        setUser(null);
      }
    } else {
      // If either token is missing, clear all state
      setAccessToken(null);
      setRefreshToken(null);
      setUser(null);
    }
    setIsLoading(false);
  }, [setAccessToken, setRefreshToken, setUser, setIsLoading]);

  const login = async (username, password) => {
    const result = await authService.login(username, password);
    if (result.success) {
      // Defensive check: Ensure both tokens are present and valid
      const accessToken = authService.getAccessToken();
      const refreshToken = authService.getRefreshToken();
      if (!accessToken || !refreshToken || accessToken === 'undefined' || refreshToken === 'undefined') {
        console.error("Login succeeded but no valid access or refresh token was provided or stored. Automatic session refresh will fail.");
        await logout({ showInfoToast: false });
        return { success: false, error: "Login failed due to a server configuration issue. Please contact support." };
      }
      // Update jotai atoms and localStorage after successful login
      setAccessToken(accessToken);
      setRefreshToken(refreshToken);
      setUser(result.user);
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
      return { success: true, user: result.user };
    } else {
      return { success: false, error: result.error };
    }
  };

  const logout = useCallback(async (options = {}) => {
    const { showInfoToast = true } = options;
    await authService.logout(true); // true to notify backend
    // Clear jotai atoms and localStorage
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    // Remove the default header from the client
    delete apiClient.defaults.headers.common['Authorization'];
    if (showInfoToast) {
      toast.info("You have been logged out.");
    }
  }, [setAccessToken, setRefreshToken, setUser]);

  // Listen for unrecoverable auth errors from the API interceptor
  useEffect(() => {
    const handleAuthError = async () => {
      // Check if a token exists. This prevents running logout if the user is already logged out
      // and some background process fails.
      if (authService.getAccessToken()) {
        toast.error("Your session has expired. Please log in again.");
        try {
          // Await the logout promise to handle any potential rejections gracefully.
          await logout({ showInfoToast: false });
        } catch (e) {
          // This safeguard prevents an "uncaught promise rejection" in the console.
          console.error("A non-critical error occurred during the automated logout process:", e);
        }
      }
    };

    window.addEventListener('auth-error', handleAuthError);
    return () => window.removeEventListener('auth-error', handleAuthError);
  }, [logout]);

  const value = {
    user,
    accessToken,
    isAuthenticated,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
