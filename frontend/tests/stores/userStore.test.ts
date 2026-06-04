import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useUserStore } from '../../src/stores/userStore';
import { usersApi } from '../../src/services/api';

vi.mock('../../src/services/api', () => ({
  usersApi: {
    list: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

describe('userStore', () => {
  beforeEach(() => {
    useUserStore.setState({
      users: [],
      total: 0,
      loading: false,
      error: null,
    });
  });

  it('has initial state', () => {
    const state = useUserStore.getState();
    expect(state.users).toEqual([]);
    expect(state.total).toBe(0);
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('sets loading true during fetchUsers', async () => {
    vi.mocked(usersApi.list).mockImplementation(
      () => new Promise(() => {}),
    );

    useUserStore.getState().fetchUsers();
    expect(useUserStore.getState().loading).toBe(true);
  });

  it('sets users and total on successful fetch', async () => {
    const items = [{ id: '1', email: 'a@a.com', username: 'a', is_active: true, created_at: '', updated_at: '' }];
    vi.mocked(usersApi.list).mockResolvedValue({
      data: { items, total: 1, page: 1, size: 20, pages: 1 },
    } as any);

    await useUserStore.getState().fetchUsers();

    const state = useUserStore.getState();
    expect(state.users).toEqual(items);
    expect(state.total).toBe(1);
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('sets error on failed fetch', async () => {
    vi.mocked(usersApi.list).mockRejectedValue({
      response: { data: { detail: 'Server error' } },
    });

    await useUserStore.getState().fetchUsers();

    const state = useUserStore.getState();
    expect(state.error).toBe('Server error');
    expect(state.loading).toBe(false);
  });
});
