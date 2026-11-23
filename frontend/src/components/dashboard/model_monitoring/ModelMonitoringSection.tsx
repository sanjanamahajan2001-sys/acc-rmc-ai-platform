import React, { useState } from "react";
import { Cpu, Activity, Brain } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import {
  PredictionSummaryDTO,
  ActualVsPredictedResponseDTO,
  PredictionErrorTrendResponseDTO,
  ModelFeatureImportanceResponseDTO,
  ModelRegistryListDTO,
} from "../../../services/reportingService";
import { EvaluationModeStatus } from "./EvaluationModeStatus";
import { ModelPerformanceSummary } from "./ModelPerformanceSummary";
import { PredictionValidationChart } from "./PredictionValidationChart";
import { PredictionErrorTrend } from "./PredictionErrorTrend";
import { ModelFeatureImportance } from "./ModelFeatureImportance";
import { ModelInformationPanel } from "./ModelInformationPanel";

interface ModelMonitoringSectionProps {
  predictionSummary?: PredictionSummaryDTO | null;
  actualVsPredicted?: ActualVsPredictedResponseDTO | null;
  predictionErrorTrend?: PredictionErrorTrendResponseDTO | null;
  featureImportance?: ModelFeatureImportanceResponseDTO | null;
  modelRegistry?: ModelRegistryListDTO | null;
  backtestData?: ActualVsPredictedResponseDTO | null;
  isLoading?: boolean;
  plantCode?: string | null;
  recipeCode?: string | null;
  dateFrom?: string | null;
  dateTo?: string | null;
  filters?: any;
}

export const ModelMonitoringSection: React.FC<ModelMonitoringSectionProps> = ({
  predictionSummary,
  actualVsPredicted,
  predictionErrorTrend,
  featureImportance,
  modelRegistry,
  backtestData,
  isLoading = false,
}) => {
  const [activeMode, setActiveMode] = useState<"PRODUCTION_STORED" | "RETROSPECTIVE_BACKTEST">("PRODUCTION_STORED");

  // Determine active dataset based on mode
  const currentMetrics = activeMode === "PRODUCTION_STORED"
    ? predictionSummary?.metrics
    : backtestData?.summary_metrics;

  const currentScope = activeMode === "PRODUCTION_STORED"
    ? predictionSummary?.scope
    : backtestData?.scope;

  const currentScatterData = activeMode === "PRODUCTION_STORED"
    ? actualVsPredicted
    : backtestData;

  const activeModelVersion = modelRegistry?.active_model_version || currentScope?.model_version || "—";

  return (
    <div style={{ marginBottom: "36px" }}>
      {/* Section Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "14px",
          paddingBottom: "8px",
          borderBottom: `1px solid ${tokens.borderLight}`,
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Cpu size={18} color={tokens.primaryAccent} />
          <h2
            style={{
              margin: 0,
              fontSize: "1.05rem",
              fontWeight: 700,
              color: tokens.textPrimary,
              letterSpacing: "-0.01em",
            }}
          >
            Strength Prediction Validation & Model Monitoring
          </h2>
        </div>
        <span style={{ fontSize: "0.72rem", color: tokens.textMuted }}>
          Authoritative Model Performance, Residual Trends & 12-Feature Predictor Lineage
        </span>
      </div>

      {/* Mode Status & Operational Toggle */}
      <EvaluationModeStatus
        activeMode={activeMode}
        onModeChange={setActiveMode}
        productionScope={predictionSummary?.scope}
        backtestScope={backtestData?.scope}
        activeModelVersion={activeModelVersion}
        isLoading={isLoading}
      />

      {/* KPI Performance Summary */}
      <ModelPerformanceSummary
        metrics={currentMetrics}
        scope={currentScope}
        isLoading={isLoading}
      />

      {/* Dual Column: Scatter Plot & Residual Trend */}
      <div className="dashboard-sqc-charts-grid" style={{ marginBottom: "16px" }}>
        <PredictionValidationChart
          data={currentScatterData}
          isLoading={isLoading}
          isBacktestMode={activeMode === "RETROSPECTIVE_BACKTEST"}
          title={
            activeMode === "PRODUCTION_STORED"
              ? "Production Actual vs. Predicted Strength"
              : "Retrospective Backtest (Actual vs. Predicted)"
          }
        />
        <PredictionErrorTrend
          data={predictionErrorTrend}
          isLoading={isLoading}
        />
      </div>

      {/* Dual Column: Feature Importance & Model Registry Information */}
      <div className="dashboard-materials-dual-grid">
        <ModelFeatureImportance
          data={featureImportance}
          isLoading={isLoading}
        />
        <ModelInformationPanel
          registryData={modelRegistry}
          scope={currentScope}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};
