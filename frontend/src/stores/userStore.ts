import { create } from 'zustand';
import type { User } from '../types';
import { usersApi } from '../services/api';
import toast from 'react-hot-toast';

interface UserStore {
  users: User[];
  total: number;
  loading: boolean;
  error: string | null;
  fetchUsers: (page?: number, size?: number, search?: string) => Promise<void>;
  updateUser: (id: string, data: Partial<User>) => Promise<void>;
  deleteUser: (id: string) => Promise<void>;
}

export const useUserStore = create<UserStore>((set, get) => ({
  users: [],
  total: 0,
  loading: false,
  error: null,

  fetchUsers: async (page = 1, size = 20, search?: string) => {
    set({ loading: true, error: null });
    try {
      const res = await usersApi.list({ page, size, search });
      set({ users: res.data.items, total: res.data.total, loading: false });
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to fetch users';
      set({ error: msg, loading: false });
    }
  },

  updateUser: async (id, data) => {
    try {
      await usersApi.update(id, data);
      toast.success('User updated successfully');
      get().fetchUsers();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to update user';
      toast.error(msg);
      throw err;
    }
  },

  deleteUser: async (id) => {
    try {
      await usersApi.delete(id);
      toast.success('User deleted successfully');
      get().fetchUsers();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to delete user';
      toast.error(msg);
      throw err;
    }
  },
}));
