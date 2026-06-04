export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  roles?: Role[];
}

export interface Role {
  id: string;
  name: string;
  description: string;
  is_system: boolean;
  permissions?: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  resource: string;
  action: string;
  description: string;
}

export interface AuditLog {
  id: string;
  event_type: string;
  user_id: string;
  user_email: string;
  resource: string;
  action: string;
  ip_address: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

export interface AIQueryRequest {
  query: string;
}

export interface AIQueryResponse {
  answer: string;
  latency_ms: number;
  tokens_used: number;
  cost: number;
  model: string;
  context_docs: Array<{ content: string; score: number }>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
