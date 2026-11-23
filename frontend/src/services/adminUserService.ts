import { apiClient } from './apiClient';

export interface UserRole {
  id: string;
  name: string;
  description?: string;
}

export interface UserSummaryItem {
  id: string;
  username: string;
  email: string;
  full_name: string;
  account_status: string;
  password_status: string;
  must_change_password: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
  version: number;
  roles: string[];
}

export interface UserDetailDTO {
  id: string;
  username: string;
  email: string;
  full_name: string;
  account_status: string;
  password_status: string;
  must_change_password: boolean;
  failed_login_attempts?: number;
  last_login_at: string | null;
  last_password_change_at?: string | null;
  created_at: string;
  updated_at: string;
  version: number;
  roles: string[];
}

export interface AdminUserMetrics {
  total_users: number;
  active_users: number;
  administrators: number;
  password_pending: number;
}

export interface AdminUserListResponse {
  items: UserSummaryItem[];
  total: number;
  page: number;
  page_size: number;
  metrics: AdminUserMetrics;
}

export interface GetUsersParams {
  q?: string;
  account_status?: string;
  role_id?: string;
  page?: number;
  page_size?: number;
}

export interface UserAdminCreateRequestDTO {
  username: string;
  email: string;
  full_name: string;
  roles: string[];
}

export interface UserAdminCreateResponseDTO {
  user: UserSummaryItem;
  temporary_password: string;
  expires_at: string;
  message: string;
}

export interface PasswordResetResponseDTO {
  user_id: string;
  username: string;
  temporary_password: string;
  expires_at: string;
  message?: string;
}

export interface MessageResponseDTO {
  message: string;
}

export const adminUserService = {
  async getUsers(params: GetUsersParams = {}): Promise<AdminUserListResponse> {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.account_status) query.append('account_status', params.account_status);
    if (params.role_id) query.append('role_id', params.role_id);
    if (params.page) query.append('page', String(params.page));
    if (params.page_size) query.append('page_size', String(params.page_size));

    const res = await apiClient.get<AdminUserListResponse>(`/admin/users?${query.toString()}`);
    return res;
  },

  async getUserById(userId: string): Promise<UserDetailDTO> {
    const res = await apiClient.get<UserDetailDTO>(`/admin/users/${userId}`);
    return res;
  },

  async createUser(payload: UserAdminCreateRequestDTO): Promise<UserAdminCreateResponseDTO> {
    const res = await apiClient.post<UserAdminCreateResponseDTO>('/admin/users', payload);
    return res;
  },

  async resetPassword(userId: string): Promise<PasswordResetResponseDTO> {
    const res = await apiClient.post<PasswordResetResponseDTO>(`/admin/users/${userId}/reset-password`);
    return res;
  },

  async activateUser(userId: string): Promise<UserDetailDTO> {
    const res = await apiClient.post<UserDetailDTO>(`/admin/users/${userId}/activate`);
    return res;
  },

  async deactivateUser(userId: string): Promise<UserDetailDTO> {
    const res = await apiClient.post<UserDetailDTO>(`/admin/users/${userId}/deactivate`);
    return res;
  },

  async deleteUser(userId: string): Promise<MessageResponseDTO> {
    const res = await apiClient.delete<MessageResponseDTO>(`/admin/users/${userId}`);
    return res;
  }
};
