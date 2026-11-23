import React, { useState } from "react";
import { CheckCircle2, AlertCircle, AlertTriangle, HelpCircle, ShieldCheck, ChevronDown, ChevronUp } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { BatchVarianceAnalysisDTO } from "../../../services/reportingService";

interface BatchWeighingVarianceChartProps {
  data: BatchVarianceAnalysisDTO | null;
  isLoading: boolean;
}

export const BatchWeighingVarianceChart: React.FC<BatchWeighingVarianceChartProps> = ({
  data,
  isLoading,
}) => {
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

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
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>Loading Annex E weighing variance analysis...</span>
      </div>
    );
  }

  const summary = data?.overall_summary;
  const categories = data?.categories || [];
  const hasData = summary && summary.total_weighments > 0;

  const toggleCategory = (code: string) => {
    setExpandedCategory((prev) => (prev === code ? null : code));
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
        boxSizing: "border-box",
        minWidth: 0,
        height: "100%",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <ShieldCheck size={18} color={tokens.primaryAccent} />
          <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
            {summary?.indicator_name || "IS 4926:2003 Annex E Weighment Tolerance Indicator"}
          </h3>
        </div>
        <p style={{ margin: "4px 0 0 0", fontSize: "0.78rem", color: tokens.textMuted }}>
          Weighing equipment & batching accuracy compliance under IS 4926 Clause E-1 (Binders ±2%, Agg/Water/SP ±3%)
        </p>
      </div>

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
          <HelpCircle size={28} color={tokens.textMuted} style={{ marginBottom: "8px" }} />
          <div style={{ fontSize: "0.85rem", fontWeight: 600, color: tokens.textSecondary }}>
            No batch weighment records available
          </div>
          <div style={{ fontSize: "0.75rem", color: tokens.textMuted, marginTop: "4px" }}>
            Weighment telemetry will appear as batches are dispatched from the batching plant.
          </div>
        </div>
      ) : (
        <>
          {/* Top Compliance Summary Bar */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
              gap: "10px",
              padding: "12px 14px",
              backgroundColor: "#F8FAFC",
              borderRadius: "8px",
              border: `1px solid ${tokens.borderLight}`,
              marginBottom: "16px",
            }}
          >
            <div>
              <div style={{ fontSize: "0.7rem", color: tokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>
                Compliance Rate
              </div>
              <div
                style={{
                  fontSize: "1.25rem",
                  fontWeight: 700,
                  color: summary.annex_e_compliance_rate_pct >= 90 ? tokens.successGreen : tokens.warningAmber,
                }}
              >
                {summary.annex_e_compliance_rate_pct.toFixed(1)}%
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.7rem", color: tokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>
                Compliant Weighments
              </div>
              <div style={{ fontSize: "1.15rem", fontWeight: 700, color: tokens.successGreen }}>
                {summary.compliant_weighments.toLocaleString()}
                <span style={{ fontSize: "0.72rem", color: tokens.textMuted, fontWeight: 400 }}> / {summary.classifiable_weighments.toLocaleString()}</span>
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.7rem", color: tokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>
                Breaches ({">"} Tol.)
              </div>
              <div style={{ fontSize: "1.15rem", fontWeight: 700, color: summary.non_compliant_weighments > 0 ? tokens.errorRed : tokens.successGreen }}>
                {summary.non_compliant_weighments.toLocaleString()}
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.7rem", color: tokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>
                Evaluated Batches
              </div>
              <div style={{ fontSize: "1.15rem", fontWeight: 700, color: tokens.textPrimary }}>
                {summary.annex_e_weighment_batch_count.toLocaleString()}
              </div>
            </div>

            {summary.unclassified_record_count > 0 && (
              <div>
                <div style={{ fontSize: "0.7rem", color: "#6D28D9", textTransform: "uppercase", fontWeight: 600 }}>
                  Not Classifiable
                </div>
                <div style={{ fontSize: "1.15rem", fontWeight: 700, color: "#6D28D9" }}>
                  {summary.unclassified_record_count.toLocaleString()}
                </div>
              </div>
            )}
          </div>

          {/* Unclassified Materials Warning if present */}
          {summary.unclassified_record_count > 0 && (
            <div
              style={{
                padding: "8px 12px",
                backgroundColor: "#FAF5FF",
                border: "1px solid #E9D5FF",
                borderRadius: "6px",
                fontSize: "0.76rem",
                color: "#6D28D9",
                marginBottom: "14px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <AlertCircle size={14} />
              <span>
                <strong>Unclassified Records ({summary.unclassified_record_count}):</strong> Material codes (
                {summary.unclassified_material_codes.join(", ")}) do not match IS 4926 standard categories and are treated as <em>Not Classifiable</em> (excluded from pass/fail calculations).
              </span>
            </div>
          )}

          {/* Categories Breakdown List */}
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", flex: 1 }}>
            {categories.map((cat) => {
              const isNotClassifiable = cat.compliance_status === "NOT_CLASSIFIABLE";
              const isExpanded = expandedCategory === cat.category_code;
              const compRate = cat.compliance_rate_pct ?? 0;
              const tolLabel = isNotClassifiable ? "Not Classifiable" : `±${cat.is4926_tolerance_pct?.toFixed(0)}%`;

              return (
                <div
                  key={cat.category_code}
                  style={{
                    border: `1px solid ${tokens.borderLight}`,
                    borderRadius: "8px",
                    overflow: "hidden",
                    backgroundColor: "#FFFFFF",
                  }}
                >
                  <div
                    onClick={() => toggleCategory(cat.category_code)}
                    style={{
                      padding: "10px 14px",
                      backgroundColor: "#FBFCFE",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      cursor: "pointer",
                      userSelect: "none",
                      gap: "10px",
                      flexWrap: "wrap",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      {isNotClassifiable ? (
                        <HelpCircle size={16} color="#6D28D9" />
                      ) : compRate >= 95 ? (
                        <CheckCircle2 size={16} color={tokens.successGreen} />
                      ) : compRate >= 80 ? (
                        <AlertTriangle size={16} color={tokens.warningAmber} />
                      ) : (
                        <AlertCircle size={16} color={tokens.errorRed} />
                      )}
                      <div>
                        <span style={{ fontSize: "0.82rem", fontWeight: 700, color: tokens.textPrimary }}>
                          {cat.category_name}
                        </span>
                        <span
                          style={{
                            marginLeft: "8px",
                            fontSize: "0.68rem",
                            fontWeight: 600,
                            padding: "1px 6px",
                            borderRadius: "4px",
                            backgroundColor: isNotClassifiable ? "#FAF5FF" : "#EFF6FF",
                            color: isNotClassifiable ? "#6D28D9" : "#1D4ED8",
                            border: `1px solid ${isNotClassifiable ? "#E9D5FF" : "#BFDBFE"}`,
                          }}
                        >
                          Tolerance: {tolLabel}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                      <div style={{ textAlign: "right" }}>
                        <span style={{ fontSize: "0.82rem", fontWeight: 700, color: isNotClassifiable ? "#6D28D9" : compRate >= 90 ? tokens.successGreen : tokens.warningAmber }}>
                          {isNotClassifiable ? "N/A" : `${compRate.toFixed(1)}%`}
                        </span>
                        <span style={{ fontSize: "0.72rem", color: tokens.textMuted, marginLeft: "4px" }}>
                          ({cat.compliant_count}/{cat.record_count})
                        </span>
                      </div>
                      {isExpanded ? <ChevronUp size={16} color={tokens.textMuted} /> : <ChevronDown size={16} color={tokens.textMuted} />}
                    </div>
                  </div>

                  {/* Expanded Material Details */}
                  {isExpanded && cat.materials && cat.materials.length > 0 && (
                    <div style={{ padding: "8px 14px", backgroundColor: "#F8FAFC", borderTop: `1px solid ${tokens.borderLight}`, overflowX: "auto", WebkitOverflowScrolling: "touch" }}>
                      <table style={{ width: "100%", minWidth: "560px", fontSize: "0.74rem", borderCollapse: "collapse" }}>
                        <thead>
                          <tr style={{ textAlign: "left", color: tokens.textMuted, borderBottom: `1px solid ${tokens.borderLight}` }}>
                            <th style={{ padding: "6px 8px" }}>Material</th>
                            <th style={{ padding: "6px 8px", textAlign: "right" }}>Records</th>
                            <th style={{ padding: "6px 8px", textAlign: "right" }}>Planned (kg)</th>
                            <th style={{ padding: "6px 8px", textAlign: "right" }}>Actual (kg)</th>
                            <th style={{ padding: "6px 8px", textAlign: "right" }}>Mean Var (%)</th>
                            <th style={{ padding: "6px 8px", textAlign: "right" }}>Max |Var| (%)</th>
                            <th style={{ padding: "6px 8px", textAlign: "center" }}>Compliance</th>
                          </tr>
                        </thead>
                        <tbody>
                          {cat.materials.map((m) => (
                            <tr key={m.material_code} style={{ borderBottom: `1px solid ${tokens.borderLight}` }}>
                              <td style={{ padding: "6px 8px", fontWeight: 600, color: tokens.textPrimary }}>
                                {m.material_name}
                              </td>
                              <td style={{ padding: "6px 8px", textAlign: "right", color: tokens.textSecondary }}>
                                {m.record_count}
                              </td>
                              <td style={{ padding: "6px 8px", textAlign: "right", color: tokens.textMuted }}>
                                {m.planned_quantity_kg.toLocaleString(undefined, { maximumFractionDigits: 1 })}
                              </td>
                              <td style={{ padding: "6px 8px", textAlign: "right", fontWeight: 600, color: tokens.textPrimary }}>
                                {m.actual_quantity_kg.toLocaleString(undefined, { maximumFractionDigits: 1 })}
                              </td>
                              <td style={{ padding: "6px 8px", textAlign: "right", fontWeight: 600, color: m.mean_variance_pct >= 0 ? tokens.warningAmber : "#2563EB" }}>
                                {m.mean_variance_pct >= 0 ? "+" : ""}{m.mean_variance_pct.toFixed(2)}%
                              </td>
                              <td style={{ padding: "6px 8px", textAlign: "right", color: tokens.textSecondary }}>
                                {m.max_abs_variance_pct.toFixed(2)}%
                              </td>
                              <td style={{ padding: "6px 8px", textAlign: "center" }}>
                                {m.compliance_status === "NOT_CLASSIFIABLE" ? (
                                  <span style={{ fontSize: "0.66rem", color: "#6D28D9", backgroundColor: "#FAF5FF", padding: "1px 6px", borderRadius: "4px" }}>
                                    Unclassified
                                  </span>
                                ) : (
                                  <span style={{ fontSize: "0.66rem", color: (m.compliance_rate_pct ?? 0) >= 90 ? tokens.successGreen : tokens.warningAmber, fontWeight: 700 }}>
                                    {m.compliance_rate_pct != null ? `${m.compliance_rate_pct.toFixed(1)}%` : "—"}
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};
