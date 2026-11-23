import React, { useEffect } from "react";
import { X, User, Target, Shield, Clock, Globe, GitCommit, Copy, Check } from "lucide-react";
import { AuditEventItem } from "../../types/audit";
import { enterpriseLightTokens as tokens, secondaryButtonBase } from "../manual-entry/enterpriseLightTokens";

interface AuditDetailDrawerProps {
  event: AuditEventItem | null;
  onClose: () => void;
  onViewCorrelation: (correlationId: string) => void;
}

export const AuditDetailDrawer: React.FC<AuditDetailDrawerProps> = ({
  event,
  onClose,
  onViewCorrelation,
}) => {
  const [copied, setCopied] = React.useState(false);

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!event) return null;

  const handleCopyCorrelation = () => {
    if (event.correlation_id) {
      navigator.clipboard.writeText(event.correlation_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const cardStyle: React.CSSProperties = {
    backgroundColor: "#FFFFFF",
    border: `1px solid ${tokens.border}`,
    borderRadius: "8px",
    padding: "14px 16px",
    marginBottom: "14px",
  };

  const sectionHeaderStyle: React.CSSProperties = {
    fontSize: "0.75rem",
    fontWeight: 700,
    color: tokens.textMuted,
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    marginBottom: "10px",
    display: "flex",
    alignItems: "center",
    gap: "6px",
  };

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        aria-hidden="true"
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: "rgba(15, 23, 42, 0.4)",
          zIndex: 100,
          backdropFilter: "blur(1px)",
        }}
      />

      {/* Slide-out Drawer */}
      <aside
        aria-label="Audit Event Detail Inspector"
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: "100%",
          maxWidth: "min(540px, 100vw)",
          backgroundColor: tokens.surfacePrimary,
          borderLeft: `1px solid ${tokens.border}`,
          zIndex: 101,
          display: "flex",
          flexDirection: "column",
          boxShadow: "-4px 0 24px rgba(0, 0, 0, 0.12)",
          fontFamily: tokens.fontFamily,
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 20px",
            borderBottom: `1px solid ${tokens.border}`,
            backgroundColor: "#FFFFFF",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontSize: "0.72rem", fontWeight: 700, color: tokens.textMuted, textTransform: "uppercase" }}>
              Audit Event Inspector
            </div>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 800, color: tokens.textPrimary, margin: "2px 0 0 0" }}>
              {event.event_type}
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close Inspector"
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: "6px",
              borderRadius: "6px",
              color: tokens.textSecondary,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Scrollable Body */}
        <div style={{ flex: 1, overflowY: "auto", padding: "18px 20px" }}>
          {/* Status Banner */}
          <div
            style={{
              padding: "12px 14px",
              borderRadius: "6px",
              marginBottom: "16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              backgroundColor: event.result === "SUCCESS" ? "#DCFCE7" : event.result === "DENIED" ? "#F3E8FF" : "#FEE2E2",
              border: `1px solid ${event.result === "SUCCESS" ? "#86EFAC" : event.result === "DENIED" ? "#D8B4FE" : "#FCA5A5"}`,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "1rem" }}>
                {event.result === "SUCCESS" ? "✅" : event.result === "DENIED" ? "🔒" : "⚠️"}
              </span>
              <div>
                <div style={{ fontWeight: 700, fontSize: "0.84rem", color: event.result === "SUCCESS" ? "#166534" : event.result === "DENIED" ? "#6B21A8" : "#991B1B" }}>
                  Outcome: {event.result}
                </div>
                <div style={{ fontSize: "0.72rem", color: tokens.textSecondary }}>
                  Severity: <span style={{ fontWeight: 700 }}>{event.severity}</span> | Module: <span style={{ fontWeight: 700 }}>{event.module}</span>
                </div>
              </div>
            </div>
            <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontFamily: "monospace" }}>
              {new Date(event.timestamp).toISOString().replace("T", " ").substring(0, 19)} UTC
            </div>
          </div>

          {/* Actor Card */}
          <div style={cardStyle}>
            <div style={sectionHeaderStyle}>
              <User size={14} />
              <span>Actor (Who)</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "minmax(90px, auto) 1fr", gap: "8px", fontSize: "0.82rem", alignItems: "start" }}>
              <div style={{ color: tokens.textMuted }}>Username:</div>
              <div style={{ fontWeight: 700, color: tokens.textPrimary }}>{event.actor.username}</div>

              {event.actor.full_name && (
                <>
                  <div style={{ color: tokens.textMuted }}>Full Name:</div>
                  <div style={{ color: tokens.textPrimary }}>{event.actor.full_name}</div>
                </>
              )}

              {event.actor.email && (
                <>
                  <div style={{ color: tokens.textMuted }}>Email:</div>
                  <div style={{ color: tokens.textPrimary }}>{event.actor.email}</div>
                </>
              )}

              <div style={{ color: tokens.textMuted }}>Assigned Roles:</div>
              <div>
                {event.actor.roles && event.actor.roles.length > 0 ? (
                  <span style={{ fontWeight: 600, color: tokens.primaryAccent }}>{event.actor.roles.join(", ")}</span>
                ) : (
                  <span style={{ color: tokens.textMuted }}>N/A (System / Unauthenticated)</span>
                )}
              </div>

              {event.actor.user_id && (
                <>
                  <div style={{ color: tokens.textMuted }}>User GUID:</div>
                  <div style={{ fontFamily: "monospace", fontSize: "0.74rem", color: tokens.textSecondary }}>{event.actor.user_id}</div>
                </>
              )}
            </div>
          </div>

          {/* Target Card */}
          <div style={cardStyle}>
            <div style={sectionHeaderStyle}>
              <Target size={14} />
              <span>Target Object (What)</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "minmax(90px, auto) 1fr", gap: "8px", fontSize: "0.82rem", alignItems: "start" }}>
              <div style={{ color: tokens.textMuted, whiteSpace: "nowrap" }}>Entity Type:</div>
              <div style={{ fontWeight: 700, color: tokens.textPrimary, wordBreak: "break-word" }}>{event.target.entity_type}</div>

              <div style={{ color: tokens.textMuted, whiteSpace: "nowrap" }}>Target ID:</div>
              <div style={{ display: "flex", alignItems: "flex-start", gap: "6px", minWidth: 0 }}>
                <span
                  style={{
                    fontFamily: "monospace",
                    fontSize: "0.78rem",
                    color: tokens.textPrimary,
                    wordBreak: "break-all",
                    overflowWrap: "anywhere",
                    backgroundColor: "#F1F5F9",
                    padding: "2px 6px",
                    borderRadius: "4px",
                    border: `1px solid ${tokens.borderLight}`,
                    lineHeight: "1.4",
                  }}
                >
                  {event.target.entity_id}
                </span>
              </div>

              {event.target.entity_name && (
                <>
                  <div style={{ color: tokens.textMuted, whiteSpace: "nowrap" }}>Target Name:</div>
                  <div style={{ color: tokens.textPrimary, wordBreak: "break-word" }}>{event.target.entity_name}</div>
                </>
              )}
            </div>
          </div>

          {/* Network & Lineage Card */}
          <div style={cardStyle}>
            <div style={sectionHeaderStyle}>
              <Globe size={14} />
              <span>Network & Correlation Lineage</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "minmax(90px, auto) 1fr", gap: "8px", fontSize: "0.82rem", alignItems: "start" }}>
              <div style={{ color: tokens.textMuted }}>Client IP:</div>
              <div style={{ fontFamily: "monospace", color: tokens.textPrimary }}>{event.ip_address || "Internal / Local"}</div>

              <div style={{ color: tokens.textMuted }}>User Agent:</div>
              <div style={{ fontSize: "0.74rem", color: tokens.textSecondary, wordBreak: "break-all" }}>
                {event.user_agent || "N/A"}
              </div>

              {event.correlation_id && (
                <>
                  <div style={{ color: tokens.textMuted }}>Correlation ID:</div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <span style={{ fontFamily: "monospace", fontSize: "0.74rem", color: tokens.primaryAccent }}>
                      {event.correlation_id}
                    </span>
                    <button
                      type="button"
                      onClick={handleCopyCorrelation}
                      aria-label="Copy correlation ID"
                      style={{ background: "none", border: "none", cursor: "pointer", padding: "2px", color: tokens.textMuted }}
                    >
                      {copied ? <Check size={13} color="#166534" /> : <Copy size={13} />}
                    </button>
                  </div>
                </>
              )}
            </div>

            {event.correlation_id && (
              <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: `1px solid ${tokens.borderLight}` }}>
                <button
                  type="button"
                  onClick={() => onViewCorrelation(event.correlation_id!)}
                  aria-label="View complete correlation trace"
                  style={{
                    ...secondaryButtonBase,
                    width: "100%",
                    minHeight: "34px",
                    fontSize: "0.78rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                    color: tokens.primaryAccent,
                    borderColor: tokens.primaryAccentBorder,
                    backgroundColor: tokens.primaryAccentLight,
                  }}
                >
                  <GitCommit size={14} />
                  <span>Trace Complete Event Timeline ({event.correlation_id.substring(0, 12)}...)</span>
                </button>
              </div>
            )}
          </div>

          {/* Structured Safe Metadata Details */}
          <div style={cardStyle}>
            <div style={sectionHeaderStyle}>
              <Shield size={14} />
              <span>Event Metadata & Details (Safe Presentation)</span>
            </div>

            {Object.keys(event.details).length === 0 ? (
              <div style={{ fontSize: "0.78rem", color: tokens.textMuted, fontStyle: "italic" }}>
                No extra metadata attributes recorded.
              </div>
            ) : (
              <div
                style={{
                  backgroundColor: "#F8FAFC",
                  border: `1px solid ${tokens.borderLight}`,
                  borderRadius: "6px",
                  padding: "10px 12px",
                  maxHeight: "240px",
                  overflowY: "auto",
                  fontFamily: "monospace",
                  fontSize: "0.75rem",
                  color: tokens.textPrimary,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                }}
              >
                {JSON.stringify(event.details, null, 2)}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "14px 20px",
            borderTop: `1px solid ${tokens.border}`,
            backgroundColor: "#FFFFFF",
            display: "flex",
            justifyContent: "flex-end",
          }}
        >
          <button
            type="button"
            onClick={onClose}
            aria-label="Close drawer"
            style={{
              ...secondaryButtonBase,
              minHeight: "36px",
              padding: "6px 18px",
              fontSize: "0.82rem",
            }}
          >
            Close
          </button>
        </div>
      </aside>
    </>
  );
};
