import React from "react";
import { Eye, GitCommit, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";
import { AuditEventItem } from "../../types/audit";
import { enterpriseLightTokens as tokens, secondaryButtonBase } from "../manual-entry/enterpriseLightTokens";

interface AuditTableProps {
  events: AuditEventItem[];
  loading: boolean;
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  onPageChange: (newPage: number) => void;
  onPageSizeChange: (newPageSize: number) => void;
  onSelectEvent: (event: AuditEventItem) => void;
  onSelectCorrelation: (correlationId: string) => void;
}

export const AuditTable: React.FC<AuditTableProps> = ({
  events,
  loading,
  total,
  page,
  pageSize,
  totalPages,
  onPageChange,
  onPageSizeChange,
  onSelectEvent,
  onSelectCorrelation,
}) => {
  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case "CRITICAL":
        return { bg: "#FEE2E2", text: "#991B1B", border: "#FCA5A5" };
      case "WARNING":
        return { bg: "#FFEDD5", text: "#9A3412", border: "#FDBA74" };
      case "INFO":
      default:
        return { bg: "#F1F5F9", text: "#475569", border: "#CBD5E1" };
    }
  };

  const getResultBadge = (result: string) => {
    switch (result.toUpperCase()) {
      case "SUCCESS":
        return { bg: "#DCFCE7", text: "#166534", border: "#86EFAC", label: "Success" };
      case "FAILURE":
        return { bg: "#FEE2E2", text: "#991B1B", border: "#FCA5A5", label: "Failure" };
      case "DENIED":
        return { bg: "#F3E8FF", text: "#6B21A8", border: "#D8B4FE", label: "Denied" };
      case "QUARANTINED":
        return { bg: "#FEF9C3", text: "#854D0E", border: "#FDE047", label: "Quarantine" };
      default:
        return { bg: "#F1F5F9", text: "#475569", border: "#CBD5E1", label: result };
    }
  };

  const getModuleBadge = (module: string) => {
    switch (module.toUpperCase()) {
      case "AUTH":
        return { bg: "#E0E7FF", text: "#3730A3" };
      case "USER_ADMIN":
        return { bg: "#EDE9FE", text: "#5B21B6" };
      case "DATA_INGESTION":
        return { bg: "#E0F2FE", text: "#075985" };
      case "MANUAL_ENTRY":
        return { bg: "#FEF3C7", text: "#92400E" };
      case "MODEL_TRAINING":
      case "ML_TRAINING_JOB":
      case "ML_MODEL_REGISTRY":
        return { bg: "#E0E7FF", text: "#4338CA" };
      case "QUALITY_QA":
        return { bg: "#D1FAE5", text: "#065F46" };
      case "MASTER_DATA":
        return { bg: "#FCE7F3", text: "#9D174D" };
      case "AI_MIX_OPTIMIZATION":
      case "OPTIMIZATION":
        return { bg: "#F3E8FF", text: "#6B21A8" };
      case "SETTINGS":
        return { bg: "#FEF3C7", text: "#92400E" };
      case "SECURITY":
        return { bg: "#FFE4E6", text: "#9F1239" };
      default:
        return { bg: "#F1F5F9", text: "#475569" };
    }
  };

  const formatTimestamp = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toISOString().replace("T", " ").substring(0, 19) + " UTC";
    } catch {
      return ts;
    }
  };

  return (
    <div
      style={{
        backgroundColor: tokens.surfacePrimary,
        border: `1px solid ${tokens.border}`,
        borderRadius: "8px",
        overflow: "hidden",
        boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
      }}
    >
      {/* Contained Horizontal Scroll Table Wrapper */}
      <div style={{ width: "100%", overflowX: "auto", minHeight: "260px" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            textAlign: "left",
            fontSize: "0.82rem",
            fontFamily: tokens.fontFamily,
          }}
        >
          <thead>
            <tr
              style={{
                backgroundColor: "#F8FAFC",
                borderBottom: `1px solid ${tokens.border}`,
                color: tokens.textMuted,
                fontWeight: 600,
                fontSize: "0.72rem",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              <th style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>Timestamp (UTC)</th>
              <th style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>Actor</th>
              <th style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>Module</th>
              <th style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>Event / Action</th>
              <th style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>Target Entity</th>
              <th style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>Result</th>
              <th style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>Severity</th>
              <th style={{ padding: "12px 16px", textAlign: "right", whiteSpace: "nowrap" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} style={{ padding: "40px 16px", textAlign: "center", color: tokens.textMuted }}>
                  <div style={{ display: "inline-block", animation: "spin 1s linear infinite", fontSize: "1.2rem", marginBottom: "8px" }}>
                    🔄
                  </div>
                  <div>Loading live enterprise audit records...</div>
                </td>
              </tr>
            ) : events.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: "48px 16px", textAlign: "center", color: tokens.textSecondary }}>
                  <div style={{ fontSize: "2rem", marginBottom: "8px" }}>📋</div>
                  <div style={{ fontWeight: 600, color: tokens.textPrimary }}>No audit events found</div>
                  <div style={{ fontSize: "0.78rem", color: tokens.textMuted, marginTop: "4px" }}>
                    Try broadening your search keywords or adjusting the selected filter parameters.
                  </div>
                </td>
              </tr>
            ) : (
              events.map((ev) => {
                const sev = getSeverityBadge(ev.severity);
                const res = getResultBadge(ev.result);
                const mod = getModuleBadge(ev.module);

                return (
                  <tr
                    key={ev.id}
                    style={{
                      borderBottom: `1px solid ${tokens.borderLight}`,
                      transition: "background-color 0.15s ease",
                      cursor: "pointer",
                    }}
                    onClick={() => onSelectEvent(ev)}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#F8FAFC")}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                  >
                    {/* Timestamp */}
                    <td style={{ padding: "12px 16px", whiteSpace: "nowrap", color: tokens.textPrimary, fontFamily: "monospace", fontSize: "0.78rem" }}>
                      {formatTimestamp(ev.timestamp)}
                    </td>

                    {/* Actor */}
                    <td style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>
                      <div style={{ fontWeight: 600, color: tokens.textPrimary }}>{ev.actor.username}</div>
                      {ev.actor.roles && ev.actor.roles.length > 0 && (
                        <div style={{ fontSize: "0.7rem", color: tokens.textMuted }}>{ev.actor.roles.join(", ")}</div>
                      )}
                    </td>

                    {/* Module */}
                    <td style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>
                      <span
                        style={{
                          backgroundColor: mod.bg,
                          color: mod.text,
                          padding: "3px 8px",
                          borderRadius: "4px",
                          fontSize: "0.72rem",
                          fontWeight: 600,
                        }}
                      >
                        {ev.module}
                      </span>
                    </td>

                    {/* Event / Action */}
                    <td style={{ padding: "12px 16px" }}>
                      <div style={{ fontWeight: 600, color: tokens.textPrimary }}>{ev.event_type}</div>
                      <div style={{ fontSize: "0.7rem", color: tokens.textMuted }}>Action: {ev.action}</div>
                    </td>

                    {/* Target */}
                    <td style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>
                      <div style={{ fontWeight: 500, color: tokens.textPrimary }}>{ev.target.entity_type}</div>
                      <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontFamily: "monospace" }}>
                        {ev.target.entity_id}
                      </div>
                    </td>

                    {/* Result */}
                    <td style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>
                      <span
                        style={{
                          backgroundColor: res.bg,
                          color: res.text,
                          border: `1px solid ${res.border}`,
                          padding: "3px 8px",
                          borderRadius: "4px",
                          fontSize: "0.72rem",
                          fontWeight: 600,
                        }}
                      >
                        {res.label}
                      </span>
                    </td>

                    {/* Severity */}
                    <td style={{ padding: "12px 16px", whiteSpace: "nowrap" }}>
                      <span
                        style={{
                          backgroundColor: sev.bg,
                          color: sev.text,
                          border: `1px solid ${sev.border}`,
                          padding: "2px 7px",
                          borderRadius: "4px",
                          fontSize: "0.68rem",
                          fontWeight: 700,
                          textTransform: "uppercase",
                        }}
                      >
                        {ev.severity}
                      </span>
                    </td>

                    {/* Actions */}
                    <td style={{ padding: "12px 16px", textAlign: "right", whiteSpace: "nowrap" }}>
                      <div style={{ display: "inline-flex", alignItems: "center", gap: "6px" }} onClick={(e) => e.stopPropagation()}>
                        {ev.correlation_id && (
                          <button
                            type="button"
                            onClick={() => onSelectCorrelation(ev.correlation_id!)}
                            title="Trace Correlation Lineage"
                            aria-label="Trace correlation lineage"
                            style={{
                              ...secondaryButtonBase,
                              minHeight: "28px",
                              padding: "4px 8px",
                              fontSize: "0.72rem",
                              display: "flex",
                              alignItems: "center",
                              gap: "4px",
                            }}
                          >
                            <GitCommit size={13} color={tokens.primaryAccent} />
                            <span>Trace</span>
                          </button>
                        )}

                        <button
                          type="button"
                          onClick={() => onSelectEvent(ev)}
                          title="Inspect Event Details"
                          aria-label="Inspect event details"
                          style={{
                            ...secondaryButtonBase,
                            minHeight: "28px",
                            padding: "4px 8px",
                            fontSize: "0.72rem",
                            display: "flex",
                            alignItems: "center",
                            gap: "4px",
                          }}
                        >
                          <Eye size={13} />
                          <span>Inspect</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div
        style={{
          padding: "12px 16px",
          borderTop: `1px solid ${tokens.border}`,
          backgroundColor: "#F8FAFC",
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "12px",
          fontSize: "0.78rem",
          color: tokens.textSecondary,
        }}
      >
        {/* Count info */}
        <div>
          Showing <span style={{ fontWeight: 600, color: tokens.textPrimary }}>{total === 0 ? 0 : (page - 1) * pageSize + 1}</span> to{" "}
          <span style={{ fontWeight: 600, color: tokens.textPrimary }}>{Math.min(page * pageSize, total)}</span> of{" "}
          <span style={{ fontWeight: 600, color: tokens.textPrimary }}>{total.toLocaleString()}</span> entries
        </div>

        {/* Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {/* Page size selector */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ fontSize: "0.72rem", color: tokens.textMuted }}>Per page:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              aria-label="Select page size"
              style={{
                height: "30px",
                padding: "2px 8px",
                fontSize: "0.78rem",
                borderRadius: "4px",
                border: `1px solid ${tokens.border}`,
                backgroundColor: "#FFFFFF",
              }}
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          {/* Nav buttons */}
          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <button
              type="button"
              disabled={page <= 1 || loading}
              onClick={() => onPageChange(1)}
              aria-label="First page"
              style={{
                ...secondaryButtonBase,
                minHeight: "30px",
                padding: "4px 8px",
                opacity: page <= 1 ? 0.5 : 1,
              }}
            >
              <ChevronsLeft size={14} />
            </button>
            <button
              type="button"
              disabled={page <= 1 || loading}
              onClick={() => onPageChange(page - 1)}
              aria-label="Previous page"
              style={{
                ...secondaryButtonBase,
                minHeight: "30px",
                padding: "4px 8px",
                opacity: page <= 1 ? 0.5 : 1,
              }}
            >
              <ChevronLeft size={14} />
            </button>

            <span style={{ padding: "0 8px", fontWeight: 600, color: tokens.textPrimary }}>
              Page {page} of {totalPages}
            </span>

            <button
              type="button"
              disabled={page >= totalPages || loading}
              onClick={() => onPageChange(page + 1)}
              aria-label="Next page"
              style={{
                ...secondaryButtonBase,
                minHeight: "30px",
                padding: "4px 8px",
                opacity: page >= totalPages ? 0.5 : 1,
              }}
            >
              <ChevronRight size={14} />
            </button>
            <button
              type="button"
              disabled={page >= totalPages || loading}
              onClick={() => onPageChange(totalPages)}
              aria-label="Last page"
              style={{
                ...secondaryButtonBase,
                minHeight: "30px",
                padding: "4px 8px",
                opacity: page >= totalPages ? 0.5 : 1,
              }}
            >
              <ChevronsRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
