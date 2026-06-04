import { create } from 'zustand';
import type { AIQueryResponse } from '../types';
import { aiApi } from '../services/api';

interface HistoryEntry {
  query: string;
  response: string;
  timestamp: string;
  metadata?: {
    latency_ms: number;
    total_tokens: number;
    estimated_cost: number;
    context_chunks: number;
  };
}

interface AIStore {
  query: (text: string) => Promise<AIQueryResponse | null>;
  history: HistoryEntry[];
  loading: boolean;
  error: string | null;
}

export const useAIStore = create<AIStore>((set) => ({
  history: [],
  loading: false,
  error: null,

  query: async (text) => {
    set({ loading: true, error: null });
    try {
      const res = await aiApi.query({ query: text });
      const data: AIQueryResponse = res.data;
      const entry: HistoryEntry = {
        query: text,
        response: data.answer,
        timestamp: new Date().toISOString(),
        metadata: {
          latency_ms: data.latency_ms,
          total_tokens: data.tokens_used,
          estimated_cost: data.cost,
          context_chunks: data.context_docs?.length || 0,
        },
      };
      set((state) => ({
        history: [...state.history, entry],
        loading: false,
      }));
      return data;
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to get AI response';
      set({ error: msg, loading: false });
      return null;
    }
  },
}));
