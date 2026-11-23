/**
 * Enterprise 403 Access Denied Component.
 * Styled strictly with Approved Enterprise Light Theme Tokens.
 */

import React from "react";
import { useNavigate } from "react-router-dom";
import { enterpriseLightTokens as tokens, primaryButtonBase, secondaryButtonBase } from "../manual-entry/enterpriseLightTokens";
import { CanonicalRole } from "../../types/auth";
import { useAuth } from "../../context/AuthContext";

interface AccessDeniedProps {
  requiredRoles?: CanonicalRole[];
  userRoles?: CanonicalRole[];
  customMessage?: string;
}

export const AccessDenied: React.FC<AccessDeniedProps> = ({
  requiredRoles,
  userRoles,
  customMessage,
}) => {
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const activeRoles = userRoles || user?.roles || [];

  return (
    <div
      style={{
        minHeight: "75vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        backgroundColor: tokens.pageBg,
        fontFamily: tokens.fontFamily,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "520px",
          backgroundColor: tokens.surfacePrimary,
          border: `1px solid ${tokens.border}`,
          borderRadius: "10px",
          boxShadow: tokens.shadowCard,
          padding: "36px 32px",
          textAlign: "center",
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: "56px",
            height: "56px",
            borderRadius: "12px",
            backgroundColor: tokens.errorRedLight,
            border: `1px solid ${tokens.errorRedBorder}`,
            color: tokens.errorRed,
            fontSize: "1.6rem",
            marginBottom: "16px",
          }}
        >
          🛡️
        </div>

        <h1
          style={{
            fontSize: "1.35rem",
            fontWeight: 700,
            color: tokens.textPrimary,
            margin: "0 0 8px 0",
            letterSpacing: "-0.01em",
          }}
        >
          Access Restricted (403 Forbidden)
        </h1>

        <p
          style={{
            fontSize: "0.875rem",
            color: tokens.textSecondary,
            lineHeight: 1.5,
            margin: "0 0 20px 0",
          }}
        >
          {customMessage ||
            "You do not have the required role permissions to access this operational feature. Your access attempt has been logged for compliance."}
        </p>

        {requiredRoles && requiredRoles.length > 0 && (
          <div
            style={{
              backgroundColor: tokens.surfaceSecondary,
              border: `1px solid ${tokens.borderLight}`,
              borderRadius: "6px",
              padding: "12px 16px",
              textAlign: "left",
              marginBottom: "24px",
              fontSize: "0.8rem",
            }}
          >
            <div style={{ fontWeight: 600, color: tokens.textPrimary, marginBottom: "6px" }}>
              Authorization Details:
            </div>
            <div style={{ color: tokens.textSecondary, marginBottom: "4px" }}>
              <strong>Required Role(s):</strong> {requiredRoles.join(", ")}
            </div>
            <div style={{ color: tokens.textSecondary }}>
              <strong>Your Assigned Role(s):</strong>{" "}
              {activeRoles.length > 0 ? activeRoles.join(", ") : "None Assigned"}
            </div>
          </div>
        )}

        <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
          <button
            type="button"
            onClick={() => navigate("/acc/dashboard")}
            style={{
              ...primaryButtonBase,
              padding: "9px 18px",
            }}
          >
            ← Return to Dashboard
          </button>
          <button
            type="button"
            onClick={logout}
            style={{
              ...secondaryButtonBase,
              padding: "9px 18px",
            }}
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
};
