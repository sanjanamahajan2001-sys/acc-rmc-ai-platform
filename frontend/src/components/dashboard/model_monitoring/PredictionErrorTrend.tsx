import React, { useState } from "react";
import { TrendingUp, Info } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { PredictionErrorTrendResponseDTO, PredictionErrorTrendItemDTO } from "../../../services/reportingService";

interface PredictionErrorTrendProps {
  data?: PredictionErrorTrendResponseDTO | null;
  isLoading?: boolean;
}

export const PredictionErrorTrend: React.FC<PredictionErrorTrendProps> = ({
  data,
  isLoading = false,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<PredictionErrorTrendItemDTO | null>(null);

  if (isLoading) {
    return (
      <div
        style={{
          padding: "24px",
          backgroundColor: "#FFFFFF",
          borderRadius: "10px",
          border: `1px solid ${tokens.borderLight}`,
          height: "360px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>Loading error trend...</span>
      </div>
    );
  }

  const items = data?.items || [];
  const hasData = items.length > 0;
  const threshold = typeof data?.operational_monitoring_threshold_mpa === "number" && !isNaN(data.operational_monitoring_threshold_mpa)
    ? data.operational_monitoring_threshold_mpa
    : 3.0;
  const rollingWindow = data?.rolling_window_size ?? 10;

  // Chart coordinates
  const chartWidth = 520;
  const chartHeight = 260;
  const chartPadding = 40;
  const validResiduals = items
    .map((it) => Math.abs(it.residual_mpa))
    .filter((v) => typeof v === "number" && !isNaN(v));
  const maxAbsError = Math.max(...validResiduals, threshold + 2, 6);

  const scaleY = (res: number) => {
    if (typeof res !== "number" || isNaN(res)) return chartHeight / 2;
    // Map [-maxAbsError, +maxAbsError] to [chartHeight - chartPadding, chartPadding]
    const norm = (res + maxAbsError) / (2 * maxAbsError || 1);
    return (chartHeight - chartPadding) - norm * (chartHeight - 2 * chartPadding);
  };

  const scaleX = (idx: number) => {
    if (typeof idx !== "number" || isNaN(idx)) return chartPadding;
    if (items.length <= 1) return chartWidth / 2;
    return chartPadding + (idx / (items.length - 1)) * (chartWidth - 2 * chartPadding);
  };

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
          marginBottom: "12px",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <TrendingUp size={18} color={tokens.primaryAccent} />
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
              Prediction Error & Residual Trend
            </h3>
          </div>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.78rem", color: tokens.textMuted }}>
            Chronological model residuals (Predicted − Actual) with moving average and monitoring limits
          </p>
        </div>

        {/* Legend */}
        {hasData && (
          <div style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "0.74rem", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <div style={{ width: "8px", height: "8px", borderRadius: "2px", backgroundColor: "#3B82F6" }} />
              <span style={{ color: tokens.textSecondary }}>Residual (MPa)</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <div style={{ width: "12px", height: "2px", backgroundColor: "#D97706" }} />
              <span style={{ color: tokens.textSecondary }}>Rolling MAE (W={rollingWindow})</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <div style={{ width: "12px", height: "2px", borderTop: "2px dashed #EF4444" }} />
              <span style={{ color: "#DC2626", fontWeight: 600 }}>±{threshold.toFixed(1)} MPa Limit</span>
            </div>
          </div>
        )}
      </div>

      {/* Threshold Operational Clarification Banner */}
      <div
        style={{
          padding: "6px 10px",
          backgroundColor: "#F8FAFC",
          borderRadius: "6px",
          border: `1px solid ${tokens.borderLight}`,
          fontSize: "0.72rem",
          color: tokens.textMuted,
          marginBottom: "12px",
          display: "flex",
          alignItems: "center",
          gap: "6px",
        }}
      >
        <Info size={13} color={tokens.textMuted} style={{ flexShrink: 0 }} />
        <span>
          <strong>Operational Monitoring Threshold (±{threshold.toFixed(1)} MPa): </strong>
          Internal threshold for model residual alerts; does not represent IS 456 acceptance criteria.
        </span>
      </div>

      {/* Chart Canvas */}
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
            padding: "36px 20px",
            minHeight: "220px",
            textAlign: "center",
          }}
        >
          <Info size={28} color={tokens.textMuted} style={{ marginBottom: "8px" }} />
          <div style={{ fontSize: "0.85rem", fontWeight: 600, color: tokens.textSecondary }}>
            No residual trend data available
          </div>
          <div style={{ fontSize: "0.75rem", color: tokens.textMuted, marginTop: "4px", maxWidth: "340px" }}>
            Awaiting sequential batch predictions to plot temporal error drift and rolling accuracy.
          </div>
        </div>
      ) : (
        <div
          className="dashboard-contained-scroll"
          style={{
            position: "relative",
            width: "100%",
            overflowX: "auto",
          }}
        >
          <div style={{ minWidth: "500px" }}>
            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              style={{ width: "100%", height: "230px", display: "block" }}
            >
              {/* Zero Residual Center Line */}
              <line
                x1={chartPadding}
                y1={scaleY(0)}
                x2={chartWidth - chartPadding}
                y2={scaleY(0)}
                stroke="#64748B"
                strokeWidth="1.5"
              />
              <text
                x={chartPadding - 6}
                y={scaleY(0) + 3}
                fontSize="9"
                fill="#64748B"
                fontWeight="600"
                textAnchor="end"
              >
                0 MPa
              </text>

              {/* Upper Operational Threshold (+3 MPa) */}
              <line
                x1={chartPadding}
                y1={scaleY(threshold)}
                x2={chartWidth - chartPadding}
                y2={scaleY(threshold)}
                stroke="#EF4444"
                strokeWidth="1.2"
                strokeDasharray="4 4"
              />
              <text
                x={chartWidth - chartPadding + 6}
                y={scaleY(threshold) + 3}
                fontSize="9"
                fill="#DC2626"
                fontWeight="600"
                textAnchor="start"
              >
                +{threshold.toFixed(0)} MPa
              </text>

              {/* Lower Operational Threshold (-3 MPa) */}
              <line
                x1={chartPadding}
                y1={scaleY(-threshold)}
                x2={chartWidth - chartPadding}
                y2={scaleY(-threshold)}
                stroke="#EF4444"
                strokeWidth="1.2"
                strokeDasharray="4 4"
              />
              <text
                x={chartWidth - chartPadding + 6}
                y={scaleY(-threshold) + 3}
                fontSize="9"
                fill="#DC2626"
                fontWeight="600"
                textAnchor="start"
              >
                -{threshold.toFixed(0)} MPa
              </text>

              {/* Data Points and Error Stems */}
              {items.map((item, idx) => {
                const cx = scaleX(idx);
                const cy = scaleY(item.residual_mpa);
                const cyZero = scaleY(0);
                const isHovered = hoveredPoint?.batch_id === item.batch_id;
                const isExceeded = Math.abs(item.residual_mpa) > threshold;

                return (
                  <g
                    key={`${item.batch_id || "batch"}-${idx}`}
                    onMouseEnter={() => setHoveredPoint(item)}
                    onMouseLeave={() => setHoveredPoint(null)}
                    style={{ cursor: "pointer" }}
                  >
                    {/* Vertical Stem */}
                    <line
                      x1={cx}
                      y1={cyZero}
                      x2={cx}
                      y2={cy}
                      stroke={isExceeded ? "#EF4444" : "#3B82F6"}
                      strokeWidth={isHovered ? 2.5 : 1.5}
                    />
                    {/* Point Circle */}
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isHovered ? 6 : 4}
                      fill={isExceeded ? "#EF4444" : "#3B82F6"}
                      stroke="#FFFFFF"
                      strokeWidth={1.5}
                    />
                  </g>
                );
              })}

              {/* Rolling MAE Line (if computed) */}
              {items.length > 1 && (() => {
                const validMaeItems = items
                  .map((it, origIdx) => ({
                    ...it,
                    plotIdx: typeof it.index === "number" && !isNaN(it.index) ? it.index : origIdx,
                  }))
                  .filter((it) => it.rolling_mae_mpa !== null && it.rolling_mae_mpa !== undefined && typeof it.rolling_mae_mpa === "number" && !isNaN(it.rolling_mae_mpa));

                if (validMaeItems.length === 0) return null;

                const pathD = validMaeItems
                  .map((it, idx) => {
                    const x = scaleX(it.plotIdx);
                    const y = scaleY(it.rolling_mae_mpa!);
                    if (isNaN(x) || isNaN(y)) return null;
                    return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
                  })
                  .filter(Boolean)
                  .join(" ");

                if (!pathD) return null;

                return (
                  <path
                    d={pathD}
                    fill="none"
                    stroke="#D97706"
                    strokeWidth="2"
                  />
                );
              })()}
            </svg>
          </div>

          {/* Hover Tooltip */}
          {hoveredPoint && (
            <div
              style={{
                marginTop: "8px",
                padding: "8px 12px",
                backgroundColor: "#0F172A",
                color: "#F8FAFC",
                borderRadius: "6px",
                fontSize: "0.74rem",
                display: "flex",
                flexWrap: "wrap",
                gap: "12px",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <strong>Batch: </strong>{hoveredPoint.batch_number}
              </div>
              <div>
                <strong>Actual: </strong>{hoveredPoint.actual_strength_mpa.toFixed(2)} MPa
              </div>
              <div>
                <strong>Predicted: </strong>{hoveredPoint.predicted_strength_mpa.toFixed(2)} MPa
              </div>
              <div>
                <strong>Residual: </strong>
                <span style={{ color: hoveredPoint.residual_mpa >= 0 ? "#86EFAC" : "#FCA5A5" }}>
                  {hoveredPoint.residual_mpa > 0 ? "+" : ""}{hoveredPoint.residual_mpa.toFixed(2)} MPa
                </span>
              </div>
              {hoveredPoint.rolling_mae_mpa !== null && hoveredPoint.rolling_mae_mpa !== undefined && (
                <div>
                  <strong>Rolling MAE: </strong>{hoveredPoint.rolling_mae_mpa.toFixed(2)} MPa
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
