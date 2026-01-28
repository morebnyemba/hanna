import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import Cookies from 'js-cookie';
import { resetAuthErrorFlag } from '@/app/lib/apiClient';

interface User {
  username: string;
  email?: string;
  role: 'admin' | 'client' | 'manufacturer' | 'technician' | 'retailer' | 'retailer_branch' | null;
}

interface SelectedRetailer {
  id: number;
  company_name: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  selectedRetailer: SelectedRetailer | null;
  hasHydrated?: boolean;
  login: (tokens: { access: string; refresh: string }, userData: { username: string; email: string; role: any }, retailer?: SelectedRetailer | null) => void;
  logout: () => void;
  setTokens: (tokens: { access: string; refresh: string }) => void;
  setSelectedRetailer: (retailer: SelectedRetailer | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      selectedRetailer: null,
      hasHydrated: false,
      login: (tokens, userData, retailer = null) => {
        set({
          accessToken: tokens.access,
          refreshToken: tokens.refresh,
          user: userData,
          selectedRetailer: retailer,
        });
        // Manually set a cookie for the middleware to read on server-side requests.
        // The middleware cannot access localStorage, but it can access cookies.
        const cookieState = { state: { accessToken: tokens.access } };
        Cookies.set('auth-storage', JSON.stringify(cookieState), { expires: 7, path: '/' });
        // Reset auth error flag on successful login
        resetAuthErrorFlag();
      },
      logout: () => {
        set({
        accessToken: null,
        refreshToken: null,
        user: null,
        selectedRetailer: null,
      });
        // Also remove the cookie on logout.
        Cookies.remove('auth-storage', { path: '/' });
      },
      setTokens: (tokens) => set({
        accessToken: tokens.access,
        refreshToken: tokens.refresh,
      }),
      setSelectedRetailer: (retailer) => set({
        selectedRetailer: retailer,
      }),
    }),
    {
      name: 'auth-storage', // name of the item in storage (must be unique)
      storage: createJSONStorage(() => localStorage), // use localStorage
      onRehydrateStorage: () => (state, error) => {
        // Mark store as hydrated so UI can wait before redirecting
        useAuthStore.setState({ hasHydrated: true });
      },
    }
  )
);

export const loginAction = async (username: string, password: string, selectedRetailer?: { id: number; company_name: string } | null) => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
  const response = await fetch(`${apiUrl}/crm-api/auth/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
    credentials: 'include', // Required for CORS requests with cookies
  });

  if (!response.ok) throw new Error('Login failed. Please check your credentials.');
  
  const data = await response.json();
  // The backend now returns 'role', 'username', 'email', 'access', 'refresh'
  useAuthStore.getState().login(
    { access: data.access, refresh: data.refresh }, 
    { username: data.username, email: data.email, role: data.role },
    selectedRetailer || null
  );

  // Return the data so the login page can use the role for redirection
  return data;
};
