import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "../context/AuthContext";
import { LoginPage } from "../pages/LoginPage";
import { ChangePasswordPage } from "../pages/ChangePasswordPage";
import { ProtectedRoute } from "../components/common/ProtectedRoute";
import { apiClient, setAuthToken, clearAuthToken, ApiError } from "../services/apiClient";
import { UserIdentity } from "../types/auth";

describe("Phase 7: Login & Forced Password Change UI Suite", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearAuthToken();
    sessionStorage.clear();
  });

  const renderLogin = (initialRoute = "/acc/login") => {
    return render(
      <MemoryRouter initialEntries={[initialRoute]}>
        <AuthProvider>
          <Routes>
            <Route path="/acc/login" element={<LoginPage />} />
            <Route
              path="/acc/dashboard"
              element={
                <ProtectedRoute>
                  <div>Operations Dashboard View</div>
                </ProtectedRoute>
              }
            />
            <Route
              path="/acc/change-password"
              element={
                <ProtectedRoute requireForcedPasswordChange={true}>
                  <ChangePasswordPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );
  };

  it("1. Login form renders brand identity, inputs, show/hide button and sign in button", () => {
    const { container } = renderLogin();

    expect(screen.getByText("ACC Concrete Operations")).toBeInTheDocument();
    expect(container.querySelector("#login-username")).toBeInTheDocument();
    expect(container.querySelector("#login-password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sign In to Operations Console/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Show password/i })).toBeInTheDocument();
  });

  it("2. Password visibility toggle switches input type between password and text", () => {
    const { container } = renderLogin();

    const passwordInput = container.querySelector("#login-password") as HTMLInputElement;
    const toggleButton = screen.getByRole("button", { name: /Show password/i });

    expect(passwordInput.type).toBe("password");

    fireEvent.click(toggleButton);
    expect(passwordInput.type).toBe("text");
    expect(screen.getByRole("button", { name: /Hide password/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Hide password/i }));
    expect(passwordInput.type).toBe("password");
  });

  it("3. Valid login successfully authenticates and transitions to dashboard", async () => {
    const mockUser: UserIdentity = {
      id: "usr-01",
      username: "admin",
      email: "admin@acc-rmc.in",
      full_name: "Master Admin",
      roles: ["SUPER_ADMIN"],
      account_status: "ACTIVE",
      password_status: "NORMAL",
      must_change_password: false,
    };

    vi.spyOn(apiClient, "post").mockResolvedValue({
      access_token: "jwt-token-123",
      token_type: "bearer",
      expires_in: 28800,
      must_change_password: false,
      user: mockUser,
    });
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    const { container } = renderLogin();

    const usernameInput = container.querySelector("#login-username") as HTMLInputElement;
    const passwordInput = container.querySelector("#login-password") as HTMLInputElement;

    fireEvent.change(usernameInput, { target: { value: "admin" } });
    fireEvent.change(passwordInput, { target: { value: "SecPass123!" } });
    fireEvent.submit(container.querySelector("form")!);

    await waitFor(() => {
      expect(screen.getByText("Operations Dashboard View")).toBeInTheDocument();
    });
  });

  it("4. Invalid credentials renders clean enterprise error without technical stack traces", async () => {
    vi.spyOn(apiClient, "post").mockRejectedValue(
      new ApiError(401, "Invalid username or password.", "UNAUTHORIZED")
    );

    const { container } = renderLogin();

    const usernameInput = container.querySelector("#login-username") as HTMLInputElement;
    const passwordInput = container.querySelector("#login-password") as HTMLInputElement;

    fireEvent.change(usernameInput, { target: { value: "invalid_user" } });
    fireEvent.change(passwordInput, { target: { value: "WrongPass" } });
    fireEvent.submit(container.querySelector("form")!);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Invalid username or password.");
    });
    expect(screen.queryByText("Operations Dashboard View")).not.toBeInTheDocument();
  });

  it("5. Login with forced password change (must_change_password=true) redirects directly to /acc/change-password", async () => {
    const mockTempUser: UserIdentity = {
      id: "usr-02",
      username: "temp_operator",
      email: "temp@acc-rmc.in",
      full_name: "Temp Operator",
      roles: ["PLANT_OPERATOR"],
      account_status: "ACTIVE",
      password_status: "CHANGE_REQUIRED",
      must_change_password: true,
    };

    vi.spyOn(apiClient, "post").mockResolvedValue({
      access_token: "temp-jwt-token",
      token_type: "bearer",
      expires_in: 3600,
      must_change_password: true,
      user: mockTempUser,
    });
    vi.spyOn(apiClient, "get").mockResolvedValue(mockTempUser);

    const { container } = renderLogin();

    const usernameInput = container.querySelector("#login-username") as HTMLInputElement;
    const passwordInput = container.querySelector("#login-password") as HTMLInputElement;

    fireEvent.change(usernameInput, { target: { value: "temp_operator" } });
    fireEvent.change(passwordInput, { target: { value: "TempPass123!" } });
    fireEvent.submit(container.querySelector("form")!);

    await waitFor(() => {
      expect(screen.getByText("Password Setup Required")).toBeInTheDocument();
    });
  });

  it("6. Password change form validates policy criteria in real-time", async () => {
    const mockUser: UserIdentity = {
      id: "usr-02",
      username: "temp_operator",
      email: "temp@acc-rmc.in",
      full_name: "Temp Operator",
      roles: ["PLANT_OPERATOR"],
      account_status: "ACTIVE",
      password_status: "CHANGE_REQUIRED",
      must_change_password: true,
    };

    setAuthToken("temp-token");
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    const { container } = render(
      <MemoryRouter initialEntries={["/acc/change-password"]}>
        <AuthProvider>
          <Routes>
            <Route
              path="/acc/change-password"
              element={
                <ProtectedRoute requireForcedPasswordChange={true}>
                  <ChangePasswordPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Password Setup Required")).toBeInTheDocument();
    });

    const newPwInput = container.querySelector("#new-pw") as HTMLInputElement;
    const confirmPwInput = container.querySelector("#confirm-pw") as HTMLInputElement;

    // Initial criteria checklist states
    expect(screen.getByText(/At least 10 characters/i)).toHaveTextContent("•");

    // Enter partial password
    fireEvent.change(newPwInput, { target: { value: "Short1!" } });
    expect(screen.getByText(/One uppercase/i)).toHaveTextContent("✓");
    expect(screen.getByText(/One lowercase/i)).toHaveTextContent("✓");
    expect(screen.getByText(/One number/i)).toHaveTextContent("✓");
    expect(screen.getByText(/One special character/i)).toHaveTextContent("✓");
    expect(screen.getByText(/At least 10 characters/i)).toHaveTextContent("•");

    // Enter valid 10+ character password
    fireEvent.change(newPwInput, { target: { value: "SecureEnterprise2026!" } });
    expect(screen.getByText(/At least 10 characters/i)).toHaveTextContent("✓");

    // Matching confirmation
    fireEvent.change(confirmPwInput, { target: { value: "SecureEnterprise2026!" } });
    expect(screen.getByText(/Passwords match/i)).toHaveTextContent("✓");
  });

  it("7. Password change mismatch shows validation error", async () => {
    const mockUser: UserIdentity = {
      id: "usr-02",
      username: "temp_operator",
      email: "temp@acc-rmc.in",
      full_name: "Temp Operator",
      roles: ["PLANT_OPERATOR"],
      account_status: "ACTIVE",
      password_status: "CHANGE_REQUIRED",
      must_change_password: true,
    };

    setAuthToken("temp-token");
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);

    const { container } = render(
      <MemoryRouter initialEntries={["/acc/change-password"]}>
        <AuthProvider>
          <Routes>
            <Route
              path="/acc/change-password"
              element={
                <ProtectedRoute requireForcedPasswordChange={true}>
                  <ChangePasswordPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Password Setup Required")).toBeInTheDocument();
    });

    const currentPw = container.querySelector("#current-pw") as HTMLInputElement;
    const newPw = container.querySelector("#new-pw") as HTMLInputElement;
    const confirmPw = container.querySelector("#confirm-pw") as HTMLInputElement;

    fireEvent.change(currentPw, { target: { value: "OldPass123!" } });
    fireEvent.change(newPw, { target: { value: "NewSecurePass2026!" } });
    fireEvent.change(confirmPw, { target: { value: "MismatchPass2026!" } });

    const form = container.querySelector("form") as HTMLFormElement;
    fireEvent.submit(form);

    expect(screen.getByRole("alert")).toHaveTextContent("New password and confirmation do not match.");
  });

      it("8. Successful password change submits to API and redirects to /acc/dashboard", async () => {
    const mockUser: UserIdentity = {
      id: "usr-02",
      username: "temp_operator",
      email: "temp@acc-rmc.in",
      full_name: "Temp Operator",
      roles: ["PLANT_OPERATOR"],
      account_status: "ACTIVE",
      password_status: "CHANGE_REQUIRED",
      must_change_password: true,
    };

    setAuthToken("temp-token");
    let hasChanged = false;

    vi.spyOn(apiClient, "get").mockImplementation(async (url: string) => {
      if (hasChanged) {
        return { ...mockUser, must_change_password: false, password_status: "NORMAL" };
      }
      return mockUser;
    });

    const postSpy = vi.spyOn(apiClient, "post").mockImplementation(async (url: string, body?: any) => {
      if (url === "/auth/change-password") {
        hasChanged = true;
        return {
          message: "Password updated successfully.",
          access_token: "new-permanent-token",
          token_type: "bearer",
          expires_in: 28800,
          user: { ...mockUser, must_change_password: false, password_status: "NORMAL" },
        };
      }
      return {};
    });

    const { container } = render(
      <MemoryRouter initialEntries={["/acc/change-password"]}>
        <AuthProvider>
          <Routes>
            <Route
              path="/acc/change-password"
              element={
                <ProtectedRoute requireForcedPasswordChange={true}>
                  <ChangePasswordPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/acc/dashboard"
              element={
                <ProtectedRoute>
                  <div>Operations Dashboard View</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Password Setup Required")).toBeInTheDocument();
    });

    const currentPw = container.querySelector("#current-pw") as HTMLInputElement;
    const newPw = container.querySelector("#new-pw") as HTMLInputElement;
    const confirmPw = container.querySelector("#confirm-pw") as HTMLInputElement;

    fireEvent.change(currentPw, { target: { value: "OldPass123!" } });
    fireEvent.change(newPw, { target: { value: "NewSecurePass2026!" } });
    fireEvent.change(confirmPw, { target: { value: "NewSecurePass2026!" } });

    const submitBtn = screen.getByRole("button", { name: /Set Password & Proceed/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(postSpy).toHaveBeenCalledWith("/auth/change-password", {
        current_password: "OldPass123!",
        new_password: "NewSecurePass2026!",
        confirm_new_password: "NewSecurePass2026!",
      });
      expect(screen.getByText("Operations Dashboard View")).toBeInTheDocument();
    });
  });

  it("9. Sign out button on change-password page invalidates session and returns to login", async () => {
    const mockUser: UserIdentity = {
      id: "usr-02",
      username: "temp_operator",
      email: "temp@acc-rmc.in",
      full_name: "Temp Operator",
      roles: ["PLANT_OPERATOR"],
      account_status: "ACTIVE",
      password_status: "CHANGE_REQUIRED",
      must_change_password: true,
    };

    setAuthToken("temp-token");
    vi.spyOn(apiClient, "get").mockResolvedValue(mockUser);
    vi.spyOn(apiClient, "post").mockResolvedValue({ message: "Logged out" });

    render(
      <MemoryRouter initialEntries={["/acc/change-password"]}>
        <AuthProvider>
          <Routes>
            <Route path="/acc/login" element={<LoginPage />} />
            <Route
              path="/acc/change-password"
              element={
                <ProtectedRoute requireForcedPasswordChange={true}>
                  <ChangePasswordPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Password Setup Required")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /Sign Out/i }));

    await waitFor(() => {
      expect(screen.getByText("ACC Concrete Operations")).toBeInTheDocument();
    });
  });
});
