import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { AuthProvider, useAuth } from "../context/AuthContext";
import { ProtectedRoute } from "../components/common/ProtectedRoute";
import { apiClient, setAuthToken, getAuthToken, clearAuthToken } from "../services/apiClient";
import { UserIdentity } from "../types/auth";

// Mock child components
const MockLoginPage = () => <div>Login Page View</div>;
const MockDashboardPage = () => <div>Operations Dashboard View</div>;
const MockAdminPage = () => <div>Admin User Management View</div>;
const MockChangePasswordPage = () => <div>Change Password View</div>;

const setupApp = (initialRoute = "/acc/dashboard", allowedRoles?: any[]) => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <AuthProvider>
        <Routes>
          <Route path="/acc/login" element={<MockLoginPage />} />
          <Route path="/acc/change-password" element={<MockChangePasswordPage />} />
          
          <Route element={<ProtectedRoute />}>
            <Route path="/acc/dashboard" element={<MockDashboardPage />} />
          </Route>

          <Route element={<ProtectedRoute allowedRoles={allowedRoles || ["SUPER_ADMIN", "ADMIN"]} />}>
            <Route path="/acc/admin/users" element={<MockAdminPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
};

describe("Phase 6: Frontend Authentication Architecture Suite", () => {
  beforeEach(() => {
    sessionStorage.clear();
    clearAuthToken();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    sessionStorage.clear();
    clearAuthToken();
    vi.restoreAllMocks();
  });

  it("1. Unauthenticated user cannot access protected route and is redirected to /acc/login", async () => {
    // No token set
    setupApp("/acc/dashboard");

    await waitFor(() => {
      expect(screen.getByText("Login Page View")).toBeInTheDocument();
    });
    expect(screen.queryByText("Operations Dashboard View")).not.toBeInTheDocument();
  });

  it("2. Authenticated user with normal status can access protected route", async () => {
    const mockUser: UserIdentity = {
      id: "usr-01",
      username: "operator01",
      email: "op@acc.in",
      full_name: "Test Operator",
      roles: ["PLANT_OPERATOR"],
      account_status: "ACTIVE",
      password_status: "NORMAL",
      must_change_password: false,
    };

    setAuthToken("fake-jwt-token");
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    setupApp("/acc/dashboard");

    await waitFor(() => {
      expect(screen.getByText("Operations Dashboard View")).toBeInTheDocument();
    });
  });

  it("3. Forced-password-change user (must_change_password=true) is restricted and redirected to /acc/change-password", async () => {
    const mockUser: UserIdentity = {
      id: "usr-02",
      username: "newuser",
      email: "new@acc.in",
      full_name: "New User",
      roles: ["PLANT_OPERATOR"],
      account_status: "ACTIVE",
      password_status: "CHANGE_REQUIRED",
      must_change_password: true,
    };

    setAuthToken("temp-jwt-token");
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    setupApp("/acc/dashboard");

    await waitFor(() => {
      expect(screen.getByText("Change Password View")).toBeInTheDocument();
    });
    expect(screen.queryByText("Operations Dashboard View")).not.toBeInTheDocument();
  });

  it("4. Admin route blocks non-admin role with Enterprise AccessDenied (403)", async () => {
    const mockUser: UserIdentity = {
      id: "usr-03",
      username: "labtech01",
      email: "lab@acc.in",
      full_name: "Lab Tech",
      roles: ["LAB_TECHNICIAN"],
      account_status: "ACTIVE",
      password_status: "NORMAL",
      must_change_password: false,
    };

    setAuthToken("lab-token");
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    setupApp("/acc/admin/users", ["SUPER_ADMIN", "ADMIN"]);

    await waitFor(() => {
      expect(screen.getByText("Access Restricted (403 Forbidden)")).toBeInTheDocument();
    });
    expect(screen.queryByText("Admin User Management View")).not.toBeInTheDocument();
    expect(screen.getByText(/Required Role\(s\):/i)).toBeInTheDocument();
  });

  it("5. Admin / Super Admin can successfully access admin routes", async () => {
    const mockUser: UserIdentity = {
      id: "usr-04",
      username: "admin01",
      email: "admin@acc.in",
      full_name: "System Admin",
      roles: ["ADMIN"],
      account_status: "ACTIVE",
      password_status: "NORMAL",
      must_change_password: false,
    };

    setAuthToken("admin-token");
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    setupApp("/acc/admin/users", ["SUPER_ADMIN", "ADMIN"]);

    await waitFor(() => {
      expect(screen.getByText("Admin User Management View")).toBeInTheDocument();
    });
  });

  it("6. 401 response triggers session invalidation and clears auth state", async () => {
    setAuthToken("expired-token");

    // Simulate 401 rejection on token verification
    vi.spyOn(apiClient, "get").mockRejectedValue({ status: 401, message: "Token expired" });

    setupApp("/acc/dashboard");

    await waitFor(() => {
      expect(screen.getByText("Login Page View")).toBeInTheDocument();
    });
    expect(getAuthToken()).toBeNull();
  });

  it("7. 403 Forbidden is handled cleanly without terminating session", async () => {
    const mockUser: UserIdentity = {
      id: "usr-05",
      username: "viewer",
      email: "viewer@acc.in",
      full_name: "Analyst Viewer",
      roles: ["ANALYST_VIEWER"],
      account_status: "ACTIVE",
      password_status: "NORMAL",
      must_change_password: false,
    };

    setAuthToken("viewer-token");
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    setupApp("/acc/admin/users", ["SUPER_ADMIN", "ADMIN"]);

    await waitFor(() => {
      expect(screen.getByText("Access Restricted (403 Forbidden)")).toBeInTheDocument();
    });
    // Ensure token is still present (not logged out)
    expect(getAuthToken()).toBe("viewer-token");
  });

  it("8. logout() clears token and user state deterministically", async () => {
    let authContextRef: any = null;

    const TestComponent = () => {
      const auth = useAuth();
      authContextRef = auth;
      return <div>Auth Component: {auth.isAuthenticated ? "LOGGED_IN" : "LOGGED_OUT"}</div>;
    };

    const mockUser: UserIdentity = {
      id: "usr-06",
      username: "op1",
      email: "op1@acc.in",
      full_name: "Op One",
      roles: ["PLANT_OPERATOR"],
      account_status: "ACTIVE",
      password_status: "NORMAL",
      must_change_password: false,
    };

    setAuthToken("active-token");
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);
    vi.spyOn(apiClient, "post").mockResolvedValue({ status: "success" });

    render(
      <MemoryRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Auth Component: LOGGED_IN")).toBeInTheDocument();
    });

    // Call logout
    await authContextRef.logout();

    await waitFor(() => {
      expect(screen.getByText("Auth Component: LOGGED_OUT")).toBeInTheDocument();
    });
    expect(getAuthToken()).toBeNull();
  });

  it("9. Session bootstrap loads current user from /api/v1/auth/me", async () => {
    const mockUser: UserIdentity = {
      id: "usr-07",
      username: "quality_head_1",
      email: "qh@acc.in",
      full_name: "Quality Head 1",
      roles: ["QUALITY_HEAD"],
      account_status: "ACTIVE",
      password_status: "NORMAL",
      must_change_password: false,
    };

    setAuthToken("qh-token");
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    setupApp("/acc/dashboard");

    await waitFor(() => {
      expect(getSpy).toHaveBeenCalledWith("/auth/me");
      expect(screen.getByText("Operations Dashboard View")).toBeInTheDocument();
    });
  });

  it("10. Role state is backend-derived and authoritative", async () => {
    const TestComponent = () => {
      const auth = useAuth();
      return (
        <div>
          <span>Roles: {auth.roles.join(",")}</span>
          <span>IsAdmin: {auth.isAdmin ? "YES" : "NO"}</span>
          <span>IsSuperAdmin: {auth.isSuperAdmin ? "YES" : "NO"}</span>
        </div>
      );
    };

    const mockUser: UserIdentity = {
      id: "usr-08",
      username: "admin_user",
      email: "admin@acc.in",
      full_name: "Admin User",
      roles: ["ADMIN"],
      account_status: "ACTIVE",
      password_status: "NORMAL",
      must_change_password: false,
    };

    setAuthToken("admin-jwt");
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    render(
      <MemoryRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Roles: ADMIN")).toBeInTheDocument();
      expect(screen.getByText("IsAdmin: YES")).toBeInTheDocument();
      expect(screen.getByText("IsSuperAdmin: NO")).toBeInTheDocument();
    });
  });

  it("11. No authentication bypass via direct route navigation", async () => {
    clearAuthToken();
    vi.spyOn(apiClient, "get").mockRejectedValue(new Error("No token"));

    setupApp("/acc/admin/users");

    await waitFor(() => {
      expect(screen.getByText("Login Page View")).toBeInTheDocument();
    });
    expect(screen.queryByText("Admin User Management View")).not.toBeInTheDocument();
  });

  it("12. Startup/refresh behavior is deterministic with token validation", async () => {
    setAuthToken("valid-refresh-token");
    const mockUser: UserIdentity = {
      id: "usr-09",
      username: "plantop02",
      email: "plantop@acc.in",
      full_name: "Plant Operator 02",
      roles: ["PLANT_OPERATOR"],
      account_status: "ACTIVE",
      password_status: "NORMAL",
      must_change_password: false,
    };
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    const { unmount } = setupApp("/acc/dashboard");

    await waitFor(() => {
      expect(screen.getByText("Operations Dashboard View")).toBeInTheDocument();
    });

    unmount();

    // Reset spy for remount
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    // Simulate page refresh (remount with same storage)
    setupApp("/acc/dashboard");
    await waitFor(() => {
      expect(screen.getByText("Operations Dashboard View")).toBeInTheDocument();
    });
  });
});
