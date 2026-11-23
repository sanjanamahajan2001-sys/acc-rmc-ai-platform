/**
 * Authoritative Authentication & Session Context for ACC RMC Platform.
 *
 * Implements:
 * 1. Single authoritative frontend authentication state.
 * 2. Backend-authoritative user bootstrap on startup (/api/v1/auth/me).
 * 3. Secure login (/api/v1/auth/login) & logout (/api/v1/auth/logout).
 * 4. Forced password change state management (/api/v1/auth/change-password).
 * 5. Automatic 401 session revocation listener.
 * 6. Non-bypassable 6-role helper functions (SUPER_ADMIN full capability).
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import {
  CanonicalRole,
  UserIdentity,
  LoginResponsePayload,
  ChangePasswordPayload,
  ChangePasswordResponse,
} from "../types/auth";
import { apiClient, getAuthToken, setAuthToken, clearAuthToken, onUnauthorized, ApiError } from "../services/apiClient";

export interface AuthContextType {
  user: UserIdentity | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  mustChangePassword: boolean;
  error: string | null;
  roles: CanonicalRole[];
  login: (usernameOrEmail: string, password: string) => Promise<LoginResponsePayload>;
  logout: () => Promise<void>;
  changePassword: (payload: ChangePasswordPayload) => Promise<ChangePasswordResponse>;
  refreshSession: () => Promise<UserIdentity | null>;
  clearError: () => void;
  // RBAC Capability Helpers
  hasRole: (role: CanonicalRole) => boolean;
  hasAnyRole: (allowedRoles: CanonicalRole[]) => boolean;
  isSuperAdmin: boolean;
  isAdmin: boolean;
  isQualityHead: boolean;
  isLabTech: boolean;
  isPlantOperator: boolean;
  isAnalyst: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserIdentity | null>(null);
  const [token, setTokenState] = useState<string | null>(() => getAuthToken());
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [mustChangePassword, setMustChangePassword] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  /**
   * Authoritative Current-User Bootstrap.
   * Calls GET /api/v1/auth/me to inspect live database session state.
   */
  const refreshSession = useCallback(async (): Promise<UserIdentity | null> => {
    const activeToken = getAuthToken();
    if (!activeToken) {
      setUser(null);
      setIsAuthenticated(false);
      setMustChangePassword(false);
      setIsLoading(false);
      return null;
    }

    try {
      const identity = await apiClient.get<UserIdentity>("/auth/me");
      setUser(identity);
      setIsAuthenticated(true);
      setMustChangePassword(Boolean(identity.must_change_password));
      setTokenState(activeToken);
      setError(null);
      return identity;
    } catch (err: any) {
      // Check if this is a 403 password change quarantine
      if (
        err instanceof ApiError &&
        err.status === 403 &&
        (err.message?.includes("Password change required") || err.message?.includes("must_change_password"))
      ) {
        setIsAuthenticated(true);
        setMustChangePassword(true);
        setTokenState(activeToken);
        setError(null);
        return null;
      }

      // 401 or real unauthorized
      setUser(null);
      setIsAuthenticated(false);
      setMustChangePassword(false);
      setTokenState(null);
      clearAuthToken();
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial startup bootstrap
  useEffect(() => {
    refreshSession();
  }, [refreshSession]);

  // Centralized 401 Unauthorized listener from apiClient
  useEffect(() => {
    const unsubscribe = onUnauthorized(() => {
      setUser(null);
      setTokenState(null);
      setIsAuthenticated(false);
      setMustChangePassword(false);
      setIsLoading(false);
    });
    return unsubscribe;
  }, []);

  /**
   * Login Action: POST /api/v1/auth/login
   */
  const login = async (usernameOrEmail: string, password: string): Promise<LoginResponsePayload> => {
    setIsLoading(true);
    setError(null);

    try {
      const payload = {
        username_or_email: usernameOrEmail.trim(),
        password,
      };

      const response = await apiClient.post<LoginResponsePayload>("/auth/login", payload);

      setAuthToken(response.access_token);
      setTokenState(response.access_token);
      setUser(response.user);
      setIsAuthenticated(true);
      const isMustChange = Boolean(response.must_change_password || response.user?.must_change_password);
      setMustChangePassword(isMustChange);

      return response;
    } catch (err: any) {
      let msg = "Invalid username or password. Please check your credentials.";
      if (err instanceof ApiError) {
        msg = err.message;
      }
      setError(msg);
      setIsAuthenticated(false);
      setUser(null);
      setTokenState(null);
      clearAuthToken();
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Logout Action: POST /api/v1/auth/logout
   */
  const logout = async (): Promise<void> => {
    try {
      if (getAuthToken()) {
        await apiClient.post("/auth/logout");
      }
    } catch {
      // Ignore backend errors during logout cleanup
    } finally {
      clearAuthToken();
      setTokenState(null);
      setUser(null);
      setIsAuthenticated(false);
      setMustChangePassword(false);
      setError(null);
    }
  };

  /**
   * Forced Password Change Action: POST /api/v1/auth/change-password
   */
  const changePassword = async (payload: ChangePasswordPayload): Promise<ChangePasswordResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<ChangePasswordResponse>("/auth/change-password", {
        current_password: payload.current_password,
        new_password: payload.new_password,
        confirm_new_password: payload.confirm_password,
      });

      // Successfully changed: refresh authoritative session
      setMustChangePassword(false);
      if (user) {
        setUser({ ...user, must_change_password: false, password_status: "NORMAL" });
      }

      await refreshSession();
      return response;
    } catch (err: any) {
      const msg = err instanceof ApiError ? err.message : "Failed to change password. Please check requirements.";
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // RBAC Capability Helpers (SUPER_ADMIN has universal operational access)
  const roles = user?.roles || [];

  const hasRole = useCallback(
    (role: CanonicalRole): boolean => {
      if (!user) return false;
      if (user.roles.includes("SUPER_ADMIN")) return true;
      return user.roles.includes(role);
    },
    [user]
  );

  const hasAnyRole = useCallback(
    (allowedRoles: CanonicalRole[]): boolean => {
      if (!user) return false;
      if (user.roles.includes("SUPER_ADMIN")) return true;
      return allowedRoles.some((role) => user.roles.includes(role));
    },
    [user]
  );

  const isSuperAdmin = Boolean(user?.roles.includes("SUPER_ADMIN"));
  const isAdmin = Boolean(isSuperAdmin || user?.roles.includes("ADMIN"));
  const isQualityHead = Boolean(isSuperAdmin || user?.roles.includes("QUALITY_HEAD"));
  const isLabTech = Boolean(isSuperAdmin || user?.roles.includes("LAB_TECHNICIAN"));
  const isPlantOperator = Boolean(isSuperAdmin || user?.roles.includes("PLANT_OPERATOR"));
  const isAnalyst = Boolean(isSuperAdmin || user?.roles.includes("ANALYST_VIEWER"));

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated,
        isLoading,
        mustChangePassword,
        error,
        roles,
        login,
        logout,
        changePassword,
        refreshSession,
        clearError,
        hasRole,
        hasAnyRole,
        isSuperAdmin,
        isAdmin,
        isQualityHead,
        isLabTech,
        isPlantOperator,
        isAnalyst,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
