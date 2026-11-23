import React from "react";
import { LineChart, Clock, Info } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { StrengthTimelineListDTO } from "../../../services/reportingService";

interface StrengthTrendTimelineProps {
  data: StrengthTimelineListDTO | null;
  isLoading: boolean;
}

export const StrengthTrendTimeline: React.FC<StrengthTrendTimelineProps> = ({
  data,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div
        style={{
          padding: "24px",
          backgroundColor: "#FFFFFF",
          borderRadius: "10px",
          border: `1px solid ${tokens.borderLight}`,
          height: "320px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>Loading strength trend timeline...</span>
      </div>
    );
  }

  const timeline = data?.timeline || [];
  const hasData = timeline.length > 0;

  return (
    <div
      style={{
        padding: "20px 24px",
        backgroundColor: "#FFFFFF",
        borderRadius: "10px",
        border: `1px solid ${tokens.borderLight}`,
        boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.02)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        boxSizing: "border-box",
        minWidth: 0,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "16px",
          flexWrap: "wrap",
          gap: "10px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <LineChart size={18} color={tokens.primaryAccent} />
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
              Recent Batch Strength Progression (Last 50 Batches)
            </h3>
          </div>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.78rem", color: tokens.textMuted }}>
            Chronological 7-day and 28-day break tests for recent production batches
          </p>
        </div>

        {/* Legend */}
        {hasData && (
          <div style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "0.75rem", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#3B82F6" }} />
              <span style={{ color: tokens.textSecondary }}>28-Day Break</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#94A3B8" }} />
              <span style={{ color: tokens.textSecondary }}>7-Day Break</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <Clock size={12} color="#D97706" />
              <span style={{ color: tokens.textMuted }}>Curing (Pending)</span>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      {!hasData ? (
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#F8FAFC",
            borderRadius: "8px",
            border: `1px dashed ${tokens.border}`,
            padding: "30px",
            minHeight: "220px",
          }}
        >
          <Info size={28} color={tokens.textMuted} style={{ marginBottom: "8px" }} />
          <div style={{ fontSize: "0.85rem", fontWeight: 600, color: tokens.textSecondary }}>
            No recent batches recorded
          </div>
          <div style={{ fontSize: "0.75rem", color: tokens.textMuted, marginTop: "4px" }}>
            Production batches will appear chronologically as they are submitted or ingested.
          </div>
        </div>
      ) : (
        <div className="dashboard-contained-scroll" style={{ flex: 1, maxHeight: "280px" }}>
          <table className="dashboard-timeline-table">
            <thead>
              <tr style={{ borderBottom: `1px solid ${tokens.borderLight}`, textAlign: "left" }}>
                <th style={{ padding: "8px 10px", color: tokens.textMuted, fontWeight: 700 }}>Batch #</th>
                <th style={{ padding: "8px 10px", color: tokens.textMuted, fontWeight: 700 }}>Mix / Grade</th>
                <th style={{ padding: "8px 10px", color: tokens.textMuted, fontWeight: 700, textAlign: "right" }}>7-Day</th>
                <th style={{ padding: "8px 10px", color: tokens.textMuted, fontWeight: 700, textAlign: "right" }}>28-Day</th>
                <th style={{ padding: "8px 10px", color: tokens.textMuted, fontWeight: 700, textAlign: "right" }}>Target (fck)</th>
                <th style={{ padding: "8px 10px", color: tokens.textMuted, fontWeight: 700, textAlign: "center" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {timeline.map((pt) => {
                const has28d = pt.result_28d_mpa != null;
                const isPass = pt.is_compliant_28d === true;

                return (
                  <tr key={pt.batch_number} style={{ borderBottom: `1px solid ${tokens.borderLight}` }}>
                    <td style={{ padding: "8px 10px", fontWeight: 600, color: tokens.textPrimary }}>
                      {pt.batch_number}
                    </td>
                    <td style={{ padding: "8px 10px", color: tokens.textSecondary }}>
                      {pt.recipe_code} ({pt.grade})
                    </td>
                    <td style={{ padding: "8px 10px", textAlign: "right", color: pt.result_7d_mpa ? tokens.textSecondary : tokens.textMuted }}>
                      {pt.result_7d_mpa != null ? `${pt.result_7d_mpa.toFixed(1)} MPa` : "—"}
                    </td>
                    <td style={{ padding: "8px 10px", textAlign: "right", fontWeight: 700, color: has28d ? (isPass ? "#059669" : "#DC2626") : tokens.textMuted }}>
                      {has28d ? `${pt.result_28d_mpa!.toFixed(1)} MPa` : "Pending 28D"}
                    </td>
                    <td style={{ padding: "8px 10px", textAlign: "right", color: tokens.textMuted }}>
                      {pt.target_fck_mpa.toFixed(0)} MPa
                    </td>
                    <td style={{ padding: "8px 10px", textAlign: "center" }}>
                      {!has28d ? (
                        <span style={{ fontSize: "0.68rem", color: "#D97706", backgroundColor: "#FFFBEB", padding: "2px 6px", borderRadius: "4px" }}>
                          Curing
                        </span>
                      ) : isPass ? (
                        <span style={{ fontSize: "0.68rem", color: "#059669", backgroundColor: "#ECFDF5", padding: "2px 6px", borderRadius: "4px" }}>
                          Pass
                        </span>
                      ) : (
                        <span style={{ fontSize: "0.68rem", color: "#DC2626", backgroundColor: "#FEF2F2", padding: "2px 6px", borderRadius: "4px" }}>
                          Low Break
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
