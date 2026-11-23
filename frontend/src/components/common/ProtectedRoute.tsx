/**
 * Protected Route Component for ACC RMC Platform.
 *
 * Enforces:
 * 1. Unauthenticated gate: Redirects to /acc/login.
 * 2. Forced password change quarantine: Redirects must_change_password users to /acc/change-password.
 * 3. Role authorization gate: Renders AccessDenied (403) if user lacks required canonical roles.
 * 4. Enterprise Light Theme loading indicator during session bootstrap.
 * 5. Supports both Outlet (nested routing) and children elements.
 */

import React from "react";
import { Navigate, useLocation, Outlet } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { CanonicalRole } from "../../types/auth";
import { enterpriseLightTokens as tokens } from "../manual-entry/enterpriseLightTokens";
import { AccessDenied } from "./AccessDenied";

interface ProtectedRouteProps {
  children?: React.ReactNode;
  allowedRoles?: CanonicalRole[];
  requireForcedPasswordChange?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
  requireForcedPasswordChange = false,
}) => {
  const { isAuthenticated, isLoading, mustChangePassword, hasAnyRole, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: tokens.pageBg,
          fontFamily: tokens.fontFamily,
          color: tokens.textSecondary,
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              border: `3px solid ${tokens.border}`,
              borderTopColor: tokens.accent,
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              margin: "0 auto 16px",
            }}
          />
          <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
          <div style={{ fontSize: "0.9rem", fontWeight: 600, color: tokens.textPrimary }}>
            Verifying ACC Security Session...
          </div>
          <div style={{ fontSize: "0.78rem", color: tokens.textSecondary, marginTop: "4px" }}>
            Database identity & role resolution
          </div>
        </div>
      </div>
    );
  }

  // 1. Unauthenticated -> Redirect to Login
  if (!isAuthenticated) {
    return <Navigate to="/acc/login" state={{ from: location }} replace />;
  }

  // 2. Forced Password Change Quarantine
  if (mustChangePassword && !requireForcedPasswordChange) {
    return <Navigate to="/acc/change-password" replace />;
  }

  // 3. Already Normal Password accessing Password Change Page -> Redirect to Dashboard
  if (!mustChangePassword && requireForcedPasswordChange) {
    return <Navigate to="/acc/dashboard" replace />;
  }

  // 4. Role Authorization Gate
  if (allowedRoles && allowedRoles.length > 0 && !hasAnyRole(allowedRoles)) {
    return <AccessDenied requiredRoles={allowedRoles} userRoles={user?.roles} />;
  }

  return children ? <>{children}</> : <Outlet />;
};
