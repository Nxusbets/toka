import { create } from 'zustand';
import type { AuditLog } from '../types';
import { auditApi } from '../services/api';

interface AuditStore {
  logs: AuditLog[];
  total: number;
  loading: boolean;
  error: string | null;
  fetchLogs: (params?: {
    page?: number;
    size?: number;
    event_type?: string;
    start_date?: string;
    end_date?: string;
  }) => Promise<void>;
}

export const useAuditStore = create<AuditStore>((set) => ({
  logs: [],
  total: 0,
  loading: false,
  error: null,

  fetchLogs: async (params = {}) => {
    set({ loading: true, error: null });
    try {
      const res = await auditApi.list({ page: 1, size: 5, ...params });
      set({ logs: res.data.items || [], total: res.data.total || 0, loading: false });
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to fetch audit logs';
      set({ error: msg, loading: false });
    }
  },
}));
