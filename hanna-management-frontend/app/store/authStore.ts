import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface User {
  username: string;
  email: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  login: (tokens: { access: string; refresh: string }, userData: User) => void;
  logout: () => void;
  setTokens: (tokens: { access: string; refresh: string }) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      login: (tokens, userData) => set({
        accessToken: tokens.access,
        refreshToken: tokens.refresh,
        user: userData,
      }),
      logout: () => set({
        accessToken: null,
        refreshToken: null,
        user: null,
      }),
      setTokens: (tokens) => set({
        accessToken: tokens.access,
        refreshToken: tokens.refresh,
      }),
    }),
    {
      name: 'auth-storage', // name of the item in storage (must be unique)
      storage: createJSONStorage(() => localStorage), // use localStorage
    }
  )
);

export const loginAction = async (username: string, password: string) => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
  const response = await fetch(`${apiUrl}/crm-api/auth/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) throw new Error('Login failed. Please check your credentials.');
  
  const data = await response.json();
  useAuthStore.getState().login({ access: data.access, refresh: data.refresh }, { username: data.username, email: data.email });
};
