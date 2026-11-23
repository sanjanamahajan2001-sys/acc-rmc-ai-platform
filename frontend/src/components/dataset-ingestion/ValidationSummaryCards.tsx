/**
 * Modular Vite Component: Validation Summary Cards & Statistics.
 * Enterprise Operations Light Theme Migration.
 */

import React from "react";
import { PreviewStatisticsDTO } from "../../types/validationContracts";
import { enterpriseLightTokens as tokens } from "../manual-entry/enterpriseLightTokens";

interface ValidationSummaryCardsProps {
  statistics: PreviewStatisticsDTO;
}

export const ValidationSummaryCards: React.FC<ValidationSummaryCardsProps> = ({ statistics }) => {
  const cardStyle: React.CSSProperties = {
    padding: "16px",
    backgroundColor: tokens.surfacePrimary,
    border: `1px solid ${tokens.border}`,
    borderRadius: "8px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
  };

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "14px",
        marginBottom: "20px",
      }}
    >
      {/* Quality Score Card */}
      <div style={cardStyle}>
        <div style={{ fontSize: "0.75rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Quality Score</div>
        <div
          style={{
            fontSize: "1.7rem",
            fontWeight: 700,
            color: statistics.overall_quality_score >= 90 ? tokens.statusSuccessText : tokens.statusWarningText,
            marginTop: "4px",
          }}
        >
          {statistics.overall_quality_score.toFixed(1)}%
        </div>
        <div style={{ fontSize: "0.72rem", color: tokens.textMuted, marginTop: "2px" }}>WS-03.3 Multi-Tier Assessment</div>
      </div>

      {/* Evaluated Rows */}
      <div style={cardStyle}>
        <div style={{ fontSize: "0.75rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Total Rows Evaluated</div>
        <div style={{ fontSize: "1.7rem", fontWeight: 700, color: tokens.textPrimary, marginTop: "4px" }}>
          {statistics.total_rows_evaluated.toLocaleString()}
        </div>
        <div style={{ fontSize: "0.72rem", color: tokens.accent, marginTop: "2px", fontWeight: 600 }}>100% Validated</div>
      </div>

      {/* Valid Rows */}
      <div style={cardStyle}>
        <div style={{ fontSize: "0.75rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Valid Rows</div>
        <div style={{ fontSize: "1.7rem", fontWeight: 700, color: tokens.statusSuccessText, marginTop: "4px" }}>
          {statistics.valid_rows_count.toLocaleString()}
        </div>
        <div style={{ fontSize: "0.72rem", color: tokens.statusSuccessText, marginTop: "2px", fontWeight: 600 }}>Ready for Persistence</div>
      </div>

      {/* Quarantined Rows */}
      <div style={cardStyle}>
        <div style={{ fontSize: "0.75rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Quarantined Rows</div>
        <div
          style={{
            fontSize: "1.7rem",
            fontWeight: 700,
            color: statistics.quarantined_rows_count > 0 ? tokens.statusErrorText : tokens.statusSuccessText,
            marginTop: "4px",
          }}
        >
          {statistics.quarantined_rows_count.toLocaleString()}
        </div>
        <div
          style={{
            fontSize: "0.72rem",
            color: statistics.quarantined_rows_count > 0 ? tokens.statusErrorText : tokens.textMuted,
            marginTop: "2px",
            fontWeight: statistics.quarantined_rows_count > 0 ? 600 : 400,
          }}
        >
          {statistics.quarantined_rows_count > 0 ? "Requires Review" : "0 Critical Errors"}
        </div>
      </div>
    </div>
  );
};
