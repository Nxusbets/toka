import { create } from 'zustand';
import type { User, AuthTokens, LoginCredentials, RegisterCredentials } from '../types';
import { authApi } from '../services/api';

interface AuthStore {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
  checkAuth: () => boolean;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  tokens: JSON.parse(localStorage.getItem('auth-tokens') || 'null'),
  isAuthenticated: !!localStorage.getItem('auth-tokens'),

  login: async (credentials) => {
    const res = await authApi.login(credentials);
    const tokens = res.data;
    localStorage.setItem('auth-tokens', JSON.stringify(tokens));
    set({ tokens, isAuthenticated: true });
    try {
      const payload = JSON.parse(atob(tokens.access_token.split('.')[1]));
      set({
        user: {
          id: payload.sub || payload.user_id || '',
          email: payload.email || credentials.email,
          username: payload.username || '',
          is_active: true,
          created_at: '',
          updated_at: '',
        },
      });
    } catch {
      // JWT decode best-effort; user info can be fetched separately
    }
  },

  register: async (credentials) => {
    const res = await authApi.register(credentials);
    const tokens = res.data;
    localStorage.setItem('auth-tokens', JSON.stringify(tokens));
    set({ tokens, isAuthenticated: true });
    try {
      const payload = JSON.parse(atob(tokens.access_token.split('.')[1]));
      set({
        user: {
          id: payload.sub || payload.user_id || '',
          email: payload.email || credentials.email,
          username: payload.username || credentials.username,
          is_active: true,
          created_at: '',
          updated_at: '',
        },
      });
    } catch {
      // JWT decode best-effort
    }
  },

  logout: () => {
    localStorage.removeItem('auth-tokens');
    set({ user: null, tokens: null, isAuthenticated: false });
  },

  checkAuth: () => {
    const tokens = localStorage.getItem('auth-tokens');
    if (!tokens) {
      set({ user: null, tokens: null, isAuthenticated: false });
      return false;
    }
    try {
      const parsed = JSON.parse(tokens);
      set({ tokens: parsed, isAuthenticated: true });
      return true;
    } catch {
      set({ user: null, tokens: null, isAuthenticated: false });
      return false;
    }
  },
}));
