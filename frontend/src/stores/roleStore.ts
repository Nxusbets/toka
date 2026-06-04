import { create } from 'zustand';
import type { Role } from '../types';
import { rolesApi } from '../services/api';
import toast from 'react-hot-toast';

interface RoleStore {
  roles: Role[];
  total: number;
  loading: boolean;
  error: string | null;
  fetchRoles: (page?: number, size?: number) => Promise<void>;
  createRole: (data: Partial<Role>) => Promise<void>;
  updateRole: (id: string, data: Partial<Role>) => Promise<void>;
  deleteRole: (id: string) => Promise<void>;
}

export const useRoleStore = create<RoleStore>((set, get) => ({
  roles: [],
  total: 0,
  loading: false,
  error: null,

  fetchRoles: async (page = 1, size = 20) => {
    set({ loading: true, error: null });
    try {
      const res = await rolesApi.list({ page, size });
      set({ roles: res.data.items, total: res.data.total, loading: false });
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to fetch roles';
      set({ error: msg, loading: false });
    }
  },

  createRole: async (data) => {
    try {
      await rolesApi.create(data);
      toast.success('Role created successfully');
      get().fetchRoles();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to create role';
      toast.error(msg);
      throw err;
    }
  },

  updateRole: async (id, data) => {
    try {
      await rolesApi.update(id, data);
      toast.success('Role updated successfully');
      get().fetchRoles();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to update role';
      toast.error(msg);
      throw err;
    }
  },

  deleteRole: async (id) => {
    try {
      await rolesApi.delete(id);
      toast.success('Role deleted successfully');
      get().fetchRoles();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to delete role';
      toast.error(msg);
      throw err;
    }
  },
}));
