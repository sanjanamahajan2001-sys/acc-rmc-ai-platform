import React, { useState } from "react";
import { ScatterChart, Info, HelpCircle } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { ActualVsPredictedResponseDTO, ActualVsPredictedItemDTO } from "../../../services/reportingService";

interface PredictionValidationChartProps {
  data?: ActualVsPredictedResponseDTO | null;
  isLoading?: boolean;
  title?: string;
  isBacktestMode?: boolean;
}

export const PredictionValidationChart: React.FC<PredictionValidationChartProps> = ({
  data,
  isLoading = false,
  title = "Actual vs. Predicted 28-Day Strength",
  isBacktestMode = false,
}) => {
  const [hoveredItem, setHoveredItem] = useState<ActualVsPredictedItemDTO | null>(null);

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
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>Loading validation data...</span>
      </div>
    );
  }

  const items = data?.items || [];
  const hasData = items.length > 0;
  const sampleCount = data?.summary_metrics?.sample_count ?? items.length;

  // Chart coordinate scaling
  const minVal = 0;
  const maxVal = 70; // 0 to 70 MPa standard range
  const chartPadding = 40;
  const chartWidth = 460;
  const chartHeight = 260;

  const scaleX = (val: number) => chartPadding + ((val - minVal) / (maxVal - minVal)) * (chartWidth - 2 * chartPadding);
  const scaleY = (val: number) => (chartHeight - chartPadding) - ((val - minVal) / (maxVal - minVal)) * (chartHeight - 2 * chartPadding);

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
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
              {title}
            </h3>
            {isBacktestMode && (
              <span
                style={{
                  fontSize: "0.68rem",
                  fontWeight: 600,
                  backgroundColor: "#FEF3C7",
                  color: "#92400E",
                  padding: "2px 6px",
                  borderRadius: "4px",
                }}
              >
                Backtest ({sampleCount} pairs)
              </span>
            )}
          </div>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.78rem", color: tokens.textMuted }}>
            Scatter comparison of model predictions (X-axis) against laboratory break tests (Y-axis)
          </p>
        </div>

        {/* Legend */}
        {hasData && (
          <div style={{ display: "flex", alignItems: "center", gap: "14px", fontSize: "0.74rem", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#4F46E5" }} />
              <span style={{ color: tokens.textSecondary }}>Genuine ML Model</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <div style={{ width: "8px", height: "8px", borderRadius: "2px", backgroundColor: "#D97706" }} />
              <span style={{ color: "#D97706" }}>Fallback Estimate (Disaggregated)</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <div style={{ width: "12px", height: "2px", backgroundColor: "#94A3B8" }} />
              <span style={{ color: tokens.textMuted }}>Ideal (y = x)</span>
            </div>
          </div>
        )}
      </div>

      {/* Notice Callout for Limited Data */}
      {hasData && sampleCount < 30 && (
        <div
          style={{
            padding: "8px 12px",
            backgroundColor: "#FFFBEB",
            borderRadius: "6px",
            border: "1px solid #FDE68A",
            fontSize: "0.74rem",
            color: "#92400E",
            marginBottom: "12px",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          <Info size={14} color="#D97706" style={{ flexShrink: 0 }} />
          <span>
            <strong>Sample Size Notice: </strong>Only {sampleCount} genuine model evaluation pairs available. Model performance metrics exclude heuristic fallbacks.
          </span>
        </div>
      )}

      {/* Main Chart Area */}
      {!hasData ? (
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "40px 0",
          }}
        >
          <ScatterChart size={32} color={tokens.border} style={{ marginBottom: "8px" }} />
          <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>No validation pairs available for the selected filters.</span>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
          <div style={{ position: "relative", width: "100%", height: `${chartHeight}px` }}>
            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              style={{ width: "100%", height: "100%", overflow: "visible" }}
            >
              {/* Grid Lines */}
              {[10, 20, 30, 40, 50, 60].map((val) => (
                <g key={`grid-y-${val}`}>
                  {/* Horizontal Grid */}
                  <line
                    x1={chartPadding}
                    y1={scaleY(val)}
                    x2={chartWidth - chartPadding}
                    y2={scaleY(val)}
                    stroke="#E2E8F0"
                    strokeDasharray="3 3"
                  />
                  <text
                    x={chartPadding - 6}
                    y={scaleY(val) + 3}
                    fontSize="9"
                    fill="#94A3B8"
                    textAnchor="end"
                  >
                    {val}
                  </text>

                  {/* Vertical Grid */}
                  <line
                    x1={scaleX(val)}
                    y1={chartPadding}
                    x2={scaleX(val)}
                    y2={chartHeight - chartPadding}
                    stroke="#E2E8F0"
                    strokeDasharray="3 3"
                  />
                  <text
                    x={scaleX(val)}
                    y={chartHeight - chartPadding + 14}
                    fontSize="9"
                    fill="#94A3B8"
                    textAnchor="middle"
                  >
                    {val}
                  </text>
                </g>
              ))}

              {/* Equality Line (y = x) */}
              <line
                x1={scaleX(10)}
                y1={scaleY(10)}
                x2={scaleX(65)}
                y2={scaleY(65)}
                stroke="#94A3B8"
                strokeWidth="1.5"
                strokeDasharray="4 4"
              />

              {/* Data Points */}
              {items.map((item, idx) => {
                const cx = scaleX(item.predicted_strength_mpa);
                const cy = scaleY(item.actual_strength_mpa);
                const isHovered = hoveredItem?.batch_id === item.batch_id;
                const isModel = item.prediction_source === "ML_MODEL" || item.prediction_source === "MODEL";

                return (
                  <g
                    key={`${item.batch_id || 'batch'}-${idx}`}
                    onMouseEnter={() => setHoveredItem(item)}
                    onMouseLeave={() => setHoveredItem(null)}
                    style={{ cursor: "pointer" }}
                  >
                    {isModel ? (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isHovered ? 7 : 5}
                        fill="#4F46E5"
                        stroke="#FFFFFF"
                        strokeWidth={1.5}
                        style={{ transition: "all 0.15s ease" }}
                      />
                    ) : (
                      <rect
                        x={cx - (isHovered ? 5 : 3.5)}
                        y={cy - (isHovered ? 5 : 3.5)}
                        width={isHovered ? 10 : 7}
                        height={isHovered ? 10 : 7}
                        fill="#D97706"
                        stroke="#FFFFFF"
                        strokeWidth={1.5}
                        opacity={0.8}
                        style={{ transition: "all 0.15s ease" }}
                      />
                    )}
                  </g>
                );
              })}

              {/* Axis Labels */}
              <text
                x={chartWidth / 2}
                y={chartHeight - 4}
                fontSize="10"
                fontWeight="600"
                fill={tokens.textSecondary}
                textAnchor="middle"
              >
                Predicted Strength (MPa)
              </text>
              <text
                transform={`rotate(-90 12 ${chartHeight / 2})`}
                x={12}
                y={chartHeight / 2}
                fontSize="10"
                fontWeight="600"
                fill={tokens.textSecondary}
                textAnchor="middle"
              >
                Actual 28D Strength (MPa)
              </text>
            </svg>
          </div>

          {/* Point Tooltip */}
          {hoveredItem && (
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
                <strong>Batch: </strong>{hoveredItem.batch_number} ({hoveredItem.recipe_code || "Standard Mix"})
                <span
                  style={{
                    marginLeft: "6px",
                    padding: "1px 5px",
                    borderRadius: "3px",
                    fontSize: "0.68rem",
                    fontWeight: 600,
                    backgroundColor: hoveredItem.prediction_source === "ML_MODEL" ? "rgba(79, 70, 229, 0.3)" : "rgba(217, 119, 6, 0.3)",
                    color: hoveredItem.prediction_source === "ML_MODEL" ? "#A5B4FC" : "#FDE68A",
                  }}
                >
                  {hoveredItem.prediction_source === "ML_MODEL" ? "ML Model Inference" : "Heuristic Fallback"}
                </span>
              </div>
              <div>
                <strong>Actual: </strong>{hoveredItem.actual_strength_mpa.toFixed(2)} MPa
              </div>
              <div>
                <strong>Predicted: </strong>{hoveredItem.predicted_strength_mpa.toFixed(2)} MPa
              </div>
              <div>
                <strong>Residual: </strong>
                <span style={{ color: hoveredItem.residual_mpa >= 0 ? "#86EFAC" : "#FCA5A5" }}>
                  {hoveredItem.residual_mpa > 0 ? "+" : ""}{hoveredItem.residual_mpa.toFixed(2)} MPa
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
