/**
 * Step 5: Automated Quality Gate Evaluation & Pre-Submission Audit.
 * Responsive Mobile + Tablet + Desktop Hardening.
 * Enterprise Operations Light Theme Migration.
 */

import React, { useState, useEffect } from "react";
import { masterDataService, ManualDraftResponse, QualityCheckResult } from "../../services/masterDataService";
import { enterpriseLightTokens as tokens, primaryButtonBase, secondaryButtonBase } from "./enterpriseLightTokens";

interface Step5Props {
  draft: ManualDraftResponse;
  onBack: () => void;
  onNext: (updatedDraft: ManualDraftResponse) => void;
}

export const Step5QualityChecks: React.FC<Step5Props> = ({ draft, onBack, onNext }) => {
  const [result, setResult] = useState<QualityCheckResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isRevalidating, setIsRevalidating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQualityGate = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await masterDataService.evaluateStep5QualityChecks(draft.draft_id);
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to evaluate quality gate rules.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (draft?.draft_id) {
      fetchQualityGate();
    }
  }, [draft?.draft_id]);

  const handleProceedToStep6 = async () => {
    if (!result?.final_review_eligible) {
      setError("This batch is blocked from final review due to critical Quality Gate violations.");
      return;
    }
    try {
      setIsRevalidating(true);
      const latestDraft = await masterDataService.getManualDraft(draft.draft_id);
      onNext(latestDraft);
    } catch (err: any) {
      setError(err.message || "Failed to proceed to Step 6 Final Review.");
    } finally {
      setIsRevalidating(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: "40px", textAlign: "center", color: tokens.textMuted }}>
        <div>Evaluating Quality Gate Rules (IS 456, IS 10262 & Plant Operational Bounds)...</div>
      </div>
    );
  }

  const isClear = result?.overall_status === "QUALITY_CLEAR";
  const isBlocked = result?.overall_status === "BLOCKED";

  const categories = ["SCHEMA_DATA_INTEGRITY", "MATERIAL_PROPORTIONS", "WATER_CEMENTITIOUS_RATIO", "LABORATORY_QA_STRENGTH", "OPERATIONAL_PLANT_BOUNDS"];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "18px", color: tokens.textPrimary }}>
      {error && (
        <div
          style={{
            padding: "12px 16px",
            backgroundColor: tokens.statusErrorBg,
            border: `1px solid ${tokens.statusErrorBorder}`,
            borderRadius: tokens.radius,
            color: tokens.statusErrorText,
            fontSize: "0.85rem",
          }}
        >
          {error}
        </div>
      )}

      {/* Section 1: Quality Gate KPI Status Cards */}
      <div className="responsive-stat-grid">
        <div style={{ background: tokens.surfacePrimary, padding: "12px 14px", borderRadius: "8px", border: `1px solid ${tokens.border}`, boxShadow: tokens.shadowCard }}>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Data Quality Score</div>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: tokens.accent, marginTop: "2px" }}>
            {result?.data_quality_score ?? "--"}%
          </div>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted }}>Target: ≥ 85.0%</div>
        </div>

        <div style={{ background: tokens.surfacePrimary, padding: "12px 14px", borderRadius: "8px", border: `1px solid ${tokens.border}`, boxShadow: tokens.shadowCard }}>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Blocking Errors</div>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: (result?.error_count || 0) > 0 ? tokens.statusErrorText : tokens.statusSuccessText, marginTop: "2px" }}>
            {result?.error_count ?? 0}
          </div>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted }}>Must be 0 to proceed</div>
        </div>

        <div style={{ background: tokens.surfacePrimary, padding: "12px 14px", borderRadius: "8px", border: `1px solid ${tokens.border}`, boxShadow: tokens.shadowCard }}>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Warnings</div>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: (result?.warning_count || 0) > 0 ? tokens.statusWarningText : tokens.statusSuccessText, marginTop: "2px" }}>
            {result?.warning_count ?? 0}
          </div>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted }}>Non-blocking advisories</div>
        </div>

        <div style={{ background: tokens.surfacePrimary, padding: "12px 14px", borderRadius: "8px", border: `1px solid ${tokens.border}`, boxShadow: tokens.shadowCard }}>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Gate Status</div>
          <div
            style={{
              fontSize: "0.95rem",
              fontWeight: 800,
              color: isClear ? tokens.statusSuccessText : isBlocked ? tokens.statusErrorText : tokens.statusWarningText,
              marginTop: "4px",
            }}
          >
            {result?.overall_status}
          </div>
          <div style={{ fontSize: "0.72rem", color: tokens.textMuted }}>Authoritative Gate</div>
        </div>
      </div>

      {/* Section 2: Validation Rules Ledger */}
      <div>
        <h4 style={{ color: tokens.textPrimary, marginBottom: "0.5rem", fontSize: "0.92rem", fontWeight: 600 }}>
          Validation Rules Ledger & Provenance Metadata
        </h4>
        <div
          style={{
            background: tokens.surfaceSecondary,
            borderRadius: "8px",
            border: `1px solid ${tokens.border}`,
            padding: "12px 14px",
            maxHeight: "280px",
            overflowY: "auto",
          }}
        >
          {categories.map((cat) => {
            const categoryChecks = result?.checks.filter((c) => c.category === cat) || [];
            return (
              <div key={cat} style={{ marginBottom: "0.85rem" }}>
                <div style={{ fontSize: "0.75rem", fontWeight: 700, color: tokens.accent, marginBottom: "0.4rem", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                  {cat}
                </div>
                {categoryChecks.map((c) => {
                  const isPass = c.severity === "INFO";
                  const isWarn = c.severity === "WARNING";
                  const statusBg = isPass ? tokens.statusSuccessBg : isWarn ? tokens.statusWarningBg : tokens.statusErrorBg;
                  const statusBorder = isPass ? tokens.statusSuccessBorder : isWarn ? tokens.statusWarningBorder : tokens.statusErrorBorder;
                  const statusText = isPass ? tokens.statusSuccessText : isWarn ? tokens.statusWarningText : tokens.statusErrorText;

                  return (
                    <div
                      key={c.rule_code}
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "6px",
                        padding: "0.5rem 0.75rem",
                        background: tokens.surfacePrimary,
                        borderRadius: "6px",
                        border: `1px solid ${tokens.border}`,
                        marginBottom: "0.35rem",
                        fontSize: "0.8rem",
                      }}
                    >
                      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.5rem", flex: 1 }}>
                        <span
                          style={{
                            background: statusBg,
                            border: `1px solid ${statusBorder}`,
                            color: statusText,
                            fontWeight: 700,
                            fontSize: "0.72rem",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {isPass ? "✓ PASS" : isWarn ? "⚠️ WARN" : "✕ ERROR"}
                        </span>
                        <span style={{ color: tokens.textPrimary, fontWeight: 600 }}>{c.title}:</span>
                        <span className="text-wrap-safe" style={{ color: tokens.textSecondary }}>{c.message}</span>
                      </div>
                      {c.actual_value !== undefined && c.actual_value !== null && (
                        <div style={{ fontSize: "0.75rem", color: tokens.textMuted, fontFamily: "monospace" }}>
                          Actual: {String(c.actual_value)}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>

      {/* Section 3: Batch Summary & Authoritative Values */}
      <div>
        <h4 style={{ color: tokens.textPrimary, marginBottom: "0.5rem", fontSize: "0.92rem", fontWeight: 600 }}>
          Authoritative Batch & Mix Provenance Summary
        </h4>
        <div
          className="responsive-stat-grid"
          style={{
            background: tokens.surfaceSecondary,
            padding: "12px 14px",
            borderRadius: "8px",
            border: `1px solid ${tokens.border}`,
            fontSize: "0.82rem",
          }}
        >
          <div><span style={{ color: tokens.textMuted }}>Batch #:</span> <strong style={{ color: tokens.statusSuccessText }}>{result?.batch_number}</strong></div>
          <div><span style={{ color: tokens.textMuted }}>Plant:</span> <strong style={{ color: tokens.textPrimary }}>{result?.plant_code}</strong></div>
          <div><span style={{ color: tokens.textMuted }}>Recipe:</span> <strong style={{ color: tokens.textPrimary }}>{result?.recipe_code}</strong></div>
          <div><span style={{ color: tokens.textMuted }}>Total Binder:</span> <strong style={{ color: tokens.accent }}>{result?.total_binder_kg_m3 ? `${result.total_binder_kg_m3} kg/m³` : "N/A"}</strong></div>
          <div><span style={{ color: tokens.textMuted }}>Effective Water:</span> <strong style={{ color: tokens.accent }}>{result?.effective_water_kg_m3 ? `${result.effective_water_kg_m3} kg/m³` : "N/A"}</strong></div>
          <div><span style={{ color: tokens.textMuted }}>W/B Ratio:</span> <strong style={{ color: tokens.statusWarningText }}>{result?.w_b_ratio ? result.w_b_ratio.toFixed(3) : "N/A"}</strong></div>
          <div><span style={{ color: tokens.textMuted }}>Yield:</span> <strong style={{ color: tokens.accent }}>{result?.yield_volume_m3 ? `${result.yield_volume_m3} m³` : "N/A"}</strong></div>
          <div><span style={{ color: tokens.textMuted }}>Cost:</span> <strong style={{ color: tokens.statusWarningText }}>{result?.estimated_cost_per_m3 || "N/A"}</strong></div>
        </div>
      </div>

      {/* Section 4 & 5: Eligibility Summary & Action Gates */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "14px",
          background: isBlocked ? tokens.statusErrorBg : tokens.statusSuccessBg,
          border: `1px solid ${isBlocked ? tokens.statusErrorBorder : tokens.statusSuccessBorder}`,
          padding: "14px 16px",
          borderRadius: "8px",
        }}
      >
        <div style={{ fontSize: "0.85rem", lineHeight: 1.5, minWidth: "240px" }}>
          <div>
            <span style={{ color: tokens.textSecondary }}>Final Review Eligibility:</span>{" "}
            <strong style={{ color: result?.final_review_eligible ? tokens.statusSuccessText : tokens.statusErrorText }}>
              {result?.final_review_eligible ? "YES (Cleared for Step 6 Review)" : "NO (Blocked by Quality Engine)"}
            </strong>
          </div>
          <div>
            <span style={{ color: tokens.textSecondary }}>Production Submission:</span>{" "}
            <strong style={{ color: isBlocked ? tokens.statusErrorText : tokens.statusWarningText }}>
              {isBlocked ? "BLOCKED" : "PENDING FINAL REVIEW"}
            </strong>
          </div>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
          <button
            type="button"
            onClick={onBack}
            style={secondaryButtonBase}
          >
            ← Back to Step 4
          </button>

          <button
            type="button"
            onClick={handleProceedToStep6}
            disabled={isBlocked || isRevalidating}
            style={{
              ...primaryButtonBase,
              opacity: isBlocked || isRevalidating ? 0.6 : 1,
              cursor: isBlocked || isRevalidating ? "not-allowed" : "pointer",
            }}
          >
            {isRevalidating ? "Revalidating Gate..." : "Next: Final Review & Submit ➔"}
          </button>
        </div>
      </div>
    </div>
  );
};
