import React from "react";
import { Gauge, Calculator, Target, Compass, BarChart2, Hash, HelpCircle } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { StatisticalMetricsDTO, ModelMonitoringScopeDTO } from "../../../services/reportingService";

interface ModelPerformanceSummaryProps {
  metrics?: StatisticalMetricsDTO | null;
  scope?: ModelMonitoringScopeDTO | null;
  isLoading?: boolean;
}

export const ModelPerformanceSummary: React.FC<ModelPerformanceSummaryProps> = ({
  metrics,
  scope,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="dashboard-sqc-summary-grid" style={{ marginBottom: "16px" }}>
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            style={{
              padding: "16px",
              backgroundColor: "#FFFFFF",
              borderRadius: "10px",
              border: `1px solid ${tokens.borderLight}`,
              height: "90px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <span style={{ fontSize: "0.78rem", color: tokens.textMuted }}>Loading metric...</span>
          </div>
        ))}
      </div>
    );
  }

  const sampleCount = metrics?.sample_count ?? 0;
  const hasData = sampleCount > 0;
  const isLimited = sampleCount > 0 && sampleCount < 30;

  const cards = [
    {
      testId: "kpi-sample-count",
      title: "Evaluation Samples",
      value: `${sampleCount} batches`,
      subtext: sampleCount === 0
        ? "No predictions in range"
        : isLimited
        ? "Limited sample size (N < 30)"
        : "Statistically sufficient sample",
      icon: <Hash size={18} color={tokens.primaryAccent} />,
      statusColor: sampleCount === 0 ? tokens.textMuted : isLimited ? "#D97706" : "#059669",
      tooltip: "Number of batch prediction-actual outcome pairs evaluated.",
    },
    {
      testId: "kpi-mae",
      title: "Mean Absolute Error (MAE)",
      value: metrics?.mae_mpa !== null && metrics?.mae_mpa !== undefined
        ? `${metrics.mae_mpa.toFixed(2)} MPa`
        : "N/A — insufficient data",
      subtext: hasData ? "Average absolute prediction error" : "Awaiting batch predictions",
      icon: <Calculator size={18} color="#0D9488" />,
      statusColor: hasData ? tokens.textPrimary : tokens.textMuted,
      tooltip: "Mean Absolute Error: mean(|predicted - actual|). Lower is better.",
    },
    {
      testId: "kpi-rmse",
      title: "Root Mean Squared Error (RMSE)",
      value: metrics?.rmse_mpa !== null && metrics?.rmse_mpa !== undefined
        ? `${metrics.rmse_mpa.toFixed(2)} MPa`
        : "N/A — insufficient data",
      subtext: "RMSE = √(MSE)",
      icon: <Gauge size={18} color="#2563EB" />,
      statusColor: hasData ? tokens.textPrimary : tokens.textMuted,
      tooltip: "Root Mean Squared Error: sqrt(mean((predicted - actual)²)). Penalizes large errors.",
    },
    {
      testId: "kpi-r2",
      title: "R² Coefficient",
      value: metrics?.r2_score !== null && metrics?.r2_score !== undefined
        ? metrics.r2_score.toFixed(3)
        : "N/A — insufficient data",
      subtext: hasData && metrics?.r2_score === null
        ? "Undefined (zero target variance)"
        : hasData
        ? "Proportion of variance explained"
        : "Requires N ≥ 2 with variance",
      icon: <Target size={18} color="#7C3AED" />,
      statusColor: metrics?.r2_score !== null && metrics?.r2_score !== undefined ? tokens.textPrimary : tokens.textMuted,
      tooltip: "Coefficient of determination: 1 - SSE/SST. Undefined when sample variance is zero or N < 2.",
    },
    {
      testId: "kpi-bias",
      title: "Mean Residual (Bias)",
      value: metrics?.mean_residual_mpa !== null && metrics?.mean_residual_mpa !== undefined
        ? `${metrics.mean_residual_mpa > 0 ? "+" : ""}${metrics.mean_residual_mpa.toFixed(2)} MPa`
        : "N/A — insufficient data",
      subtext: hasData
        ? metrics?.mean_residual_mpa === 0
          ? "Unbiased (predicted = actual)"
          : metrics?.mean_residual_mpa! > 0
          ? "Over-predicting on average"
          : "Under-predicting on average"
        : "Awaiting evaluation pairs",
      icon: <Compass size={18} color="#EA580C" />,
      statusColor: hasData ? tokens.textPrimary : tokens.textMuted,
      tooltip: "Mean residual: mean(predicted - actual). Positive indicates model over-predicts, negative indicates under-predicts.",
    },
    {
      testId: "kpi-residual-std",
      title: "Residual Std Deviation",
      value: metrics?.residual_std_dev_mpa !== null && metrics?.residual_std_dev_mpa !== undefined
        ? `${metrics.residual_std_dev_mpa.toFixed(2)} MPa`
        : "N/A — insufficient data",
      subtext: hasData && metrics?.residual_std_dev_mpa === null
        ? "Undefined for N < 2"
        : hasData
        ? "Sample dispersion (ddof=1)"
        : "Requires N ≥ 2",
      icon: <BarChart2 size={18} color="#475569" />,
      statusColor: metrics?.residual_std_dev_mpa !== null && metrics?.residual_std_dev_mpa !== undefined ? tokens.textPrimary : tokens.textMuted,
      tooltip: "Sample standard deviation of prediction residuals with ddof=1.",
    },
  ];

  return (
    <div className="dashboard-sqc-summary-grid" style={{ marginBottom: "16px" }}>
      {cards.map((card, idx) => (
        <div
          key={idx}
          style={{
            padding: "16px 18px",
            backgroundColor: "#FFFFFF",
            borderRadius: "10px",
            border: `1px solid ${tokens.borderLight}`,
            boxShadow: tokens.shadowCard,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            boxSizing: "border-box",
            minWidth: 0,
          }}
          title={card.tooltip}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <span
              style={{
                fontSize: "0.74rem",
                fontWeight: 600,
                color: tokens.textMuted,
                textTransform: "uppercase",
                letterSpacing: "0.03em",
              }}
            >
              {card.title}
            </span>
            <div
              style={{
                padding: "6px",
                borderRadius: "6px",
                backgroundColor: tokens.surfaceSecondary || "#F8FAFC",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {card.icon}
            </div>
          </div>

          <div
            data-testid={card.testId}
            style={{
              fontSize: card.value.includes("N/A") ? "0.95rem" : "1.25rem",
              fontWeight: 700,
              color: card.statusColor,
              letterSpacing: "-0.02em",
              marginBottom: "4px",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {card.value}
          </div>

          <div
            style={{
              fontSize: "0.72rem",
              color: tokens.textMuted,
              lineHeight: 1.3,
            }}
          >
            {card.subtext}
          </div>
        </div>
      ))}
    </div>
  );
};
