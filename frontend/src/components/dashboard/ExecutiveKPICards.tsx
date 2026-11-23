import React from "react";
import { OperationalMetricsDTO } from "../../services/reportingService";
import { enterpriseLightTokens as tokens } from "../manual-entry/enterpriseLightTokens";
import { MixerTruckIcon, BatchMixerIcon, BatchPlantIcon, QualitySealIcon } from "../icons";

interface ExecutiveKPICardsProps {
  metrics?: OperationalMetricsDTO;
  isLoading: boolean;
  isError: boolean;
}

export const ExecutiveKPICards: React.FC<ExecutiveKPICardsProps> = ({
  metrics,
  isLoading,
  isError,
}) => {
  const cardBaseStyle: React.CSSProperties = {
    backgroundColor: tokens.surfacePrimary,
    borderRadius: "10px",
    border: `1px solid ${tokens.border}`,
    padding: "18px 20px",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.04)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    boxSizing: "border-box",
    minWidth: 0,
  };

  if (isLoading) {
    return (
      <div className="dashboard-kpi-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} style={{ ...cardBaseStyle, minHeight: "120px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
              <div style={{ height: "14px", width: "80px", backgroundColor: "#E2E8F0", borderRadius: "4px" }} />
              <div style={{ height: "28px", width: "28px", backgroundColor: "#E2E8F0", borderRadius: "6px" }} />
            </div>
            <div style={{ height: "26px", width: "120px", backgroundColor: "#E2E8F0", borderRadius: "4px", marginBottom: "8px" }} />
            <div style={{ height: "12px", width: "150px", backgroundColor: "#F1F5F9", borderRadius: "4px" }} />
          </div>
        ))}
      </div>
    );
  }

  if (isError || !metrics) {
    return (
      <div
        style={{
          padding: "16px 20px",
          backgroundColor: tokens.statusErrorBg,
          border: `1px solid ${tokens.statusErrorBorder}`,
          borderRadius: "8px",
          color: tokens.statusErrorText,
          fontSize: "0.84rem",
          marginBottom: "24px",
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <span>Authoritative KPI data is currently unavailable. Retrying in background...</span>
      </div>
    );
  }

  const volumeFormatted = Number(metrics.total_volume_m3 || 0).toLocaleString("en-IN", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });

  const batchesFormatted = Number(metrics.total_ingested_batches || 0).toLocaleString("en-IN");
  const complianceRate = metrics.quality_compliance_rate_pct ?? 100.0;

  return (
    <div className="dashboard-kpi-grid">
      {/* 1. Total Produced Volume */}
      <div style={cardBaseStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.78rem", fontWeight: 600, color: tokens.textSecondary, textTransform: "uppercase", letterSpacing: "0.03em" }}>
            Produced Concrete Volume
          </span>
          <div style={{ padding: "6px", backgroundColor: "#EFF6FF", borderRadius: "6px", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <MixerTruckIcon size={20} />
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: "6px", marginBottom: "6px" }}>
          <span style={{ fontSize: "1.75rem", fontWeight: 700, color: tokens.textPrimary, lineHeight: 1.1 }}>
            {volumeFormatted}
          </span>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: tokens.textMuted }}>m³</span>
        </div>
        <div style={{ fontSize: "0.74rem", color: tokens.textSecondary }}>
          From {batchesFormatted} verified production batches
        </div>
      </div>

      {/* 2. Total Batches Executed */}
      <div style={cardBaseStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.78rem", fontWeight: 600, color: tokens.textSecondary, textTransform: "uppercase", letterSpacing: "0.03em" }}>
            Total Production Batches
          </span>
          <div style={{ padding: "6px", backgroundColor: "#F0FDF4", borderRadius: "6px", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <BatchMixerIcon size={20} />
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: "6px", marginBottom: "6px" }}>
          <span style={{ fontSize: "1.75rem", fontWeight: 700, color: tokens.textPrimary, lineHeight: 1.1 }}>
            {batchesFormatted}
          </span>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: tokens.textMuted }}>batches</span>
        </div>
        <div style={{ fontSize: "0.74rem", color: tokens.textSecondary }}>
          {metrics.operational_batches_count} operational actuals
        </div>
      </div>

      {/* 3. Active Production Plants */}
      <div style={cardBaseStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.78rem", fontWeight: 600, color: tokens.textSecondary, textTransform: "uppercase", letterSpacing: "0.03em" }}>
            Active Plants
          </span>
          <div style={{ padding: "6px", backgroundColor: "#FAF5FF", borderRadius: "6px", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <BatchPlantIcon size={20} />
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: "6px", marginBottom: "6px" }}>
          <span style={{ fontSize: "1.75rem", fontWeight: 700, color: tokens.textPrimary, lineHeight: 1.1 }}>
            {metrics.active_plants_count}
          </span>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: tokens.textMuted }}>terminals</span>
        </div>
        <div style={{ fontSize: "0.74rem", color: tokens.textSecondary }}>
          Participating in selected scope
        </div>
      </div>

      {/* 4. Quality Compliance Rate */}
      <div style={cardBaseStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.78rem", fontWeight: 600, color: tokens.textSecondary, textTransform: "uppercase", letterSpacing: "0.03em" }}>
            Quality Compliance (IS 456)
          </span>
          <div style={{ padding: "6px", backgroundColor: complianceRate >= 95 ? "#F0FDF4" : "#FEF3C7", borderRadius: "6px", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <QualitySealIcon size={20} />
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: "6px", marginBottom: "6px", flexWrap: "wrap" }}>
          <span style={{ fontSize: "1.75rem", fontWeight: 700, color: tokens.textPrimary, lineHeight: 1.1 }}>
            {complianceRate.toFixed(1)}%
          </span>
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: complianceRate >= 95 ? tokens.statusSuccessText : tokens.statusWarningText }}>
            {complianceRate >= 95 ? "TARGET MET" : "REVIEW REQUIRED"}
          </span>
        </div>
        <div style={{ fontSize: "0.74rem", color: tokens.textSecondary }}>
          Based on {metrics.total_cube_tests} lab specimen break tests
        </div>
      </div>
    </div>
  );
};
