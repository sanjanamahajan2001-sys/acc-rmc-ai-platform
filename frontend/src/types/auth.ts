/**
 * Authoritative Frontend Authentication & RBAC Domain Types.
 * Strictly aligned with backend Phase 1–5 canonical identity schemas.
 */

export type CanonicalRole =
  | "SUPER_ADMIN"
  | "ADMIN"
  | "QUALITY_HEAD"
  | "LAB_TECHNICIAN"
  | "PLANT_OPERATOR"
  | "ANALYST_VIEWER";

export const CANONICAL_ROLES: CanonicalRole[] = [
  "SUPER_ADMIN",
  "ADMIN",
  "QUALITY_HEAD",
  "LAB_TECHNICIAN",
  "PLANT_OPERATOR",
  "ANALYST_VIEWER",
];

export type AccountStatus = "ACTIVE" | "INACTIVE" | "LOCKED" | "DEACTIVATED";
export type PasswordStatus = "NORMAL" | "CHANGE_REQUIRED" | "EXPIRED";

export interface UserIdentity {
  id: string;
  username: string;
  email: string;
  full_name: string;
  roles: CanonicalRole[];
  account_status: AccountStatus;
  password_status: PasswordStatus;
  must_change_password: boolean;
  failed_login_attempts?: number;
  last_login_at?: string | null;
  session_version?: number;
  plant_code?: string;
  plant_name?: string;
  // Compatibility fields for legacy views
  name?: string;
  operator_id?: string;
}

export interface LoginRequestPayload {
  username?: string;
  email?: string;
  password: string;
}

export interface LoginResponsePayload {
  access_token: string;
  token_type: string;
  expires_in: number;
  must_change_password: boolean;
  user: UserIdentity;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface ChangePasswordResponse {
  status: string;
  message: string;
  password_status?: PasswordStatus;
}

export interface AuthState {
  user: UserIdentity | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  mustChangePassword: boolean;
  error: string | null;
  roles: CanonicalRole[];
}
