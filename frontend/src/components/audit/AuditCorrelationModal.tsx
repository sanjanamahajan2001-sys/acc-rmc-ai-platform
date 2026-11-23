import React, { useEffect, useState } from "react";
import { X, GitCommit, Clock, ArrowDown, User } from "lucide-react";
import { AuditEventItem, AuditCorrelationResponse } from "../../types/audit";
import { auditService } from "../../services/auditService";
import { enterpriseLightTokens as tokens, secondaryButtonBase } from "../manual-entry/enterpriseLightTokens";

interface AuditCorrelationModalProps {
  correlationId: string | null;
  onClose: () => void;
  onSelectEvent: (event: AuditEventItem) => void;
}

export const AuditCorrelationModal: React.FC<AuditCorrelationModalProps> = ({
  correlationId,
  onClose,
  onSelectEvent,
}) => {
  const [data, setData] = useState<AuditCorrelationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!correlationId) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    auditService
      .getCorrelationTrace(correlationId)
      .then((res) => {
        if (mounted) setData(res);
      })
      .catch((err) => {
        if (mounted) setError(err.message || "Failed to load correlation trace.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [correlationId]);

  if (!correlationId) return null;

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
          backgroundColor: "rgba(15, 23, 42, 0.5)",
          zIndex: 110,
          backdropFilter: "blur(2px)",
        }}
      />

      {/* Modal Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Correlation Lineage Trace"
        style={{
          position: "fixed",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "90%",
          maxWidth: "720px",
          maxHeight: "85vh",
          backgroundColor: tokens.surfacePrimary,
          border: `1px solid ${tokens.border}`,
          borderRadius: "10px",
          zIndex: 111,
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
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
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                padding: "8px",
                borderRadius: "6px",
                backgroundColor: tokens.primaryAccentLight,
                color: tokens.primaryAccent,
              }}
            >
              <GitCommit size={20} />
            </div>
            <div>
              <div style={{ fontSize: "0.72rem", fontWeight: 700, color: tokens.textMuted, textTransform: "uppercase" }}>
                Lifecycle Correlation Lineage
              </div>
              <div style={{ fontSize: "0.86rem", fontWeight: 700, color: tokens.textPrimary, fontFamily: "monospace" }}>
                {correlationId}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close Trace Modal"
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: "6px",
              borderRadius: "6px",
              color: tokens.textSecondary,
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Timeline Content */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px" }}>
          {loading ? (
            <div style={{ padding: "40px", textAlign: "center", color: tokens.textMuted }}>
              <div style={{ display: "inline-block", animation: "spin 1s linear infinite", fontSize: "1.2rem", marginBottom: "8px" }}>
                🔄
              </div>
              <div>Retrieving correlation trace sequence...</div>
            </div>
          ) : error ? (
            <div
              style={{
                padding: "16px",
                backgroundColor: "#FEE2E2",
                border: "1px solid #FCA5A5",
                borderRadius: "6px",
                color: "#991B1B",
                fontSize: "0.84rem",
              }}
            >
              {error}
            </div>
          ) : !data || data.events.length === 0 ? (
            <div style={{ padding: "40px", textAlign: "center", color: tokens.textMuted }}>
              No correlation events found for this identifier.
            </div>
          ) : (
            <div style={{ position: "relative", paddingLeft: "24px" }}>
              {/* Vertical line */}
              <div
                style={{
                  position: "absolute",
                  left: "7px",
                  top: "10px",
                  bottom: "10px",
                  width: "2px",
                  backgroundColor: tokens.border,
                }}
              />

              {data.events.map((ev, idx) => {
                const isLast = idx === data.events.length - 1;
                return (
                  <div key={ev.id} style={{ position: "relative", marginBottom: isLast ? 0 : "20px" }}>
                    {/* Node Dot */}
                    <div
                      style={{
                        position: "absolute",
                        left: "-24px",
                        top: "4px",
                        width: "16px",
                        height: "16px",
                        borderRadius: "50%",
                        backgroundColor: ev.result === "SUCCESS" ? "#166534" : "#991B1B",
                        border: "3px solid #FFFFFF",
                        boxShadow: "0 0 0 1px #CBD5E1",
                      }}
                    />

                    {/* Event Box */}
                    <div
                      style={{
                        backgroundColor: "#FFFFFF",
                        border: `1px solid ${tokens.border}`,
                        borderRadius: "8px",
                        padding: "12px 14px",
                        boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                      }}
                      onClick={() => onSelectEvent(ev)}
                      onMouseEnter={(e) => (e.currentTarget.style.borderColor = tokens.primaryAccent)}
                      onMouseLeave={(e) => (e.currentTarget.style.borderColor = tokens.border)}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                        <div>
                          <span
                            style={{
                              fontSize: "0.68rem",
                              fontWeight: 700,
                              textTransform: "uppercase",
                              padding: "2px 6px",
                              borderRadius: "4px",
                              backgroundColor: tokens.primaryAccentLight,
                              color: tokens.primaryAccent,
                              marginRight: "6px",
                            }}
                          >
                            {ev.module}
                          </span>
                          <span style={{ fontWeight: 700, fontSize: "0.85rem", color: tokens.textPrimary }}>
                            {ev.event_type}
                          </span>
                        </div>

                        <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontFamily: "monospace" }}>
                          {new Date(ev.timestamp).toISOString().replace("T", " ").substring(0, 19)} UTC
                        </div>
                      </div>

                      <div style={{ display: "flex", gap: "14px", marginTop: "8px", fontSize: "0.75rem", color: tokens.textSecondary }}>
                        <div>
                          Actor: <strong style={{ color: tokens.textPrimary }}>{ev.actor.username}</strong>
                        </div>
                        <div>
                          Target: <strong style={{ color: tokens.textPrimary }}>{ev.target.entity_type} ({ev.target.entity_id})</strong>
                        </div>
                        <div>
                          Status: <strong style={{ color: ev.result === "SUCCESS" ? "#166534" : "#991B1B" }}>{ev.result}</strong>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "14px 20px",
            borderTop: `1px solid ${tokens.border}`,
            backgroundColor: "#FFFFFF",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div style={{ fontSize: "0.75rem", color: tokens.textMuted }}>
            Total Trace Events: <strong>{data?.total_events ?? 0}</strong>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close modal"
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
      </div>
    </>
  );
};
