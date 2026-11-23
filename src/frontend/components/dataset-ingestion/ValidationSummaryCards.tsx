/**
 * Modular Vite Component: Validation Summary Cards & Statistics.
 */

import React from "react";
import { PreviewStatisticsDTO } from "../../types/validationContracts";

interface ValidationSummaryCardsProps {
  statistics: PreviewStatisticsDTO;
}

export const ValidationSummaryCards: React.FC<ValidationSummaryCardsProps> = ({ statistics }) => {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "16px",
        marginBottom: "24px",
      }}
    >
      {/* Quality Score Card */}
      <div
        style={{
          padding: "18px",
          backgroundColor: "rgba(20, 24, 35, 0.7)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "12px",
          backdropFilter: "blur(12px)",
        }}
      >
        <div style={{ fontSize: "0.8rem", color: "#9ca3af", fontWeight: 600 }}>Quality Score</div>
        <div style={{ fontSize: "1.8rem", fontWeight: 800, color: statistics.overall_quality_score >= 90 ? "#00ff87" : "#f59e0b", marginTop: "4px" }}>
          {statistics.overall_quality_score.toFixed(1)}%
        </div>
        <div style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: "4px" }}>WS-03.3 Multi-Tier Assessment</div>
      </div>

      {/* Evaluated Rows */}
      <div
        style={{
          padding: "18px",
          backgroundColor: "rgba(20, 24, 35, 0.7)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "12px",
          backdropFilter: "blur(12px)",
        }}
      >
        <div style={{ fontSize: "0.8rem", color: "#9ca3af", fontWeight: 600 }}>Total Rows Evaluated</div>
        <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#ffffff", marginTop: "4px" }}>
          {statistics.total_rows_evaluated.toLocaleString()}
        </div>
        <div style={{ fontSize: "0.75rem", color: "#00e5ff", marginTop: "4px" }}>100% Validated</div>
      </div>

      {/* Valid Rows */}
      <div
        style={{
          padding: "18px",
          backgroundColor: "rgba(20, 24, 35, 0.7)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "12px",
          backdropFilter: "blur(12px)",
        }}
      >
        <div style={{ fontSize: "0.8rem", color: "#9ca3af", fontWeight: 600 }}>Valid Rows</div>
        <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#00ff87", marginTop: "4px" }}>
          {statistics.valid_rows_count.toLocaleString()}
        </div>
        <div style={{ fontSize: "0.75rem", color: "#00ff87", marginTop: "4px" }}>Ready for Persistence</div>
      </div>

      {/* Quarantined Rows */}
      <div
        style={{
          padding: "18px",
          backgroundColor: "rgba(20, 24, 35, 0.7)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "12px",
          backdropFilter: "blur(12px)",
        }}
      >
        <div style={{ fontSize: "0.8rem", color: "#9ca3af", fontWeight: 600 }}>Quarantined Rows</div>
        <div style={{ fontSize: "1.8rem", fontWeight: 800, color: statistics.quarantined_rows_count > 0 ? "#ef4444" : "#00ff87", marginTop: "4px" }}>
          {statistics.quarantined_rows_count.toLocaleString()}
        </div>
        <div style={{ fontSize: "0.75rem", color: statistics.quarantined_rows_count > 0 ? "#ef4444" : "#9ca3af", marginTop: "4px" }}>
          {statistics.quarantined_rows_count > 0 ? "Requires Review" : "0 Critical Errors"}
        </div>
      </div>
    </div>
  );
};
