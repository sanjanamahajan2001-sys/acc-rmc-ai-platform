import React from "react";
import { BarChart3, Info } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { StrengthDistributionDTO } from "../../../services/reportingService";

interface StrengthDistributionChartProps {
  data: StrengthDistributionDTO | null;
  isLoading: boolean;
}

export const StrengthDistributionChart: React.FC<StrengthDistributionChartProps> = ({
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
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>Loading strength distribution...</span>
      </div>
    );
  }

  const bins = data?.histogram_bins || [];
  const hasData = bins.length > 0 && (data?.total_tested_batches ?? 0) > 0;
  const maxCount = hasData ? Math.max(...bins.map((b) => b.count), 1) : 1;
  const fck = data?.characteristic_strength_fck_mpa ?? null;

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
      {/* Card Header */}
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
            <BarChart3 size={18} color={tokens.primaryAccent} />
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
              28-Day Strength Distribution Histogram
            </h3>
          </div>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.78rem", color: tokens.textMuted }}>
            Frequency distribution of batch compressive strength breaks (2.5 MPa intervals)
          </p>
        </div>

        {/* Threshold Legend */}
        {hasData && (
          <div style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "0.75rem", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "2px", backgroundColor: "#3B82F6" }} />
              <span style={{ color: tokens.textSecondary }}>Meeting Spec</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "2px", backgroundColor: "#EF4444" }} />
              <span style={{ color: tokens.textSecondary }}>Below fck</span>
            </div>
            {fck !== null && (
              <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                <div style={{ width: "12px", height: "2px", backgroundColor: "#DC2626" }} />
                <span style={{ fontWeight: 600, color: "#DC2626" }}>fck ({fck.toFixed(0)})</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chart Area */}
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
            No 28-day specimen results available
          </div>
          <div style={{ fontSize: "0.75rem", color: tokens.textMuted, marginTop: "4px" }}>
            Awaiting completed laboratory breaks for selected plant and period scope.
          </div>
        </div>
      ) : (
        <div className="dashboard-contained-scroll" style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
          <div style={{ minWidth: `${Math.max(bins.length * 28, 300)}px` }}>
            {/* Histogram Bars Container */}
            <div
              style={{
                display: "flex",
                alignItems: "flex-end",
                gap: "4px",
                height: "190px",
                paddingBottom: "8px",
                borderBottom: `1px solid ${tokens.borderLight}`,
              }}
            >
              {bins.map((bin, idx) => {
                const heightPct = Math.max((bin.count / maxCount) * 100, 4);
                const barColor = bin.is_below_fck ? "#EF4444" : "#3B82F6";

                return (
                  <div
                    key={idx}
                    style={{
                      flex: 1,
                      minWidth: "16px",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      height: "100%",
                      justifyContent: "flex-end",
                    }}
                    title={`${bin.bin_label} MPa: ${bin.count} batches (${bin.is_below_fck ? "Below Requirement" : "Compliant"})`}
                  >
                    <span
                      style={{
                        fontSize: "0.68rem",
                        fontWeight: 700,
                        color: bin.count > 0 ? tokens.textPrimary : "transparent",
                        marginBottom: "4px",
                      }}
                    >
                      {bin.count > 0 ? bin.count : ""}
                    </span>

                    <div
                      style={{
                        width: "100%",
                        height: `${heightPct}%`,
                        backgroundColor: barColor,
                        borderRadius: "4px 4px 0 0",
                        transition: "height 0.3s ease",
                        cursor: "pointer",
                      }}
                    />
                  </div>
                );
              })}
            </div>

            {/* X-Axis Labels */}
            <div style={{ display: "flex", gap: "4px", marginTop: "6px" }}>
              {bins.map((bin, idx) => (
                <div
                  key={idx}
                  style={{
                    flex: 1,
                    minWidth: "16px",
                    textAlign: "center",
                    fontSize: "0.65rem",
                    color: bin.is_below_fck ? "#DC2626" : tokens.textMuted,
                    fontWeight: bin.is_below_fck ? 600 : 400,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {bin.bin_start}
                </div>
              ))}
            </div>
            <div style={{ textAlign: "center", fontSize: "0.72rem", color: tokens.textMuted, marginTop: "4px" }}>
              Compressive Strength Interval (MPa)
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
