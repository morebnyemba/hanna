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
  const [, setAccessToken] = useAtom(accessTokenAtom); // We only need the setter here, which resolves the ESLint warning.
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
          // Explicitly set the header on the client for any subsequent requests on this session.
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
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
      // Defensive check: Ensure a refresh token was stored. If not, the session
      // is not truly established and will fail on the first token expiry.
      const refreshToken = authService.getRefreshToken();
      // A more robust check to handle cases where localStorage might store the string "undefined"
      if (!refreshToken || refreshToken === 'undefined') {
        console.error("Login succeeded but no valid refresh token was provided or stored. Automatic session refresh will fail.");
        // Clear any partial login state to be safe.
        await logout({ showInfoToast: false });
        // Return a clear error to the login page.
        return { success: false, error: "Login failed due to a server configuration issue. Please contact support." };
      }

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
    // The authService.logout function internally handles potential server errors
    // (like 404 or 401) and does not throw, so a try/catch here is not needed.
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
    isAuthenticated,
    isLoadingAuth: isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
