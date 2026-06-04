import axios from 'axios';
import type {
  User, Role, Permission, AuditLog,
  AIQueryRequest, AIQueryResponse,
  PaginatedResponse, LoginCredentials, RegisterCredentials, AuthTokens,
} from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
});

api.interceptors.request.use((config) => {
  const tokens = localStorage.getItem('auth-tokens');
  if (tokens) {
    const parsed: AuthTokens = JSON.parse(tokens);
    config.headers.Authorization = `Bearer ${parsed.access_token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve(token!);
  });
  failedQueue = [];
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }
      originalRequest._retry = true;
      isRefreshing = true;
      try {
        const tokens: AuthTokens = JSON.parse(
          localStorage.getItem('auth-tokens') || '{}',
        );
        const res = await axios.post(
          `${api.defaults.baseURL}/auth/refresh`,
          { refresh_token: tokens.refresh_token },
        );
        const newTokens: AuthTokens = res.data;
        localStorage.setItem('auth-tokens', JSON.stringify(newTokens));
        processQueue(null, newTokens.access_token);
        originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`;
        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        localStorage.removeItem('auth-tokens');
        window.location.href = '/';
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  },
);

export const authApi = {
  login: (credentials: LoginCredentials) =>
    api.post<AuthTokens>('/auth/login', credentials),
  register: (credentials: RegisterCredentials) =>
    api.post<AuthTokens>('/auth/register', credentials),
  refresh: (refreshToken: string) =>
    api.post<AuthTokens>('/auth/refresh', { refresh_token: refreshToken }),
};

export const usersApi = {
  list: (params?: { page?: number; size?: number; search?: string }) =>
    api.get<PaginatedResponse<User>>('/users', { params }),
  get: (id: string) => api.get<User>(`/users/${id}`),
  create: (data: Partial<User> & { password?: string; role_ids?: string[] }) =>
    api.post<User>('/users', data),
  update: (id: string, data: Partial<User>) =>
    api.put<User>(`/users/${id}`, data),
  delete: (id: string) => api.delete(`/users/${id}`),
  assignRole: (userId: string, roleId: string) =>
    api.post<User>(`/users/${userId}/roles`, { role_id: roleId }),
  removeRole: (userId: string, roleId: string) =>
    api.delete(`/users/${userId}/roles/${roleId}`),
};

export const rolesApi = {
  list: (params?: { page?: number; size?: number }) =>
    api.get<PaginatedResponse<Role>>('/roles', { params }),
  get: (id: string) => api.get<Role>(`/roles/${id}`),
  create: (data: Partial<Role>) => api.post<Role>('/roles', data),
  update: (id: string, data: Partial<Role>) =>
    api.put<Role>(`/roles/${id}`, data),
  delete: (id: string) => api.delete(`/roles/${id}`),
  listPermissions: () => api.get<Permission[]>('/roles/permissions'),
};

export const auditApi = {
  list: (params?: {
    page?: number;
    size?: number;
    event_type?: string;
    start_date?: string;
    end_date?: string;
  }) => {
    const query: Record<string, string | number> = {};
    if (params) {
      if (params.page) query.skip = ((params.page || 1) - 1) * (params.size || 20);
      if (params.size) query.limit = params.size;
      if (params.event_type) query.event_type = params.event_type;
      if (params.start_date) query.from_date = params.start_date;
      if (params.end_date) query.to_date = params.end_date;
    }
    return api.get<any>('/audit/logs', { params: query });
  },
};

export const aiApi = {
  query: (data: AIQueryRequest) =>
    api.post<AIQueryResponse>('/ai/query', data),
  ingest: (documents: Array<{ content: string; metadata?: Record<string, unknown> }>) =>
    api.post('/ai/ingest', { documents }),
};

export default api;
