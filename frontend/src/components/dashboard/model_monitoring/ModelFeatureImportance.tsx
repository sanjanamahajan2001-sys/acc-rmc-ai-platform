import React from "react";
import { Sliders, Info, Cpu } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { ModelFeatureImportanceResponseDTO } from "../../../services/reportingService";

interface ModelFeatureImportanceProps {
  data?: ModelFeatureImportanceResponseDTO | null;
  isLoading?: boolean;
}

export const ModelFeatureImportance: React.FC<ModelFeatureImportanceProps> = ({
  data,
  isLoading = false,
}) => {
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
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>Loading feature importance...</span>
      </div>
    );
  }

  const features = data?.features || [];
  const isAvailable = data?.feature_importance_available && features.length > 0;
  const maxWeight = isAvailable ? Math.max(...features.map((f) => f.importance_weight), 0.01) : 1;

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
          marginBottom: "14px",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Sliders size={18} color={tokens.primaryAccent} />
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
              Model Feature Importance
            </h3>
          </div>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.78rem", color: tokens.textMuted }}>
            Relative predictive contribution across 12 canonical mix & production predictors ({data?.algorithm || "Ridge"})
          </p>
        </div>

        {isAvailable && (
          <span
            style={{
              fontSize: "0.72rem",
              fontWeight: 600,
              backgroundColor: "#F1F5F9",
              color: tokens.textSecondary,
              padding: "3px 8px",
              borderRadius: "4px",
              border: `1px solid ${tokens.borderLight}`,
            }}
          >
            12 Canonical Predictors
          </span>
        )}
      </div>

      {/* Feature Bars List */}
      {!isAvailable ? (
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
            Feature importance unavailable
          </div>
          <div style={{ fontSize: "0.75rem", color: tokens.textMuted, marginTop: "4px", maxWidth: "340px" }}>
            {data?.message || "Estimator weights not exposed or model artifact not loaded."}
          </div>
        </div>
      ) : (
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            overflowY: "auto",
            maxHeight: "300px",
            paddingRight: "4px",
          }}
        >
          {features.map((feat, idx) => {
            const widthPct = maxWeight > 0 ? Math.max((feat.importance_weight / maxWeight) * 100, 2) : 2;

            return (
              <div
                key={feat.feature_name || idx}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  fontSize: "0.76rem",
                }}
              >
                {/* Feature Label */}
                <div
                  style={{
                    width: "160px",
                    fontWeight: 600,
                    color: tokens.textPrimary,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    flexShrink: 0,
                  }}
                  title={`${feat.display_name} (${feat.feature_name})`}
                >
                  {feat.display_name}
                </div>

                {/* Progress Bar Container */}
                <div
                  style={{
                    flex: 1,
                    height: "18px",
                    backgroundColor: "#F1F5F9",
                    borderRadius: "4px",
                    overflow: "hidden",
                    position: "relative",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${widthPct}%`,
                      backgroundColor: feat.importance_weight > 0 ? "#4F46E5" : "#CBD5E1",
                      borderRadius: "4px",
                      transition: "width 0.3s ease",
                    }}
                  />
                </div>

                {/* Value & Unit */}
                <div
                  style={{
                    width: "80px",
                    textAlign: "right",
                    fontWeight: 600,
                    color: feat.importance_weight > 0 ? tokens.textPrimary : tokens.textMuted,
                    flexShrink: 0,
                    fontFamily: "monospace",
                    fontSize: "0.74rem",
                  }}
                >
                  {(feat.importance_weight * 100).toFixed(1)}%
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
