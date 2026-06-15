/**
 * All API endpoint functions organized by domain.
 */

import api from './client';
import type {
  User, Group, GroupMembership, Expense, Settlement,
  GroupBalances, SimplifiedSettlements, BalanceExplanation,
  ImportJob, ImportAnomaly, LoginResponse, AuditLog,
  PaginatedResponse, Currency,
} from '../types';

// ─── Auth ────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: {
    email: string; username: string; first_name: string;
    last_name: string; password: string; password_confirm: string;
  }) => api.post('/auth/register/', data),

  login: (email: string, password: string) =>
    api.post<LoginResponse>('/auth/login/', { email, password }),

  logout: (refresh: string) =>
    api.post('/auth/logout/', { refresh }),

  refreshToken: (refresh: string) =>
    api.post('/auth/token/refresh/', { refresh }),

  verifyEmail: (token: string) =>
    api.post(`/auth/verify-email/${token}/`),

  requestPasswordReset: (email: string) =>
    api.post('/auth/password-reset/', { email }),

  confirmPasswordReset: (token: string, new_password: string, new_password_confirm: string) =>
    api.post('/auth/password-reset/confirm/', { token, new_password, new_password_confirm }),

  me: () => api.get<User>('/auth/me/'),

  updateProfile: (data: Partial<User>) =>
    api.patch<User>('/auth/me/', data),

  changePassword: (old_password: string, new_password: string, new_password_confirm: string) =>
    api.post('/auth/change-password/', { old_password, new_password, new_password_confirm }),
};

// ─── Groups ──────────────────────────────────────────────────────────────────
export const groupsApi = {
  list: () => api.get<{ count: number; results: Group[] }>('/groups/'),

  create: (data: { name: string; description?: string; default_currency?: string }) =>
    api.post<Group>('/groups/', data),

  get: (id: string) => api.get<Group>(`/groups/${id}/`),

  update: (id: string, data: Partial<Group>) =>
    api.patch<Group>(`/groups/${id}/`, data),

  delete: (id: string) => api.delete(`/groups/${id}/`),

  listMembers: (id: string) =>
    api.get<{ count: number; results: GroupMembership[] }>(`/groups/${id}/members/`),

  addMember: (id: string, user_id: string, role?: string, joined_at?: string) =>
    api.post<GroupMembership>(`/groups/${id}/members/add/`, { user_id, role, joined_at }),

  leaveGroup: (id: string, left_at?: string) =>
    api.post(`/groups/${id}/members/leave/`, { left_at }),

  removeMember: (id: string, user_id: string) =>
    api.post(`/groups/${id}/members/${user_id}/remove/`),
};

// ─── Expenses ─────────────────────────────────────────────────────────────────
export const expensesApi = {
  listByGroup: (groupId: string) =>
    api.get<{ count: number; results: Expense[] }>(`/expenses/groups/${groupId}/`),

  create: (groupId: string, data: any) =>
    api.post<Expense>(`/expenses/groups/${groupId}/`, data),

  get: (id: string) => api.get<Expense>(`/expenses/${id}/`),

  update: (id: string, data: any) =>
    api.patch<Expense>(`/expenses/${id}/`, data),

  delete: (id: string) => api.delete(`/expenses/${id}/`),
};

// ─── Settlements ──────────────────────────────────────────────────────────────
export const settlementsApi = {
  listByGroup: (groupId: string) =>
    api.get<{ count: number; results: Settlement[] }>(`/settlements/groups/${groupId}/`),

  create: (groupId: string, data: any) =>
    api.post<Settlement>(`/settlements/groups/${groupId}/`, data),

  get: (id: string) => api.get<Settlement>(`/settlements/${id}/`),

  delete: (id: string) => api.delete(`/settlements/${id}/`),
};

// ─── Balances ─────────────────────────────────────────────────────────────────
export const balancesApi = {
  groupBalances: (groupId: string) =>
    api.get<GroupBalances>(`/balances/groups/${groupId}/`),

  simplifiedSettlements: (groupId: string) =>
    api.get<SimplifiedSettlements>(`/balances/groups/${groupId}/simplified/`),

  explainBalance: (groupId: string, userId?: string) =>
    api.get<BalanceExplanation>(`/balances/groups/${groupId}/explain/`, {
      params: userId ? { user_id: userId } : {},
    }),
};

// ─── Imports ──────────────────────────────────────────────────────────────────
export const importsApi = {
  list: (groupId?: string) =>
    api.get<{ count: number; results: ImportJob[] }>('/imports/', { params: groupId ? { group_id: groupId } : {} }),

  upload: (groupId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('group_id', groupId);
    return api.post<ImportJob>('/imports/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  get: (jobId: string) => api.get<ImportJob>(`/imports/${jobId}/`),

  getAnomalies: (jobId: string, filters?: { severity?: string; status?: string }) =>
    api.get<{ count: number; results: ImportAnomaly[] }>(`/imports/${jobId}/anomalies/`, { params: filters }),

  resolveAnomaly: (jobId: string, anomalyId: string, action: 'APPROVE' | 'REJECT', action_taken?: string) =>
    api.post<ImportAnomaly>(`/imports/${jobId}/anomalies/${anomalyId}/resolve/`, {
      action, action_taken,
    }),

  execute: (jobId: string) =>
    api.post<ImportJob>(`/imports/${jobId}/execute/`),

  downloadReport: (jobId: string) =>
    api.get(`/imports/${jobId}/report/`, { responseType: 'blob' }),
};

// ─── Currencies ───────────────────────────────────────────────────────────────
export const currenciesApi = {
  list: () => api.get<{ count: number; results: Currency[] }>('/currencies/'),
};

// ─── Audit ────────────────────────────────────────────────────────────────────
export const auditApi = {
  list: (params?: { action?: string; resource_type?: string; page?: number }) =>
    api.get<PaginatedResponse<AuditLog>>('/audit/', { params }),
};

// ─── AI Assist ────────────────────────────────────────────────────────────────
export const aiApi = {
  explainBalance: (group_id: string, user_id?: string) =>
    api.post('/ai/explain-balance/', { group_id, user_id }),

  explainAnomaly: (anomaly_id: string) =>
    api.post('/ai/explain-anomaly/', { anomaly_id }),

  suggestResolution: (anomaly_id: string) =>
    api.post('/ai/suggest-resolution/', { anomaly_id }),
};
