import React from "react";
import { Shield, CheckCircle2, AlertTriangle, XCircle, Clock } from "lucide-react";
import { AuditMetrics } from "../../types/audit";
import { enterpriseLightTokens as tokens } from "../manual-entry/enterpriseLightTokens";

interface AuditMetricsCardsProps {
  metrics: AuditMetrics | null;
  loading: boolean;
}

export const AuditMetricsCards: React.FC<AuditMetricsCardsProps> = ({ metrics, loading }) => {
  const cardBaseStyle: React.CSSProperties = {
    backgroundColor: tokens.surfacePrimary,
    border: `1px solid ${tokens.border}`,
    borderRadius: "8px",
    padding: "16px 18px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    minWidth: "180px",
    flex: "1 1 200px",
  };

  const skeletonStyle: React.CSSProperties = {
    height: "24px",
    width: "60px",
    backgroundColor: "#E2E8F0",
    borderRadius: "4px",
    animation: "pulse 1.5s infinite ease-in-out",
  };

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "14px", marginBottom: "20px" }}>
      {/* Total Audit Events */}
      <div style={cardBaseStyle}>
        <div>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, color: tokens.textMuted, textTransform: "uppercase" }}>
            Total Audit Events
          </div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: tokens.textPrimary, marginTop: "4px" }}>
            {loading ? <div style={skeletonStyle} /> : (metrics?.total_events.toLocaleString() ?? "0")}
          </div>
        </div>
        <div style={{ padding: "10px", borderRadius: "8px", backgroundColor: tokens.primaryAccentLight, color: tokens.primaryAccent }}>
          <Shield size={22} />
        </div>
      </div>

      {/* Successful Operations */}
      <div style={cardBaseStyle}>
        <div>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, color: tokens.textMuted, textTransform: "uppercase" }}>
            Successful Actions
          </div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#166534", marginTop: "4px" }}>
            {loading ? <div style={skeletonStyle} /> : (metrics?.successful_events.toLocaleString() ?? "0")}
          </div>
        </div>
        <div style={{ padding: "10px", borderRadius: "8px", backgroundColor: "#DCFCE7", color: "#166534" }}>
          <CheckCircle2 size={22} />
        </div>
      </div>

      {/* Failed Operations */}
      <div style={cardBaseStyle}>
        <div>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, color: tokens.textMuted, textTransform: "uppercase" }}>
            Failed Operations
          </div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#9A3412", marginTop: "4px" }}>
            {loading ? <div style={skeletonStyle} /> : (metrics?.failed_events.toLocaleString() ?? "0")}
          </div>
        </div>
        <div style={{ padding: "10px", borderRadius: "8px", backgroundColor: "#FFEDD5", color: "#9A3412" }}>
          <AlertTriangle size={22} />
        </div>
      </div>

      {/* Denied / Security Alerts */}
      <div style={cardBaseStyle}>
        <div>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, color: tokens.textMuted, textTransform: "uppercase" }}>
            Security Denials
          </div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#991B1B", marginTop: "4px" }}>
            {loading ? <div style={skeletonStyle} /> : (metrics?.denied_events.toLocaleString() ?? "0")}
          </div>
        </div>
        <div style={{ padding: "10px", borderRadius: "8px", backgroundColor: "#FEE2E2", color: "#991B1B" }}>
          <XCircle size={22} />
        </div>
      </div>

      {/* Events Last 24 Hours */}
      <div style={cardBaseStyle}>
        <div>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, color: tokens.textMuted, textTransform: "uppercase" }}>
            Activity (Last 24h)
          </div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: tokens.textPrimary, marginTop: "4px" }}>
            {loading ? <div style={skeletonStyle} /> : (metrics?.events_last_24h.toLocaleString() ?? "0")}
          </div>
        </div>
        <div style={{ padding: "10px", borderRadius: "8px", backgroundColor: "#F1F5F9", color: "#475569" }}>
          <Clock size={22} />
        </div>
      </div>
    </div>
  );
};
