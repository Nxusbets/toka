import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.hoisted(() => {
  const store: Record<string, string> = {};
  const mockStorage: Storage = {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { Object.keys(store).forEach((k) => delete store[k]); },
    get length() { return Object.keys(store).length; },
    key: (index: number) => Object.keys(store)[index] ?? null,
  };
  globalThis.localStorage = mockStorage;
});

vi.mock('../../src/services/api', () => ({
  authApi: {
    login: vi.fn(),
    refresh: vi.fn(),
  },
}));

import { useAuthStore } from '../../src/stores/authStore';

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({ user: null, tokens: null, isAuthenticated: false });
  });

  it('initial state is not authenticated', () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.tokens).toBeNull();
  });

  it('login() stores tokens and sets isAuthenticated', async () => {
    const tokens = {
      access_token: 'access123',
      refresh_token: 'refresh123',
      token_type: 'bearer',
    };
    const { authApi } = await import('../../src/services/api');
    vi.mocked(authApi.login).mockResolvedValue({ data: tokens } as any);

    await useAuthStore.getState().login({ email: 'test@test.com', password: 'pass' });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.tokens).toEqual(tokens);
  });

  it('logout() clears tokens and sets isAuthenticated to false', () => {
    useAuthStore.setState({
      isAuthenticated: true,
      tokens: { access_token: 'a', refresh_token: 'b', token_type: 'bearer' },
      user: { id: '1', email: 'a@a.com', username: 'a', is_active: true, created_at: '', updated_at: '' },
    });

    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.tokens).toBeNull();
    expect(state.user).toBeNull();
  });

  it('checkAuth() returns false when no tokens', () => {
    const result = useAuthStore.getState().checkAuth();
    expect(result).toBe(false);
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it('checkAuth() returns true when tokens exist in localStorage', () => {
    localStorage.setItem('auth-tokens', JSON.stringify({
      access_token: 'a', refresh_token: 'b', token_type: 'bearer',
    }));
    useAuthStore.setState({ tokens: null, isAuthenticated: false });

    const result = useAuthStore.getState().checkAuth();
    expect(result).toBe(true);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });
});
