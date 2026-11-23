/**
 * 404 Page Not Found Component for ACC RMC Platform.
 * Enterprise Operations Light Theme.
 */

import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  enterpriseLightTokens as tokens,
  primaryButtonBase,
} from "../components/manual-entry/enterpriseLightTokens";

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: tokens.pageBg,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: "24px",
        fontFamily: tokens.fontFamily,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "480px",
          backgroundColor: tokens.surfacePrimary,
          border: `1px solid ${tokens.border}`,
          borderRadius: "12px",
          boxShadow: tokens.shadowCard,
          padding: "36px 32px",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: "3rem", marginBottom: "12px" }}>🧭</div>
        <h1
          style={{
            fontSize: "1.6rem",
            fontWeight: 800,
            color: tokens.textPrimary,
            margin: "0 0 8px 0",
          }}
        >
          404 - Page Not Found
        </h1>
        <p
          style={{
            fontSize: "0.88rem",
            color: tokens.textSecondary,
            margin: "0 0 16px 0",
            lineHeight: 1.5,
          }}
        >
          The requested URL path <code style={{ backgroundColor: tokens.primaryAccentLight, color: tokens.accent, padding: "2px 6px", borderRadius: "4px" }}>{location.pathname}</code> does not exist on the ACC RMC AI Platform.
        </p>

        <div
          style={{
            backgroundColor: tokens.surfaceSecondary,
            border: `1px solid ${tokens.borderLight}`,
            borderRadius: "8px",
            padding: "12px",
            marginBottom: "24px",
            textAlign: "left",
            fontSize: "0.8rem",
          }}
        >
          <div style={{ fontWeight: 700, color: tokens.textPrimary, marginBottom: "4px" }}>
            Target Public Routes:
          </div>
          <ul style={{ margin: 0, paddingLeft: "18px", color: tokens.textSecondary }}>
            <li><code>/acc/dashboard</code> - Operations Dashboard</li>
            <li><code>/acc/manual-production-entry</code> - Manual Production Entry</li>
            <li><code>/acc/dataset-ingestion</code> - Dataset Ingestion</li>
            <li><code>/acc/login</code> - Operator Login</li>
          </ul>
        </div>

        <button
          onClick={() => navigate("/acc/dashboard")}
          style={{
            ...primaryButtonBase,
            width: "100%",
            padding: "10px 18px",
            display: "flex",
            justifyContent: "center",
          }}
        >
          ← Return to ACC Dashboard
        </button>
      </div>
    </div>
  );
};
