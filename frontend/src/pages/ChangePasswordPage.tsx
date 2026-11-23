/**
 * Forced & Self-Service Password Change Page for ACC RMC Platform.
 * Route: /acc/change-password
 * Theme: Frozen Light Enterprise Theme (#F4F6F9, #FBFCFE, #DCE2EA, #172033, #4F46E5).
 *
 * Implements:
 * - Enterprise Policy Feedback (10+ chars, upper, lower, number, special char)
 * - Show/Hide toggle for all password inputs
 * - Mismatch validation & real-time criteria checklists
 * - Authoritative backend validation integration (/api/v1/auth/change-password)
 * - Zero hardcoded or mock credentials
 */

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  enterpriseLightTokens as tokens,
  primaryButtonBase,
  secondaryButtonBase,
  formInputStyle,
  formLabelStyle,
} from "../components/manual-entry/enterpriseLightTokens";

export const ChangePasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const { changePassword, logout, user, error, clearError } = useAuth();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Policy validation checks matching backend SecurityConfig
  const criteria = {
    minLength: newPassword.length >= 10,
    hasUpper: /[A-Z]/.test(newPassword),
    hasLower: /[a-z]/.test(newPassword),
    hasDigit: /[0-9]/.test(newPassword),
    hasSpecial: Array.from(newPassword).some((char) => "!@#$%^&*()_+-=[]{}|;:,.<>?".includes(char)),
    matchesConfirm: Boolean(newPassword && confirmPassword && newPassword === confirmPassword),
  };

  const isAllValid =
    criteria.minLength &&
    criteria.hasUpper &&
    criteria.hasLower &&
    criteria.hasDigit &&
    criteria.hasSpecial &&
    criteria.matchesConfirm;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!currentPassword) {
      setLocalError("Please enter your current password or temporary passcode.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setLocalError("New password and confirmation do not match.");
      return;
    }

    if (!criteria.minLength || !criteria.hasUpper || !criteria.hasLower || !criteria.hasDigit || !criteria.hasSpecial) {
      setLocalError("New password does not satisfy all enterprise security requirements.");
      return;
    }

    setSubmitting(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setSuccessMessage("Password updated successfully. Transitioning to operations dashboard...");
      setTimeout(() => {
        navigate("/acc/dashboard", { replace: true });
      }, 1000);
    } catch (err: any) {
      setLocalError(err.message || "Failed to update password. Please verify current password.");
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
          maxWidth: "480px",
          backgroundColor: tokens.surfacePrimary,
          border: `1px solid ${tokens.border}`,
          borderRadius: tokens.radius,
          boxShadow: tokens.shadowCard,
          padding: "36px 32px",
          boxSizing: "border-box",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "24px" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: "48px",
              height: "48px",
              borderRadius: "8px",
              backgroundColor: tokens.statusWarningBg,
              border: `1px solid ${tokens.statusWarningBorder}`,
              color: tokens.warningAmber,
              fontSize: "1.4rem",
              marginBottom: "12px",
            }}
            aria-hidden="true"
          >
            🔒
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
            Password Setup Required
          </h1>
          <p style={{ margin: 0, fontSize: "0.85rem", color: tokens.textSecondary, lineHeight: 1.4 }}>
            Set a permanent, policy-compliant password to unlock platform operations.
          </p>
          {user && (
            <div
              style={{
                display: "inline-block",
                marginTop: "10px",
                backgroundColor: tokens.surfaceSecondary,
                color: tokens.textSecondary,
                fontSize: "0.78rem",
                fontWeight: 600,
                padding: "3px 10px",
                borderRadius: "4px",
                border: `1px solid ${tokens.borderLight}`,
              }}
            >
              Account: {user.username} ({user.roles.join(", ")})
            </div>
          )}
        </div>

        {(localError || error) && (
          <div
            role="alert"
            aria-live="assertive"
            style={{
              backgroundColor: tokens.statusErrorBg,
              border: `1px solid ${tokens.statusErrorBorder}`,
              borderRadius: tokens.radius,
              padding: "10px 14px",
              marginBottom: "18px",
              fontSize: "0.82rem",
              color: tokens.statusErrorText,
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

        {successMessage && (
          <div
            role="status"
            aria-live="polite"
            style={{
              backgroundColor: tokens.statusSuccessBg,
              border: `1px solid ${tokens.statusSuccessBorder}`,
              borderRadius: tokens.radius,
              padding: "10px 14px",
              marginBottom: "18px",
              fontSize: "0.82rem",
              color: tokens.statusSuccessText,
              fontWeight: 500,
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>✓</span>
            <div>{successMessage}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
              <label htmlFor="current-pw" style={{ ...formLabelStyle, marginBottom: 0 }}>
                Current / Temporary Passcode <span style={{ color: tokens.errorRed }}>*</span>
              </label>
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
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
                aria-label={showCurrent ? "Hide current passcode" : "Show current passcode"}
              >
                {showCurrent ? "Hide" : "Show"}
              </button>
            </div>
            <input
              id="current-pw"
              type={showCurrent ? "text" : "password"}
              name="current-password"
              value={currentPassword}
              onChange={(e) => {
                setCurrentPassword(e.target.value);
                if (localError) setLocalError(null);
              }}
              style={formInputStyle}
              required
              autoComplete="current-password"
              disabled={submitting}
            />
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
              <label htmlFor="new-pw" style={{ ...formLabelStyle, marginBottom: 0 }}>
                New Secure Password <span style={{ color: tokens.errorRed }}>*</span>
              </label>
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
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
                aria-label={showNew ? "Hide new password" : "Show new password"}
              >
                {showNew ? "Hide" : "Show"}
              </button>
            </div>
            <input
              id="new-pw"
              type={showNew ? "text" : "password"}
              name="new-password"
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value);
                if (localError) setLocalError(null);
              }}
              style={formInputStyle}
              required
              autoComplete="new-password"
              placeholder="Minimum 10 characters"
              disabled={submitting}
            />
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
              <label htmlFor="confirm-pw" style={{ ...formLabelStyle, marginBottom: 0 }}>
                Confirm New Password <span style={{ color: tokens.errorRed }}>*</span>
              </label>
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
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
                aria-label={showConfirm ? "Hide confirmation password" : "Show confirmation password"}
              >
                {showConfirm ? "Hide" : "Show"}
              </button>
            </div>
            <input
              id="confirm-pw"
              type={showConfirm ? "text" : "password"}
              name="confirm-password"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                if (localError) setLocalError(null);
              }}
              style={formInputStyle}
              required
              autoComplete="new-password"
              disabled={submitting}
            />
          </div>

          {/* Password Policy Criteria Checklist */}
          <div
            style={{
              padding: "12px 14px",
              backgroundColor: tokens.surfaceSecondary,
              border: `1px solid ${tokens.borderLight}`,
              borderRadius: tokens.radius,
              fontSize: "0.75rem",
              color: tokens.textSecondary,
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "6px 12px",
            }}
          >
            <div style={{ color: criteria.minLength ? tokens.statusSuccessText : tokens.textSecondary }}>
              {criteria.minLength ? "✓" : "•"} At least 10 characters
            </div>
            <div style={{ color: criteria.hasUpper ? tokens.statusSuccessText : tokens.textSecondary }}>
              {criteria.hasUpper ? "✓" : "•"} One uppercase (A-Z)
            </div>
            <div style={{ color: criteria.hasLower ? tokens.statusSuccessText : tokens.textSecondary }}>
              {criteria.hasLower ? "✓" : "•"} One lowercase (a-z)
            </div>
            <div style={{ color: criteria.hasDigit ? tokens.statusSuccessText : tokens.textSecondary }}>
              {criteria.hasDigit ? "✓" : "•"} One number (0-9)
            </div>
            <div style={{ color: criteria.hasSpecial ? tokens.statusSuccessText : tokens.textSecondary }}>
              {criteria.hasSpecial ? "✓" : "•"} One special character
            </div>
            <div style={{ color: criteria.matchesConfirm ? tokens.statusSuccessText : tokens.textSecondary }}>
              {criteria.matchesConfirm ? "✓" : "•"} Passwords match
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "6px" }}>
            <button
              type="submit"
              disabled={submitting || (Boolean(newPassword) && !isAllValid)}
              style={{
                ...primaryButtonBase,
                width: "100%",
                padding: "11px",
                fontSize: "0.9rem",
                cursor: submitting || (Boolean(newPassword) && !isAllValid) ? "not-allowed" : "pointer",
                opacity: submitting || (Boolean(newPassword) && !isAllValid) ? 0.65 : 1,
              }}
            >
              {submitting ? "Updating Enterprise Password..." : "Set Password & Proceed →"}
            </button>
            <button
              type="button"
              onClick={logout}
              disabled={submitting}
              style={{
                ...secondaryButtonBase,
                width: "100%",
                padding: "9px",
                fontSize: "0.85rem",
                cursor: submitting ? "not-allowed" : "pointer",
              }}
            >
              Sign Out
            </button>
          </div>
        </form>
      </div>
    </main>
  );
};
