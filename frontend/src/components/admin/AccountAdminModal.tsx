/**
 * Administration & Account Security Modal for ACC RMC Platform.
 *
 * Provides:
 * 1. User Identity & Current Profile Overview.
 * 2. Self-Service Change Password Form (with real-time 6-point policy verification).
 * 3. Administrator Governance Shortcut & Capability Overview (SUPER_ADMIN / ADMIN only).
 * 4. Frozen Enterprise Light Theme (#F4F6F9, #FBFCFE, #DCE2EA, #172033, #4F46E5).
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import {
  enterpriseLightTokens as tokens,
  primaryButtonBase,
  secondaryButtonBase,
  formInputStyle,
  formLabelStyle,
} from "../manual-entry/enterpriseLightTokens";
import { Settings, User as UserIcon, Lock, Shield, X, Check, AlertTriangle, ArrowRight } from "lucide-react";

interface AccountAdminModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AccountAdminModal: React.FC<AccountAdminModalProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { user, isSuperAdmin, isAdmin, changePassword, logout } = useAuth();

  const [activeTab, setActiveTab] = useState<"profile" | "password" | "admin">("profile");

  // Change Password Form State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !submitting) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, submitting]);

  if (!isOpen) return null;

  // Real-time policy criteria matching backend SecurityConfig
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

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    setSuccessMessage(null);

    if (!currentPassword) {
      setLocalError("Please enter your current account password.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setLocalError("New password and confirmation do not match.");
      return;
    }

    if (!isAllValid) {
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
      setSuccessMessage("Password updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setLocalError(err.message || "Failed to update password. Please check your current password.");
    } finally {
      setSubmitting(false);
    }
  };

  const isPlatformAdmin = isSuperAdmin || isAdmin;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="account-admin-modal-title"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(15, 23, 42, 0.45)",
        backdropFilter: "blur(4px)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1100,
        padding: "16px",
        fontFamily: tokens.fontFamily,
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          backgroundColor: tokens.surfacePrimary,
          border: `1px solid ${tokens.border}`,
          borderRadius: "12px",
          width: "100%",
          maxWidth: "580px",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "24px",
          boxShadow: tokens.shadowModal,
          color: tokens.textPrimary,
          boxSizing: "border-box",
        }}
      >
        {/* Header with Title and Close Button */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                backgroundColor: tokens.primaryAccentLight,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: tokens.primaryAccent,
                flexShrink: 0,
              }}
            >
              <Settings size={20} />
            </div>
            <div>
              <h2 id="account-admin-modal-title" style={{ fontSize: "1.15rem", fontWeight: 700, margin: 0, color: tokens.textPrimary }}>
                Account & Platform Settings
              </h2>
              <p style={{ margin: 0, fontSize: "0.8rem", color: tokens.textSecondary, marginTop: "2px" }}>
                Operator security profile and platform administration
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: `1px solid ${tokens.border}`,
              borderRadius: "6px",
              padding: "6px",
              cursor: "pointer",
              color: tokens.textSecondary,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              lineHeight: 1,
            }}
            aria-label="Close settings modal"
          >
            <X size={16} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: "flex",
            gap: "6px",
            borderBottom: `1px solid ${tokens.border}`,
            paddingBottom: "10px",
            marginBottom: "18px",
            overflowX: "auto",
          }}
        >
          <button
            type="button"
            onClick={() => { setActiveTab("profile"); setLocalError(null); setSuccessMessage(null); }}
            style={{
              padding: "7px 12px",
              borderRadius: "6px",
              border: "none",
              backgroundColor: activeTab === "profile" ? tokens.primaryAccentLight : "transparent",
              color: activeTab === "profile" ? tokens.primaryAccent : tokens.textSecondary,
              fontWeight: 600,
              fontSize: "0.82rem",
              cursor: "pointer",
              whiteSpace: "nowrap",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <UserIcon size={14} />
            <span>User Profile</span>
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab("password"); setLocalError(null); setSuccessMessage(null); }}
            style={{
              padding: "7px 12px",
              borderRadius: "6px",
              border: "none",
              backgroundColor: activeTab === "password" ? tokens.primaryAccentLight : "transparent",
              color: activeTab === "password" ? tokens.primaryAccent : tokens.textSecondary,
              fontWeight: 600,
              fontSize: "0.82rem",
              cursor: "pointer",
              whiteSpace: "nowrap",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <Lock size={14} />
            <span>Change Password</span>
          </button>
          {isPlatformAdmin && (
            <button
              type="button"
              onClick={() => { setActiveTab("admin"); setLocalError(null); setSuccessMessage(null); }}
              style={{
                padding: "7px 12px",
                borderRadius: "6px",
                border: "none",
                backgroundColor: activeTab === "admin" ? tokens.primaryAccentLight : "transparent",
                color: activeTab === "admin" ? tokens.primaryAccent : tokens.textSecondary,
                fontWeight: 600,
                fontSize: "0.82rem",
                cursor: "pointer",
                whiteSpace: "nowrap",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <Shield size={14} />
              <span>Admin Governance</span>
            </button>
          )}
        </div>

        {/* TAB 1: User Profile Overview */}
        {activeTab === "profile" && (
          <div>
            <div
              style={{
                backgroundColor: tokens.surfaceSecondary,
                border: `1px solid ${tokens.borderLight}`,
                borderRadius: "8px",
                padding: "16px",
                marginBottom: "18px",
              }}
            >
              <div style={{ display: "grid", gridTemplateColumns: "130px 1fr", gap: "10px", fontSize: "0.82rem", alignItems: "center" }}>
                <span style={{ color: tokens.textSecondary, fontWeight: 600 }}>Full Name:</span>
                <span style={{ fontWeight: 600, color: tokens.textPrimary }}>{user?.full_name || "Enterprise Operator"}</span>

                <span style={{ color: tokens.textSecondary, fontWeight: 600 }}>Username:</span>
                <span style={{ fontFamily: "monospace", color: tokens.primaryAccent, fontWeight: 600 }}>{user?.username}</span>

                <span style={{ color: tokens.textSecondary, fontWeight: 600 }}>Corporate Email:</span>
                <span style={{ color: tokens.textPrimary, wordBreak: "break-all" }}>{user?.email || "—"}</span>

                <span style={{ color: tokens.textSecondary, fontWeight: 600 }}>Assigned Role(s):</span>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "5px" }}>
                  {user?.roles?.map((r) => (
                    <span
                      key={r}
                      style={{
                        padding: "2px 7px",
                        borderRadius: "4px",
                        fontSize: "0.72rem",
                        fontWeight: 600,
                        backgroundColor: r === "SUPER_ADMIN" || r === "ADMIN" ? tokens.primaryAccentLight : tokens.surfacePrimary,
                        color: r === "SUPER_ADMIN" || r === "ADMIN" ? tokens.primaryAccent : tokens.textSecondary,
                        border: `1px solid ${r === "SUPER_ADMIN" || r === "ADMIN" ? tokens.primaryAccentBorder : tokens.border}`,
                      }}
                    >
                      {r}
                    </span>
                  )) || <span style={{ color: tokens.textMuted }}>—</span>}
                </div>

                <span style={{ color: tokens.textSecondary, fontWeight: 600 }}>Account Status:</span>
                <div>
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "5px",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontSize: "0.72rem",
                      fontWeight: 700,
                      backgroundColor: user?.account_status === "ACTIVE" ? tokens.statusSuccessBg : tokens.statusWarningBg,
                      color: user?.account_status === "ACTIVE" ? tokens.statusSuccessText : tokens.statusWarningText,
                      border: `1px solid ${user?.account_status === "ACTIVE" ? tokens.statusSuccessBorder : tokens.statusWarningBorder}`,
                    }}
                  >
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: user?.account_status === "ACTIVE" ? tokens.statusSuccessText : tokens.statusWarningText, display: "inline-block" }} />
                    {user?.account_status || "ACTIVE"}
                  </span>
                </div>

                <span style={{ color: tokens.textSecondary, fontWeight: 600 }}>Password Status:</span>
                <div>
                  <span
                    style={{
                      display: "inline-block",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontSize: "0.72rem",
                      fontWeight: 600,
                      backgroundColor: user?.must_change_password ? tokens.statusWarningBg : tokens.statusSuccessBg,
                      color: user?.must_change_password ? tokens.statusWarningText : tokens.statusSuccessText,
                      border: `1px solid ${user?.must_change_password ? tokens.statusWarningBorder : tokens.statusSuccessBorder}`,
                    }}
                  >
                    {user?.must_change_password ? "Must Change Upon Next Sign-in" : "Compliant / Active"}
                  </span>
                </div>

                <span style={{ color: tokens.textSecondary, fontWeight: 600 }}>Last Login:</span>
                <span style={{ color: tokens.textSecondary, fontSize: "0.8rem" }}>
                  {user?.last_login_at ? new Date(user.last_login_at).toLocaleString() : "Current Active Session"}
                </span>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button
                type="button"
                onClick={logout}
                style={{
                  ...secondaryButtonBase,
                  color: tokens.statusErrorText,
                  borderColor: tokens.statusErrorBorder,
                  backgroundColor: tokens.statusErrorBg,
                  fontSize: "0.82rem",
                }}
              >
                Sign Out Session
              </button>
              <button type="button" onClick={onClose} style={primaryButtonBase}>
                Close
              </button>
            </div>
          </div>
        )}

        {/* TAB 2: Self-Service Change Password */}
        {activeTab === "password" && (
          <div>
            <div style={{ marginBottom: "14px" }}>
              <h3 style={{ margin: "0 0 4px 0", fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
                Change your password
              </h3>
              <p style={{ margin: 0, fontSize: "0.8rem", color: tokens.textSecondary }}>
                Update your account password using the platform security policy.
              </p>
            </div>

            {localError && (
              <div
                style={{
                  padding: "10px 12px",
                  backgroundColor: tokens.statusErrorBg,
                  border: `1px solid ${tokens.statusErrorBorder}`,
                  borderRadius: "6px",
                  color: tokens.statusErrorText,
                  fontSize: "0.8rem",
                  marginBottom: "12px",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <AlertTriangle size={15} />
                <span>{localError}</span>
              </div>
            )}

            {successMessage && (
              <div
                style={{
                  padding: "10px 12px",
                  backgroundColor: tokens.statusSuccessBg,
                  border: `1px solid ${tokens.statusSuccessBorder}`,
                  borderRadius: "6px",
                  color: tokens.statusSuccessText,
                  fontSize: "0.8rem",
                  marginBottom: "12px",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <Check size={15} />
                <span>{successMessage}</span>
              </div>
            )}

            <form onSubmit={handlePasswordSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <label htmlFor="settings-current-pw" style={{ ...formLabelStyle, marginBottom: 0 }}>
                    Current Password <span style={{ color: tokens.errorRed }}>*</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowCurrent(!showCurrent)}
                    style={{ background: "none", border: "none", color: tokens.primaryAccent, fontSize: "0.75rem", cursor: "pointer", fontWeight: 600 }}
                  >
                    {showCurrent ? "Hide" : "Show"}
                  </button>
                </div>
                <input
                  id="settings-current-pw"
                  type={showCurrent ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => { setCurrentPassword(e.target.value); setLocalError(null); }}
                  style={formInputStyle}
                  placeholder="Enter current password"
                  required
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <label htmlFor="settings-new-pw" style={{ ...formLabelStyle, marginBottom: 0 }}>
                    New Password <span style={{ color: tokens.errorRed }}>*</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowNew(!showNew)}
                    style={{ background: "none", border: "none", color: tokens.primaryAccent, fontSize: "0.75rem", cursor: "pointer", fontWeight: 600 }}
                  >
                    {showNew ? "Hide" : "Show"}
                  </button>
                </div>
                <input
                  id="settings-new-pw"
                  type={showNew ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => { setNewPassword(e.target.value); setLocalError(null); }}
                  style={formInputStyle}
                  placeholder="Minimum 10 characters"
                  required
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <label htmlFor="settings-confirm-pw" style={{ ...formLabelStyle, marginBottom: 0 }}>
                    Confirm New Password <span style={{ color: tokens.errorRed }}>*</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    style={{ background: "none", border: "none", color: tokens.primaryAccent, fontSize: "0.75rem", cursor: "pointer", fontWeight: 600 }}
                  >
                    {showConfirm ? "Hide" : "Show"}
                  </button>
                </div>
                <input
                  id="settings-confirm-pw"
                  type={showConfirm ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => { setConfirmPassword(e.target.value); setLocalError(null); }}
                  style={formInputStyle}
                  placeholder="Re-enter new password"
                  required
                />
              </div>

              {/* Real-time policy checklist */}
              <div
                style={{
                  padding: "10px 12px",
                  backgroundColor: tokens.surfaceSecondary,
                  border: `1px solid ${tokens.borderLight}`,
                  borderRadius: "6px",
                  fontSize: "0.74rem",
                  color: tokens.textSecondary,
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "6px 10px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "4px", color: criteria.minLength ? tokens.statusSuccessText : tokens.textSecondary }}>
                  {criteria.minLength ? <Check size={12} /> : <span>•</span>} At least 10 characters
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "4px", color: criteria.hasUpper ? tokens.statusSuccessText : tokens.textSecondary }}>
                  {criteria.hasUpper ? <Check size={12} /> : <span>•</span>} One uppercase (A-Z)
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "4px", color: criteria.hasLower ? tokens.statusSuccessText : tokens.textSecondary }}>
                  {criteria.hasLower ? <Check size={12} /> : <span>•</span>} One lowercase (a-z)
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "4px", color: criteria.hasDigit ? tokens.statusSuccessText : tokens.textSecondary }}>
                  {criteria.hasDigit ? <Check size={12} /> : <span>•</span>} One number (0-9)
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "4px", color: criteria.hasSpecial ? tokens.statusSuccessText : tokens.textSecondary }}>
                  {criteria.hasSpecial ? <Check size={12} /> : <span>•</span>} One special character
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "4px", color: criteria.matchesConfirm ? tokens.statusSuccessText : tokens.textSecondary }}>
                  {criteria.matchesConfirm ? <Check size={12} /> : <span>•</span>} Passwords match
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "8px" }}>
                <button type="button" onClick={onClose} style={secondaryButtonBase}>
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || (Boolean(newPassword) && !isAllValid)}
                  style={{
                    ...primaryButtonBase,
                    cursor: submitting || (Boolean(newPassword) && !isAllValid) ? "not-allowed" : "pointer",
                    opacity: submitting || (Boolean(newPassword) && !isAllValid) ? 0.65 : 1,
                  }}
                >
                  {submitting ? "Updating..." : "Update Password"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* TAB 3: Admin User Administration (Restricted to SUPER_ADMIN & ADMIN) */}
        {activeTab === "admin" && isPlatformAdmin && (
          <div>
            <div
              style={{
                backgroundColor: tokens.primaryAccentLight,
                border: `1px solid ${tokens.primaryAccentBorder}`,
                borderRadius: "8px",
                padding: "16px",
                marginBottom: "16px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                <Shield size={18} color={tokens.primaryAccent} />
                <h3 style={{ margin: 0, fontSize: "0.95rem", color: tokens.primaryAccent, fontWeight: 700 }}>
                  User Administration
                </h3>
              </div>
              <p style={{ margin: 0, fontSize: "0.82rem", color: tokens.textSecondary, lineHeight: 1.45 }}>
                Manage platform user accounts, roles, access status, and temporary credentials.
              </p>
            </div>

            <div
              style={{
                backgroundColor: tokens.surfaceSecondary,
                border: `1px solid ${tokens.borderLight}`,
                borderRadius: "8px",
                padding: "14px 16px",
                marginBottom: "18px",
              }}
            >
              <div style={{ fontWeight: 600, fontSize: "0.82rem", marginBottom: "8px", color: tokens.textPrimary }}>
                Administrator Capabilities:
              </div>
              <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "0.8rem", color: tokens.textSecondary, lineHeight: 1.6 }}>
                <li>Create and provision user accounts</li>
                <li>Assign permitted RBAC roles</li>
                <li>Reset temporary credentials</li>
                <li>Activate or deactivate accounts</li>
                <li>Inspect account and access status</li>
                <li>Delete accounts where permitted</li>
              </ul>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
              <button 
                type="button" 
                onClick={() => {
                  onClose();
                  navigate("/acc/admin/users");
                }} 
                style={{
                  ...primaryButtonBase,
                  backgroundColor: tokens.primaryAccent,
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span>Launch User Management Dashboard</span>
                <ArrowRight size={14} />
              </button>
              <button type="button" onClick={onClose} style={secondaryButtonBase}>
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
