import React from "react";
import { Droplets, Info, AlertTriangle, Scale, Gauge } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { BatchVarianceAnalysisDTO, BinderEfficiencyDTO } from "../../../services/reportingService";

interface WaterCementRatioChartProps {
  varianceData: BatchVarianceAnalysisDTO | null;
  efficiencyData: BinderEfficiencyDTO | null;
  isLoading: boolean;
}

export const WaterCementRatioChart: React.FC<WaterCementRatioChartProps> = ({
  varianceData,
  efficiencyData,
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
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>Loading water & W/B ratio telemetry...</span>
      </div>
    );
  }

  const waterAnalysis = varianceData?.water_moisture_analysis;
  const fleetSummary = efficiencyData?.fleet_summary;

  const fleetWb = fleetSummary?.fleet_avg_actual_wb;
  const fleetWc = fleetSummary?.fleet_avg_actual_wc;
  const plannedWater = waterAnalysis?.planned_water_kg ?? 0;
  const actualWater = waterAnalysis?.actual_water_kg ?? 0;
  const rawVarianceKg = waterAnalysis?.raw_water_variance_kg ?? 0;
  const rawVariancePct = waterAnalysis?.raw_water_variance_pct ?? 0;
  const dataQualityStatus = waterAnalysis?.data_quality_status || "LIMITED";
  const operationalNote =
    waterAnalysis?.operational_note ||
    "Raw water variance reflects scale delivery and operational moisture compensation; moisture-corrected target unavailable.";

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
        boxSizing: "border-box",
        minWidth: 0,
        height: "100%",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <Droplets size={18} color="#0284C7" />
          <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
            Water & Water-to-Binder (W/B) Ratio Monitoring
          </h3>
        </div>
        <p style={{ margin: "4px 0 0 0", fontSize: "0.78rem", color: tokens.textMuted }}>
          Authoritative batch scale delivery, Water/Binder ratio, and moisture compensation disclosures
        </p>
      </div>

      {/* Primary & Secondary Ratio Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "12px",
          marginBottom: "16px",
        }}
      >
        {/* Primary Metric: W/B */}
        <div
          style={{
            padding: "14px",
            backgroundColor: "#F0F9FF",
            borderRadius: "8px",
            border: "1px solid #BAE6FD",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
            <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#0369A1", textTransform: "uppercase" }}>
              Water-to-Binder (W/B)
            </div>
            <span
              style={{
                fontSize: "0.62rem",
                fontWeight: 700,
                padding: "1px 6px",
                borderRadius: "4px",
                backgroundColor: "#E0F2FE",
                color: "#0369A1",
                border: "1px solid #BAE6FD",
              }}
            >
              Primary
            </span>
          </div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#0C4A6E", lineHeight: 1.1 }}>
            {fleetWb != null ? fleetWb.toFixed(3) : "—"}
          </div>
          <div style={{ fontSize: "0.7rem", color: "#0369A1", marginTop: "4px" }}>
            Water / (Cement + GGBS + Fly Ash + Silica Fume)
          </div>
        </div>

        {/* Secondary Metric: W/C */}
        <div
          style={{
            padding: "14px",
            backgroundColor: "#F8FAFC",
            borderRadius: "8px",
            border: `1px solid ${tokens.borderLight}`,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
            <div style={{ fontSize: "0.72rem", fontWeight: 700, color: tokens.textSecondary, textTransform: "uppercase" }}>
              Water-to-Cement (W/C)
            </div>
            <span
              style={{
                fontSize: "0.62rem",
                fontWeight: 600,
                padding: "1px 6px",
                borderRadius: "4px",
                backgroundColor: "#F1F5F9",
                color: tokens.textMuted,
                border: `1px solid ${tokens.border}`,
              }}
            >
              Secondary
            </span>
          </div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: tokens.textPrimary, lineHeight: 1.1 }}>
            {fleetWc != null ? fleetWc.toFixed(3) : "—"}
          </div>
          <div style={{ fontSize: "0.7rem", color: tokens.textMuted, marginTop: "4px" }}>
            Water / Pure OPC/PPC Cement
          </div>
        </div>
      </div>

      {/* Raw Water Scale Delivery Telemetry */}
      <div
        style={{
          padding: "12px 14px",
          backgroundColor: "#FBFCFE",
          borderRadius: "8px",
          border: `1px solid ${tokens.borderLight}`,
          marginBottom: "14px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
          <Scale size={15} color={tokens.textSecondary} />
          <span style={{ fontSize: "0.78rem", fontWeight: 700, color: tokens.textPrimary }}>
            Batch Scale Water Delivery
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px", fontSize: "0.75rem" }}>
          <div>
            <div style={{ color: tokens.textMuted }}>Planned Target</div>
            <div style={{ fontWeight: 700, color: tokens.textPrimary }}>
              {plannedWater.toLocaleString(undefined, { maximumFractionDigits: 1 })} kg
            </div>
          </div>
          <div>
            <div style={{ color: tokens.textMuted }}>Actual Delivered</div>
            <div style={{ fontWeight: 700, color: tokens.textPrimary }}>
              {actualWater.toLocaleString(undefined, { maximumFractionDigits: 1 })} kg
            </div>
          </div>
          <div>
            <div style={{ color: tokens.textMuted }}>Raw Scale Variance</div>
            <div
              style={{
                fontWeight: 700,
                color: rawVariancePct >= 0 ? tokens.warningAmber : "#2563EB",
              }}
            >
              {rawVariancePct >= 0 ? "+" : ""}{rawVariancePct.toFixed(2)}% ({rawVarianceKg >= 0 ? "+" : ""}{rawVarianceKg.toFixed(1)} kg)
            </div>
          </div>
        </div>
      </div>

      {/* Moisture Telemetry Limitation Disclosure */}
      <div
        style={{
          marginTop: "auto",
          padding: "10px 12px",
          backgroundColor: dataQualityStatus === "LIMITED" ? "#FFFBEB" : "#F0FDF4",
          border: `1px solid ${dataQualityStatus === "LIMITED" ? "#FDE68A" : "#BBF7D0"}`,
          borderRadius: "6px",
          display: "flex",
          alignItems: "flex-start",
          gap: "8px",
        }}
      >
        <AlertTriangle
          size={16}
          color={dataQualityStatus === "LIMITED" ? tokens.warningAmber : tokens.successGreen}
          style={{ flexShrink: 0, marginTop: "1px" }}
        />
        <div style={{ fontSize: "0.72rem", color: dataQualityStatus === "LIMITED" ? "#92400E" : "#166534", lineHeight: 1.4 }}>
          <strong>Moisture Telemetry: {dataQualityStatus}</strong> — {operationalNote}
        </div>
      </div>
    </div>
  );
};
