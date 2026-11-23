/**
 * ACC RMC Operations & Cement Strength AI Platform — Enterprise Login Page.
 * Route: /acc/login
 *
 * Implements:
 * - Enterprise Light Theme (#F4F6F9, #FBFCFE, #DCE2EA, #172033, #4F46E5)
 * - Corporate Username or Email authentication
 * - Show/Hide Password toggle control
 * - Loading, disabled, and enterprise validation states
 * - Seamless redirection to intended route or forced password change
 * - Zero hardcoded or mock credentials
 */

import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  enterpriseLightTokens as tokens,
  primaryButtonBase,
  formInputStyle,
  formLabelStyle,
} from "../components/manual-entry/enterpriseLightTokens";

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, user, error, clearError } = useAuth();

  const [usernameOrEmail, setUsernameOrEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const from = (location.state as any)?.from?.pathname || "/acc/dashboard";

  React.useEffect(() => {
    if (isAuthenticated && user) {
      if (user.must_change_password) {
        navigate("/acc/change-password", { replace: true });
      } else {
        navigate(from, { replace: true });
      }
    }
  }, [isAuthenticated, user, navigate, from]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!usernameOrEmail.trim()) {
      setLocalError("Please enter your corporate username or email.");
      return;
    }

    if (!password) {
      setLocalError("Please enter your account password.");
      return;
    }

    setSubmitting(true);

    try {
      const response = await login(usernameOrEmail.trim(), password);
      if (response.must_change_password || response.user?.must_change_password) {
        navigate("/acc/change-password", { replace: true });
      } else {
        navigate(from, { replace: true });
      }
    } catch (err: any) {
      setLocalError(err.message || "Invalid credentials. Please check your username and password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main
      role="main"
      style={{
        minHeight: "100vh",
        backgroundColor: tokens.pageBg,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: "24px",
        fontFamily: tokens.fontFamily,
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "420px",
          backgroundColor: tokens.surfacePrimary,
          border: `1px solid ${tokens.border}`,
          borderRadius: tokens.radius,
          boxShadow: tokens.shadowCard,
          padding: "36px 32px",
          boxSizing: "border-box",
        }}
      >
        {/* Enterprise Brand Identity */}
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: "48px",
              height: "48px",
              borderRadius: "8px",
              backgroundColor: tokens.primaryAccentLight,
              border: `1px solid ${tokens.primaryAccentBorder}`,
              fontSize: "1.4rem",
              marginBottom: "12px",
            }}
            aria-hidden="true"
          >
            🏗️
          </div>
          <h1
            style={{
              fontSize: "1.35rem",
              fontWeight: 700,
              color: tokens.textPrimary,
              margin: "0 0 6px 0",
              letterSpacing: "-0.01em",
            }}
          >
            ACC Concrete Operations
          </h1>
          <p
            style={{
              margin: 0,
              fontSize: "0.85rem",
              color: tokens.textSecondary,
              fontWeight: 400,
            }}
          >
            Cement Strength Engine & RMC Platform
          </p>
          <div
            style={{
              display: "inline-block",
              marginTop: "8px",
              backgroundColor: tokens.surfaceSecondary,
              color: tokens.textSecondary,
              fontSize: "0.72rem",
              fontWeight: 600,
              padding: "3px 8px",
              borderRadius: "4px",
              border: `1px solid ${tokens.border}`,
              letterSpacing: "0.03em",
            }}
          >
            OPERATIONS CONSOLE • SECURE SIGN IN
          </div>
        </div>

        {/* Accessible Error Alert Banner */}
        {(localError || error) && (
          <div
            role="alert"
            aria-live="assertive"
            style={{
              marginBottom: "20px",
              padding: "10px 14px",
              backgroundColor: tokens.statusErrorBg,
              border: `1px solid ${tokens.statusErrorBorder}`,
              color: tokens.statusErrorText,
              borderRadius: tokens.radius,
              fontSize: "0.82rem",
              lineHeight: 1.4,
              display: "flex",
              alignItems: "flex-start",
              gap: "8px",
            }}
          >
            <span style={{ fontSize: "1rem", lineHeight: 1 }} aria-hidden="true">
              ⚠️
            </span>
            <div style={{ flex: 1, fontWeight: 500 }}>{localError || error}</div>
          </div>
        )}

        {/* Enterprise Login Form */}
        <form onSubmit={handleSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          <div>
            <label htmlFor="login-username" style={formLabelStyle}>
              Username or Corporate Email <span style={{ color: tokens.errorRed }}>*</span>
            </label>
            <input
              id="login-username"
              type="text"
              name="username"
              value={usernameOrEmail}
              onChange={(e) => {
                setUsernameOrEmail(e.target.value);
                if (localError) setLocalError(null);
              }}
              placeholder="e.g. admin or operator@acc-rmc.in"
              autoComplete="username"
              autoFocus
              disabled={submitting}
              style={{
                ...formInputStyle,
                borderColor: localError && !usernameOrEmail ? tokens.errorRed : tokens.border,
              }}
              required
            />
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
              <label htmlFor="login-password" style={{ ...formLabelStyle, marginBottom: 0 }}>
                Password <span style={{ color: tokens.errorRed }}>*</span>
              </label>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  background: "none",
                  border: "none",
                  color: tokens.primaryAccent,
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  padding: 0,
                }}
                tabIndex={0}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
            <div style={{ position: "relative" }}>
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                name="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (localError) setLocalError(null);
                }}
                placeholder="Enter account password"
                autoComplete="current-password"
                disabled={submitting}
                style={{
                  ...formInputStyle,
                  borderColor: localError && !password ? tokens.errorRed : tokens.border,
                }}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            style={{
              ...primaryButtonBase,
              width: "100%",
              padding: "11px 18px",
              fontSize: "0.92rem",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              gap: "8px",
              cursor: submitting ? "not-allowed" : "pointer",
              opacity: submitting ? 0.75 : 1,
              marginTop: "4px",
            }}
          >
            {submitting ? "Authenticating Operator..." : "Sign In to Operations Console →"}
          </button>
        </form>
      </div>

      {/* Enterprise Security Footer */}
      <footer
        style={{
          marginTop: "24px",
          fontSize: "0.75rem",
          color: tokens.textMuted,
          textAlign: "center",
          lineHeight: 1.5,
        }}
      >
        <div>ACC Limited • Ready Mix Concrete Operations</div>
        <div style={{ fontSize: "0.7rem", marginTop: "2px" }}>
          Authorized Personnel Only. All access activities are audited.
        </div>
      </footer>
    </main>
  );
};
