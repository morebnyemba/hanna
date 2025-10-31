'use client';

import { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface AuthContextType {
  accessToken: string | null;
  user: { username: string; email: string } | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [user, setUser] = useState<{ username: string; email: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // On initial load, try to load the token from localStorage
    const token = localStorage.getItem('accessToken');
    if (token) {
      setAccessToken(token);
      // In a real app, you would also verify the token and fetch user data
      // For now, we'll just set a placeholder user if a token exists
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
    
    try {
      const response = await fetch(`${apiUrl}/crm-api/auth/token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed. Please check your credentials.');
      }

      const data = await response.json();
      
      // Store tokens and user data
      setAccessToken(data.access);
      setUser({ username: data.username, email: data.email });

      // Persist to localStorage
      localStorage.setItem('accessToken', data.access);
      localStorage.setItem('refreshToken', data.refresh);
      localStorage.setItem('user', JSON.stringify({ username: data.username, email: data.email }));

      router.push('/dashboard'); // Redirect to dashboard on successful login

    } catch (error) {
      console.error('Login error:', error);
      // Re-throw to be caught by the login form
      throw error;
    }
  };

  const logout = () => {
    // Clear state and localStorage
    setAccessToken(null);
    setUser(null);
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    router.push('/login'); // Redirect to login page
  };

  const value = {
    accessToken,
    user,
    login,
    logout,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};