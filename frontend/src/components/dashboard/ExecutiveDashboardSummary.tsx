import React from "react";
import {
  Activity,
  Cpu,
  Sliders,
  ShieldCheck,
} from "lucide-react";
import { ExecutiveDashboardSummaryDTO } from "../../services/reportingService";
import { enterpriseLightTokens as tokens } from "../manual-entry/enterpriseLightTokens";

interface ExecutiveDashboardSummaryProps {
  summary: ExecutiveDashboardSummaryDTO | null;
  loading?: boolean;
}

export const ExecutiveDashboardSummary: React.FC<ExecutiveDashboardSummaryProps> = ({
  summary,
  loading = false,
}) => {
  if (loading) {
    return (
      <div
        style={{
          backgroundColor: tokens.surfaceCard,
          border: `1px solid ${tokens.border}`,
          borderRadius: tokens.radiusLarge,
          padding: "20px",
          marginBottom: "24px",
          boxShadow: tokens.shadowCard,
        }}
      >
        <div style={{ height: "20px", width: "180px", backgroundColor: tokens.borderLight, borderRadius: "4px", marginBottom: "16px" }} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
          {[1, 2, 3, 4].map((i) => (
            <div key={i} style={{ height: "120px", backgroundColor: tokens.surfaceSecondary, borderRadius: tokens.radius }} />
          ))}
        </div>
      </div>
    );
  }

  if (!summary) return null;

  const {
    quality_and_production: qp,
    strength_prediction: sp,
    mix_optimization: mo,
    governance_and_commercial: gc,
  } = summary;

  const cardStyle: React.CSSProperties = {
    backgroundColor: tokens.surfaceSecondary,
    border: `1px solid ${tokens.borderLight}`,
    borderRadius: tokens.radius,
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
  };

  const groupHeaderStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "12px",
    paddingBottom: "8px",
    borderBottom: `1px solid ${tokens.borderLight}`,
  };

  const groupTitleStyle: React.CSSProperties = {
    fontSize: "0.74rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color: tokens.textSecondary,
  };

  const rowStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    fontSize: "0.78rem",
    marginBottom: "6px",
  };

  const labelStyle: React.CSSProperties = {
    color: tokens.textMuted,
  };

  const valStyle: React.CSSProperties = {
    color: tokens.textPrimary,
    fontWeight: 600,
  };

  return (
    <div
      style={{
        backgroundColor: tokens.surfaceCard,
        border: `1px solid ${tokens.border}`,
        borderRadius: tokens.radiusLarge,
        padding: "20px",
        marginBottom: "24px",
        boxShadow: tokens.shadowCard,
      }}
      data-testid="executive-dashboard-summary"
    >
      {/* Header bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "16px",
          paddingBottom: "12px",
          borderBottom: `1px solid ${tokens.border}`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Activity size={18} color={tokens.primaryAccent} />
          <h2
            style={{
              margin: 0,
              fontSize: "0.95rem",
              fontWeight: 700,
              color: tokens.textPrimary,
              letterSpacing: "-0.01em",
            }}
          >
            Dashboard Summary
          </h2>
        </div>
        <span
          style={{
            fontSize: "0.72rem",
            color: tokens.textMuted,
            fontFamily: tokens.fontMono,
            backgroundColor: tokens.surfaceSecondary,
            padding: "3px 8px",
            borderRadius: "4px",
            border: `1px solid ${tokens.borderLight}`,
          }}
        >
          Authoritative Operational Summary
        </span>
      </div>

      {/* 4 Factual Groups Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
          gap: "14px",
        }}
      >
        {/* GROUP A: QUALITY & PRODUCTION */}
        <div style={cardStyle}>
          <div>
            <div style={groupHeaderStyle}>
              <span style={groupTitleStyle}>A. Quality & Production</span>
              <Activity size={15} color={tokens.textMuted} />
            </div>
            <div>
              <div style={rowStyle}>
                <span style={labelStyle}>Batches Produced:</span>
                <span style={valStyle}>{qp?.total_batches_produced ?? "—"}</span>
              </div>
              <div style={rowStyle}>
                <span style={labelStyle}>Mean 28D Strength:</span>
                <span style={valStyle}>
                  {qp?.mean_strength_28d_mpa != null ? `${qp.mean_strength_28d_mpa} MPa` : "—"}
                </span>
              </div>
              <div style={rowStyle}>
                <span style={labelStyle}>IS Compliance:</span>
                <span
                  style={{
                    ...valStyle,
                    color:
                      (qp?.quality_compliance_percent ?? 0) >= 90
                        ? tokens.successGreen
                        : tokens.warningAmber,
                  }}
                >
                  {qp?.quality_compliance_percent != null
                    ? `${qp.quality_compliance_percent}%`
                    : "—"}
                </span>
              </div>
              <div style={rowStyle}>
                <span style={labelStyle}>Variability (σ / CV):</span>
                <span style={{ ...valStyle, fontWeight: 500 }}>
                  {qp?.strength_variability_sigma_mpa != null
                    ? `${qp.strength_variability_sigma_mpa} MPa`
                    : "—"}{" "}
                  <span style={{ color: tokens.textMuted }}>
                    ({qp?.strength_cov_percent != null ? `${qp.strength_cov_percent}%` : "—"})
                  </span>
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* GROUP B: STRENGTH PREDICTION */}
        <div style={cardStyle}>
          <div>
            <div style={groupHeaderStyle}>
              <span style={groupTitleStyle}>B. Strength Prediction</span>
              <Cpu size={15} color={tokens.textMuted} />
            </div>
            <div>
              <div style={rowStyle}>
                <span style={labelStyle}>Platform Model:</span>
                <span
                  style={{
                    ...valStyle,
                    fontFamily: tokens.fontMono,
                    fontSize: "0.72rem",
                    maxWidth: "200px",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                  title={sp?.platform_active_model}
                >
                  {sp?.platform_active_model ? `${sp.platform_active_model}${sp.platform_model_version ? ` (${sp.platform_model_version})` : ""}` : "—"}
                </span>
              </div>
              <div style={rowStyle}>
                <span style={labelStyle}>Validation Status:</span>
                <span style={{ ...valStyle, fontWeight: 500 }}>
                  {sp?.validation_status ?? "—"}
                </span>
              </div>
              <div style={rowStyle}>
                <span style={labelStyle}>Target fck / fck':</span>
                <span style={valStyle}>
                  {sp?.target_characteristic_fck_mpa != null
                    ? `${sp.target_characteristic_fck_mpa}`
                    : "—"}{" "}
                  /{" "}
                  {sp?.target_mean_strength_fck_prime_mpa != null
                    ? `${sp.target_mean_strength_fck_prime_mpa} MPa`
                    : "—"}
                </span>
              </div>
              <div style={rowStyle}>
                <span style={labelStyle}>Prediction Margin:</span>
                <span style={{ ...valStyle, fontWeight: 500 }}>
                  {sp?.prediction_margin_mpa != null
                    ? `${sp.prediction_margin_mpa > 0 ? "+" : ""}${sp.prediction_margin_mpa} MPa`
                    : "—"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* GROUP C: MIX OPTIMIZATION */}
        <div style={cardStyle}>
          <div>
            <div style={groupHeaderStyle}>
              <span style={groupTitleStyle}>C. Mix Optimization</span>
              <Sliders size={15} color={tokens.textMuted} />
            </div>
            <div>
              <div style={rowStyle}>
                <span style={labelStyle}>Run Status:</span>
                <span style={valStyle}>
                  {mo?.has_optimization_run ? "Active Run" : "No Active Run"}
                </span>
              </div>
              <div style={rowStyle}>
                <span style={labelStyle}>Evaluated (Feasible):</span>
                <span style={valStyle}>
                  {mo?.total_candidates_evaluated ?? 0} ({mo?.feasible_candidates_count ?? 0})
                </span>
              </div>
              <div style={rowStyle}>
                <span style={labelStyle}>Pareto Optimal:</span>
                <span style={valStyle}>{mo?.pareto_optimal_count ?? 0}</span>
              </div>
              <div style={rowStyle}>
                <span style={labelStyle}>Impact Summary:</span>
                <span
                  style={{
                    ...valStyle,
                    fontWeight: 500,
                    maxWidth: "200px",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                  title={mo?.recipe_impact_summary}
                >
                  {mo?.recipe_impact_summary ?? "—"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* GROUP D: GOVERNANCE & STATUS */}
        <div style={cardStyle}>
          <div>
            <div style={groupHeaderStyle}>
              <span style={groupTitleStyle}>D. Governance & Status</span>
              <ShieldCheck size={15} color={tokens.textMuted} />
            </div>
            <div>
              <div style={rowStyle}>
                <span style={labelStyle}>Human Review:</span>
                <span
                  style={{
                    ...valStyle,
                    fontSize: "0.72rem",
                    color:
                      gc?.review_status === "ACCEPTED"
                        ? tokens.successGreen
                        : gc?.review_status === "REJECTED"
                        ? tokens.errorRed
                        : tokens.warningAmber,
                  }}
                >
                  {gc?.review_status === "ACCEPTED"
                    ? "HUMAN REVIEW: ACCEPTED"
                    : gc?.review_status === "REJECTED"
                    ? "REJECTED"
                    : "PENDING_REVIEW"}
                </span>
              </div>
              <div style={rowStyle}>
                <span style={labelStyle}>Pricing Source:</span>
                <span style={{ ...valStyle, fontWeight: 500 }}>
                  {gc?.pricing_configuration_status === "CONFIGURED"
                    ? "Configured"
                    : "Not Configured"}
                </span>
              </div>
              <div style={rowStyle}>
                <span style={labelStyle}>Cost Impact:</span>
                <span style={valStyle}>
                  {gc?.cost_delta_per_m3_inr != null
                    ? `₹${gc.cost_delta_per_m3_inr}/m³`
                    : "—"}
                </span>
              </div>
              <div
                style={{
                  fontSize: "0.68rem",
                  color: tokens.textMuted,
                  marginTop: "6px",
                  paddingTop: "6px",
                  borderTop: `1px dashed ${tokens.borderLight}`,
                  fontStyle: "italic",
                }}
              >
                Production activation is outside the current phase.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
