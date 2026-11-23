/**
 * Shared styling constants & design tokens for Enterprise Operations Light theme.
 * Standardized across all 6 Manual Production Entry Wizard steps.
 */
import React from "react";

export const enterpriseLightTokens = {
  pageBg: "#F4F6F9",
  surfaceCard: "#FBFCFE",
  surfacePrimary: "#FBFCFE",
  secondarySurface: "#F8FAFC",
  surfaceSecondary: "#F8FAFC",
  border: "#DCE2EA",
  borderLight: "#E9EEF4",
  textPrimary: "#172033",
  textSecondary: "#475569",
  textMuted: "#64748B",
  primaryAccent: "#4F46E5",
  primaryAccentHover: "#4338CA",
  primaryAccentLight: "rgba(79, 70, 197, 0.08)",
  primaryAccentBorder: "rgba(79, 70, 197, 0.25)",
  accent: "#4F46E5",
  successGreen: "#059669",
  successGreenLight: "rgba(5, 150, 105, 0.08)",
  successGreenBorder: "rgba(5, 150, 105, 0.25)",
  statusSuccessText: "#059669",
  statusSuccessBg: "rgba(5, 150, 105, 0.08)",
  statusSuccessBorder: "rgba(5, 150, 105, 0.25)",
  warningAmber: "#D97706",
  warningAmberLight: "rgba(217, 119, 6, 0.08)",
  warningAmberBorder: "rgba(217, 119, 6, 0.25)",
  statusWarningText: "#D97706",
  statusWarningBg: "rgba(217, 119, 6, 0.08)",
  statusWarningBorder: "rgba(217, 119, 6, 0.25)",
  errorRed: "#DC2626",
  errorRedLight: "rgba(220, 38, 38, 0.08)",
  errorRedBorder: "rgba(220, 38, 38, 0.25)",
  statusErrorText: "#DC2626",
  statusErrorBg: "rgba(220, 38, 38, 0.08)",
  statusErrorBorder: "rgba(220, 38, 38, 0.25)",
  infoBlue: "#2563EB",
  infoBlueLight: "rgba(37, 99, 235, 0.08)",
  infoBlueBorder: "rgba(37, 99, 235, 0.25)",
  statusInfoText: "#2563EB",
  statusInfoBg: "rgba(37, 99, 235, 0.08)",
  statusInfoBorder: "rgba(37, 99, 235, 0.25)",
  fontFamily: "'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  fontMono: "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace",
  radius: "8px",
  radiusLarge: "10px",
  shadowCard: "0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)",
  shadowModal: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
};

export const formInputStyle: React.CSSProperties = {
  width: "100%",
  padding: "9px 12px",
  backgroundColor: "#FFFFFF",
  border: `1px solid ${enterpriseLightTokens.border}`,
  borderRadius: enterpriseLightTokens.radius,
  color: enterpriseLightTokens.textPrimary,
  fontSize: "0.875rem",
  fontFamily: enterpriseLightTokens.fontFamily,
  boxSizing: "border-box",
  outline: "none",
  transition: "border-color 0.15s ease",
};

export const formLabelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "0.75rem",
  fontWeight: 600,
  color: enterpriseLightTokens.textSecondary,
  marginBottom: "5px",
  letterSpacing: "0.2px",
};

export const primaryButtonStyle: React.CSSProperties = {
  backgroundColor: enterpriseLightTokens.primaryAccent,
  color: "#FFFFFF",
  border: "none",
  borderRadius: enterpriseLightTokens.radius,
  padding: "9px 18px",
  fontWeight: 600,
  fontSize: "0.875rem",
  fontFamily: enterpriseLightTokens.fontFamily,
  cursor: "pointer",
  transition: "background-color 0.15s ease",
};

export const primaryButtonBase: React.CSSProperties = primaryButtonStyle;

export const secondaryButtonStyle: React.CSSProperties = {
  backgroundColor: "#FFFFFF",
  color: enterpriseLightTokens.textSecondary,
  border: `1px solid ${enterpriseLightTokens.border}`,
  borderRadius: enterpriseLightTokens.radius,
  padding: "9px 18px",
  fontWeight: 600,
  fontSize: "0.875rem",
  fontFamily: enterpriseLightTokens.fontFamily,
  cursor: "pointer",
  transition: "all 0.15s ease",
};

export const secondaryButtonBase: React.CSSProperties = secondaryButtonStyle;
