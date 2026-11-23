import React from "react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { StrengthDistributionDTO } from "../../../services/reportingService";
import {
  PressureGaugeIcon,
  TargetAccuracyIcon,
  StrengthMarginIcon,
  BatchVariationIcon,
  LabCubeCheckIcon,
} from "../../icons";

interface StatisticalSummaryCardsProps {
  data: StrengthDistributionDTO | null;
  isLoading: boolean;
}

export const StatisticalSummaryCards: React.FC<StatisticalSummaryCardsProps> = ({
  data,
  isLoading,
}) => {
  const cardStyle: React.CSSProperties = {
    padding: "16px 18px",
    backgroundColor: "#FFFFFF",
    borderRadius: "10px",
    border: `1px solid ${tokens.borderLight}`,
    boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.02)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    boxSizing: "border-box",
    minWidth: 0,
  };

  if (isLoading) {
    return (
      <div className="dashboard-sqc-summary-grid">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} style={{ ...cardStyle, minHeight: "105px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
              <div style={{ height: "12px", width: "80px", backgroundColor: "#E2E8F0", borderRadius: "4px" }} />
              <div style={{ height: "16px", width: "16px", backgroundColor: "#E2E8F0", borderRadius: "4px" }} />
            </div>
            <div style={{ height: "24px", width: "90px", backgroundColor: "#E2E8F0", borderRadius: "4px", marginBottom: "6px" }} />
            <div style={{ height: "10px", width: "110px", backgroundColor: "#F1F5F9", borderRadius: "4px" }} />
          </div>
        ))}
      </div>
    );
  }

  const hasData = Boolean(data && data.total_tested_batches > 0);

  const getStabilityBadge = (grade?: string) => {
    switch (grade) {
      case "EXCELLENT":
        return { label: "EXCELLENT", bg: "#ECFDF5", text: "#059669", border: "#A7F3D0" };
      case "GOOD":
      case "MODERATE":
        return { label: "CONTROLLED", bg: "#EFF6FF", text: "#2563EB", border: "#BFDBFE" };
      case "HIGH_VARIATION":
        return { label: "HIGH VARIATION", bg: "#FEF2F2", text: "#DC2626", border: "#FECACA" };
      default:
        return { label: "LIMITED DATA", bg: "#F8FAFC", text: "#64748B", border: "#E2E8F0" };
    }
  };

  const stability = getStabilityBadge(data?.stability_grade);
  const marginVal = data?.strength_margin_mpa ?? null;
  const meanVal = data?.mean_strength_mpa ?? null;
  const stdVal = data?.standard_deviation_mpa ?? null;
  const cvVal = data?.coefficient_of_variation_pct ?? null;

  return (
    <div className="dashboard-sqc-summary-grid">
      {/* 1. Mean 28-Day Strength */}
      <div style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.72rem", fontWeight: 700, color: tokens.textMuted, textTransform: "uppercase", letterSpacing: "0.04em" }}>
            28-Day Mean Strength
          </span>
          <PressureGaugeIcon size={18} />
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
          <span style={{ fontSize: "1.65rem", fontWeight: 700, color: tokens.textPrimary }}>
            {hasData && meanVal !== null ? meanVal.toFixed(1) : "—"}
          </span>
          <span style={{ fontSize: "0.82rem", fontWeight: 600, color: tokens.textMuted }}>MPa</span>
        </div>
        <div style={{ fontSize: "0.72rem", color: tokens.textMuted, marginTop: "6px" }}>
          {hasData && data?.median_strength_mpa != null ? `Median: ${data.median_strength_mpa.toFixed(1)} MPa` : "Awaiting lab breaks"}
        </div>
      </div>

      {/* 2. Target Characteristic Strength */}
      <div style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.72rem", fontWeight: 700, color: tokens.textMuted, textTransform: "uppercase", letterSpacing: "0.04em" }}>
            Target Strength
          </span>
          <TargetAccuracyIcon size={18} />
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
          <span style={{ fontSize: "1.65rem", fontWeight: 700, color: tokens.textPrimary }}>
            {hasData && data?.characteristic_strength_fck_mpa != null ? data.characteristic_strength_fck_mpa.toFixed(1) : "—"}
          </span>
          <span style={{ fontSize: "0.82rem", fontWeight: 600, color: tokens.textMuted }}>MPa (fck)</span>
        </div>
        <div style={{ fontSize: "0.72rem", color: tokens.textMuted, marginTop: "6px" }}>
          {hasData && data?.target_mean_strength_fck_prime_mpa != null ? `Design Target (f'ck): ${data.target_mean_strength_fck_prime_mpa.toFixed(1)} MPa` : "IS 456 specified grade"}
        </div>
      </div>

      {/* 3. Strength Margin */}
      <div style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.72rem", fontWeight: 700, color: tokens.textMuted, textTransform: "uppercase", letterSpacing: "0.04em" }}>
            Strength Margin
          </span>
          <StrengthMarginIcon size={18} />
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
          <span
            style={{
              fontSize: "1.65rem",
              fontWeight: 700,
              color: (marginVal ?? 0) >= 0 ? "#059669" : "#DC2626",
            }}
          >
            {hasData && marginVal !== null ? `${marginVal >= 0 ? "+" : ""}${marginVal.toFixed(1)}` : "—"}
          </span>
          <span style={{ fontSize: "0.82rem", fontWeight: 600, color: tokens.textMuted }}>MPa</span>
        </div>
        <div style={{ fontSize: "0.72rem", color: tokens.textMuted, marginTop: "6px" }}>
          {hasData ? "Margin over characteristic fck" : "Awaiting test data"}
        </div>
      </div>

      {/* 4. Batch Variation */}
      <div style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.72rem", fontWeight: 700, color: tokens.textMuted, textTransform: "uppercase", letterSpacing: "0.04em" }}>
            Batch Variation
          </span>
          <BatchVariationIcon size={18} />
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
          <span style={{ fontSize: "1.65rem", fontWeight: 700, color: tokens.textPrimary }}>
            {hasData && stdVal !== null ? `±${stdVal.toFixed(1)}` : "—"}
          </span>
          <span style={{ fontSize: "0.82rem", fontWeight: 600, color: tokens.textMuted }}>MPa (σ)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "6px", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.72rem", color: tokens.textMuted }}>
            {hasData && cvVal !== null ? `CV: ${cvVal.toFixed(1)}%` : "—"}
          </span>
          {hasData && (
            <span
              style={{
                fontSize: "0.65rem",
                fontWeight: 700,
                padding: "2px 6px",
                borderRadius: "4px",
                backgroundColor: stability.bg,
                color: stability.text,
                border: `1px solid ${stability.border}`,
              }}
            >
              {stability.label}
            </span>
          )}
        </div>
      </div>

      {/* 5. Tested Batches */}
      <div style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.72rem", fontWeight: 700, color: tokens.textMuted, textTransform: "uppercase", letterSpacing: "0.04em" }}>
            Tested Batches
          </span>
          <LabCubeCheckIcon size={18} />
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
          <span style={{ fontSize: "1.65rem", fontWeight: 700, color: tokens.textPrimary }}>
            {data ? data.total_tested_batches.toLocaleString() : "0"}
          </span>
          <span style={{ fontSize: "0.82rem", fontWeight: 600, color: tokens.textMuted }}>batches</span>
        </div>
        <div style={{ fontSize: "0.72rem", color: tokens.textMuted, marginTop: "6px" }}>
          {data ? `${data.total_tested_specimens.toLocaleString()} cube specimens broken` : "0 specimens"}
        </div>
      </div>
    </div>
  );
};
