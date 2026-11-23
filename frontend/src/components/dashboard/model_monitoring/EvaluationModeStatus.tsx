import React from "react";
import { Activity, History, AlertCircle, Info, CheckCircle2, ShieldAlert } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { ModelMonitoringScopeDTO } from "../../../services/reportingService";

interface EvaluationModeStatusProps {
  activeMode: "PRODUCTION_STORED" | "RETROSPECTIVE_BACKTEST";
  onModeChange: (mode: "PRODUCTION_STORED" | "RETROSPECTIVE_BACKTEST") => void;
  productionScope?: ModelMonitoringScopeDTO | null;
  backtestScope?: ModelMonitoringScopeDTO | null;
  activeModelVersion?: string | null;
  isLoading?: boolean;
}

export const EvaluationModeStatus: React.FC<EvaluationModeStatusProps> = ({
  activeMode,
  onModeChange,
  productionScope,
  backtestScope,
  activeModelVersion,
  isLoading = false,
}) => {
  const currentScope = activeMode === "PRODUCTION_STORED" ? productionScope : backtestScope;
  const isProdEmpty = activeMode === "PRODUCTION_STORED" && (productionScope?.status === "NO_STORED_PREDICTIONS_IN_RANGE" || (productionScope?.eligible_count ?? 0) === 0);
  const isBacktestLimited = activeMode === "RETROSPECTIVE_BACKTEST" && (backtestScope?.eligible_count ?? 0) < 30;

  return (
    <div
      style={{
        backgroundColor: "#FFFFFF",
        borderRadius: "10px",
        border: `1px solid ${tokens.borderLight}`,
        boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.02)",
        padding: "16px 20px",
        marginBottom: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
      }}
    >
      {/* Mode Selector & Model Badge */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        {/* Segmented Control */}
        <div
          role="tablist"
          aria-label="Model Evaluation Mode"
          style={{
            display: "inline-flex",
            backgroundColor: "#F1F5F9",
            padding: "3px",
            borderRadius: "8px",
            border: `1px solid ${tokens.borderLight}`,
          }}
        >
          <button
            type="button"
            role="tab"
            aria-selected={activeMode === "PRODUCTION_STORED"}
            onClick={() => onModeChange("PRODUCTION_STORED")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 14px",
              fontSize: "0.8rem",
              fontWeight: activeMode === "PRODUCTION_STORED" ? 600 : 500,
              color: activeMode === "PRODUCTION_STORED" ? tokens.textPrimary : tokens.textMuted,
              backgroundColor: activeMode === "PRODUCTION_STORED" ? "#FFFFFF" : "transparent",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              boxShadow: activeMode === "PRODUCTION_STORED" ? "0 1px 2px rgba(0,0,0,0.05)" : "none",
              transition: "all 0.15s ease",
            }}
          >
            <Activity size={14} color={activeMode === "PRODUCTION_STORED" ? tokens.primaryAccent : tokens.textMuted} />
            <span>Production Monitoring (Live)</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeMode === "RETROSPECTIVE_BACKTEST"}
            onClick={() => onModeChange("RETROSPECTIVE_BACKTEST")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 14px",
              fontSize: "0.8rem",
              fontWeight: activeMode === "RETROSPECTIVE_BACKTEST" ? 600 : 500,
              color: activeMode === "RETROSPECTIVE_BACKTEST" ? tokens.textPrimary : tokens.textMuted,
              backgroundColor: activeMode === "RETROSPECTIVE_BACKTEST" ? "#FFFFFF" : "transparent",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              boxShadow: activeMode === "RETROSPECTIVE_BACKTEST" ? "0 1px 2px rgba(0,0,0,0.05)" : "none",
              transition: "all 0.15s ease",
            }}
          >
            <History size={14} color={activeMode === "RETROSPECTIVE_BACKTEST" ? "#D97706" : tokens.textMuted} />
            <span>Retrospective Backtest (Historical)</span>
          </button>
        </div>

        {/* Model Version Indicator */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.78rem" }}>
          <span style={{ color: tokens.textMuted }}>Active Model:</span>
          <span
            style={{
              fontFamily: "monospace",
              fontSize: "0.78rem",
              fontWeight: 600,
              backgroundColor: "#F1F5F9",
              padding: "3px 8px",
              borderRadius: "4px",
              color: tokens.textPrimary,
              border: `1px solid ${tokens.borderLight}`,
            }}
          >
            {activeModelVersion || currentScope?.model_version || "—"}
          </span>
          <span
            style={{
              fontSize: "0.72rem",
              fontWeight: 600,
              backgroundColor: "rgba(5, 150, 105, 0.1)",
              color: "#059669",
              padding: "2px 6px",
              borderRadius: "4px",
            }}
          >
            ACTIVE
          </span>
        </div>
      </div>

      {/* Mode Operational Context Banner */}
      {activeMode === "PRODUCTION_STORED" ? (
        <div
          style={{
            padding: "10px 14px",
            backgroundColor: isProdEmpty ? "#F8FAFC" : "#F0FDF4",
            border: `1px solid ${isProdEmpty ? tokens.borderLight : "#BBF7D0"}`,
            borderRadius: "6px",
            display: "flex",
            alignItems: "flex-start",
            gap: "10px",
          }}
        >
          <Info size={16} color={isProdEmpty ? tokens.textMuted : "#16A34A"} style={{ marginTop: "2px", flexShrink: 0 }} />
          <div style={{ fontSize: "0.78rem", lineHeight: "1.4", color: tokens.textSecondary }}>
            <strong style={{ color: tokens.textPrimary }}>Production Stored Monitoring: </strong>
            {isProdEmpty ? (
              <span>
                No production prediction records are available yet. Production monitoring will populate automatically once real-time online inferences are logged.
              </span>
            ) : (
              <span>
                Displaying genuine production predictions matched with 28-day laboratory break outcomes.
              </span>
            )}
          </div>
        </div>
      ) : (
        <div
          style={{
            padding: "10px 14px",
            backgroundColor: "#FFFBEB",
            border: "1px solid #FDE68A",
            borderRadius: "6px",
            display: "flex",
            alignItems: "flex-start",
            gap: "10px",
          }}
        >
          <AlertCircle size={16} color="#D97706" style={{ marginTop: "2px", flexShrink: 0 }} />
          <div style={{ fontSize: "0.78rem", lineHeight: "1.4", color: "#92400E" }}>
            <strong style={{ color: "#78350F" }}>Retrospective Model Backtest ({backtestScope?.eligible_count ?? 0} evaluation pairs): </strong>
            <span>
              Evaluated retrospectively against historical batch material consumption and 28-day laboratory break tests. Insufficient sample size for reliable model performance assessment.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
