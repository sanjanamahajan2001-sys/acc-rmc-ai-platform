import React, { useState } from "react";
import { Server, Database, ShieldCheck, ChevronDown, ChevronUp, FileCode, CheckCircle, Clock } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { ModelRegistryListDTO, ModelMetadataItemDTO, ModelMonitoringScopeDTO } from "../../../services/reportingService";

interface ModelInformationPanelProps {
  registryData?: ModelRegistryListDTO | null;
  scope?: ModelMonitoringScopeDTO | null;
  isLoading?: boolean;
}

export const ModelInformationPanel: React.FC<ModelInformationPanelProps> = ({
  registryData,
  scope,
  isLoading = false,
}) => {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  if (isLoading) {
    return (
      <div
        style={{
          padding: "24px",
          backgroundColor: "#FFFFFF",
          borderRadius: "10px",
          border: `1px solid ${tokens.borderLight}`,
          height: "260px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>Loading model information...</span>
      </div>
    );
  }

  const activeModel = registryData?.models?.find((m) => m.is_active || m.deployment_status === "ACTIVE") || registryData?.models?.[0];

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
        marginBottom: "16px",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Server size={18} color={tokens.primaryAccent} />
          <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
            Model Registry & Deployment Information
          </h3>
        </div>

        <button
          type="button"
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
            background: "none",
            border: "none",
            color: tokens.primaryAccent,
            fontSize: "0.76rem",
            fontWeight: 600,
            cursor: "pointer",
            padding: "4px 8px",
            borderRadius: "4px",
          }}
        >
          <span>{showTechnicalDetails ? "Hide Technical Details" : "Show Technical Details"}</span>
          {showTechnicalDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {/* Operational Information Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "14px",
          marginBottom: "14px",
        }}
      >
        {/* Model Version */}
        <div style={{ padding: "10px 12px", backgroundColor: "#F8FAFC", borderRadius: "6px", border: `1px solid ${tokens.borderLight}` }}>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted, marginBottom: "2px" }}>Active Model Version</div>
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: tokens.textPrimary, fontFamily: "monospace" }}>
            {activeModel?.model_version || "—"}
          </div>
        </div>

        {/* Algorithm */}
        <div style={{ padding: "10px 12px", backgroundColor: "#F8FAFC", borderRadius: "6px", border: `1px solid ${tokens.borderLight}` }}>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted, marginBottom: "2px" }}>Algorithm & Estimator</div>
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: tokens.textPrimary }}>
            {activeModel?.algorithm || "—"}
            <span style={{ fontSize: "0.72rem", color: tokens.textMuted, fontWeight: 400, marginLeft: "4px" }}>
              ({activeModel?.framework || "scikit-learn"})
            </span>
          </div>
        </div>

        {/* Deployment Status */}
        <div style={{ padding: "10px 12px", backgroundColor: "#F8FAFC", borderRadius: "6px", border: `1px solid ${tokens.borderLight}` }}>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted, marginBottom: "2px" }}>Deployment Status</div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span
              style={{
                fontSize: "0.72rem",
                fontWeight: 700,
                backgroundColor: "rgba(5, 150, 105, 0.1)",
                color: "#059669",
                padding: "2px 6px",
                borderRadius: "4px",
              }}
            >
              {activeModel?.deployment_status || "ACTIVE"}
            </span>
            <span style={{ fontSize: "0.75rem", color: tokens.textSecondary }}>Baseline Model (Limited Validation)</span>
          </div>
        </div>

        {/* Feature Schema */}
        <div style={{ padding: "10px 12px", backgroundColor: "#F8FAFC", borderRadius: "6px", border: `1px solid ${tokens.borderLight}` }}>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted, marginBottom: "2px" }}>Feature Schema</div>
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: tokens.textPrimary }}>
            v{activeModel?.feature_schema_version || "1.0.0"}
            <span style={{ fontSize: "0.72rem", color: tokens.textMuted, fontWeight: 400, marginLeft: "4px" }}>
              (12 Canonical Predictors)
            </span>
          </div>
        </div>
      </div>

      {/* Historical Population Funnel Lineage Summary */}
      <div
        style={{
          padding: "12px 14px",
          backgroundColor: "#F8FAFC",
          borderRadius: "6px",
          border: `1px solid ${tokens.borderLight}`,
          fontSize: "0.76rem",
          color: tokens.textSecondary,
        }}
      >
        <div style={{ fontWeight: 600, color: tokens.textPrimary, marginBottom: "6px", display: "flex", alignItems: "center", gap: "6px" }}>
          <Database size={14} color={tokens.primaryAccent} />
          <span>Historical Population & Evaluation Coverage Funnel</span>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "16px", lineHeight: "1.4" }}>
          <div>
            <span style={{ color: tokens.textMuted }}>Total Evaluated Telemetry: </span>
            <strong style={{ color: tokens.textPrimary }}>{scope?.total_predictions_count ?? scope?.eligible_count ?? 0}</strong>
          </div>
          <div>
            <span style={{ color: tokens.textMuted }}>Genuine Model Inferences (N<sub>model</sub>): </span>
            <strong style={{ color: "#059669" }}>{scope?.model_predictions_count ?? scope?.eligible_count ?? 0}</strong>
          </div>
          <div>
            <span style={{ color: tokens.textMuted }}>Heuristic Fallbacks (N<sub>fallback</sub>): </span>
            <strong style={{ color: "#D97706" }}>{scope?.fallback_predictions_count ?? 0}</strong>
          </div>
          <div>
            <span style={{ color: tokens.textMuted }}>Predictor Schema: </span>
            <strong style={{ color: tokens.textPrimary }}>12 Canonical Features</strong>
          </div>
          <div>
            <span style={{ color: tokens.textMuted }}>Coverage Status: </span>
            <strong style={{ color: "#059669" }}>Authoritative Lineage Synced</strong>
          </div>
        </div>
      </div>

      {/* Expandable Technical Details */}
      {showTechnicalDetails && (
        <div
          style={{
            marginTop: "12px",
            padding: "12px 14px",
            backgroundColor: "#0F172A",
            borderRadius: "6px",
            color: "#CBD5E1",
            fontSize: "0.72rem",
            fontFamily: "monospace",
            lineHeight: "1.5",
          }}
        >
          <div style={{ color: "#93C5FD", fontWeight: 600, marginBottom: "4px" }}>
            Model Artifact Provenance & Lineage:
          </div>
          <div>Registry ID: {activeModel?.model_registry_id || "—"}</div>
          <div>Artifact Path: {activeModel?.artifact_location || "—"}</div>
          <div>Checksum (SHA256): {activeModel?.checksum || "—"}</div>
          <div>Deployed: {activeModel?.deployment_timestamp ? new Date(activeModel.deployment_timestamp).toLocaleString() : "—"}</div>
        </div>
      )}
    </div>
  );
};
