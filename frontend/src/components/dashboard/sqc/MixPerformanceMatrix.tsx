import React, { useState, useMemo } from "react";
import { Layers, Info, ChevronLeft, ChevronRight } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { MixPerformanceListDTO } from "../../../services/reportingService";

interface MixPerformanceMatrixProps {
  data: MixPerformanceListDTO | null;
  isLoading: boolean;
}

export const MixPerformanceMatrix: React.FC<MixPerformanceMatrixProps> = ({
  data,
  isLoading,
}) => {
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  const items = useMemo(() => data?.items || [], [data?.items]);
  const hasData = items.length > 0;
  const totalItems = items.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  // Reset to page 1 if data length shrinks or filter changes
  React.useEffect(() => {
    setCurrentPage(1);
  }, [items.length, data?.scope_metadata?.plant_code, data?.scope_metadata?.date_from]);

  const paginatedItems = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return items.slice(startIndex, startIndex + pageSize);
  }, [items, currentPage, pageSize]);

  const startIndex = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endIndex = Math.min(currentPage * pageSize, totalItems);

  if (isLoading) {
    return (
      <div
        style={{
          padding: "24px",
          backgroundColor: "#FFFFFF",
          borderRadius: "10px",
          border: `1px solid ${tokens.borderLight}`,
          height: "220px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "20px",
        }}
      >
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>Loading mix performance matrix...</span>
      </div>
    );
  }

  const getStatusBadge = (status: string, compRate: number) => {
    if (status === "AWAITING_TESTS") {
      return (
        <span
          style={{
            fontSize: "0.68rem",
            fontWeight: 600,
            padding: "2px 8px",
            borderRadius: "4px",
            backgroundColor: "#F8FAFC",
            color: "#64748B",
            border: "1px solid #E2E8F0",
          }}
        >
          Awaiting Tests
        </span>
      );
    }

    if (compRate >= 95.0) {
      return (
        <span
          style={{
            fontSize: "0.68rem",
            fontWeight: 600,
            padding: "2px 8px",
            borderRadius: "4px",
            backgroundColor: "#ECFDF5",
            color: "#059669",
            border: "1px solid #A7F3D0",
          }}
        >
          Controlled
        </span>
      );
    } else if (compRate >= 80.0) {
      return (
        <span
          style={{
            fontSize: "0.68rem",
            fontWeight: 600,
            padding: "2px 8px",
            borderRadius: "4px",
            backgroundColor: "#FFFBEB",
            color: "#D97706",
            border: "1px solid #FDE68A",
          }}
        >
          Review Required
        </span>
      );
    } else {
      return (
        <span
          style={{
            fontSize: "0.68rem",
            fontWeight: 600,
            padding: "2px 8px",
            borderRadius: "4px",
            backgroundColor: "#FEF2F2",
            color: "#DC2626",
            border: "1px solid #FECACA",
          }}
        >
          Action Required
        </span>
      );
    }
  };

  return (
    <div
      style={{
        padding: "20px 24px",
        backgroundColor: "#FFFFFF",
        borderRadius: "10px",
        border: `1px solid ${tokens.borderLight}`,
        boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.02)",
        marginBottom: "20px",
        boxSizing: "border-box",
        minWidth: 0,
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Layers size={18} color={tokens.primaryAccent} />
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
              Mix Design & Grade Performance Matrix
            </h3>
          </div>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.78rem", color: tokens.textMuted }}>
            Authoritative 28-day quality compliance and strength margin breakdown by recipe
          </p>
        </div>

        {/* Page Size Selector */}
        {hasData && (
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.78rem", color: tokens.textMuted }}>
            <span>Show</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              style={{
                padding: "4px 8px",
                borderRadius: "4px",
                border: `1px solid ${tokens.border}`,
                backgroundColor: "#F8FAFC",
                color: tokens.textPrimary,
                fontSize: "0.78rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={25}>25</option>
            </select>
            <span>entries</span>
          </div>
        )}
      </div>

      {/* Table */}
      {!hasData ? (
        <div
          style={{
            padding: "30px",
            backgroundColor: "#F8FAFC",
            borderRadius: "8px",
            textAlign: "center",
            border: `1px dashed ${tokens.border}`,
          }}
        >
          <Info size={24} color={tokens.textMuted} style={{ marginBottom: "6px" }} />
          <div style={{ fontSize: "0.85rem", color: tokens.textSecondary, fontWeight: 600 }}>
            No recipe data found for selected scope
          </div>
        </div>
      ) : (
        <>
          <div className="dashboard-contained-scroll">
            <table className="dashboard-matrix-table">
              <thead>
                <tr style={{ borderBottom: `2px solid ${tokens.borderLight}`, textAlign: "left" }}>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem" }}>
                    Grade / Mix Design
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Total Batches
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    28D Tested
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Mean Strength
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Target (fck)
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Margin
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Variation (σ)
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "center" }}>
                    Compliance
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "center" }}>
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedItems.map((r) => {
                  const isUnderperforming = r.strength_margin_mpa != null && r.strength_margin_mpa < 0;
                  return (
                    <tr
                      key={r.recipe_code}
                      style={{
                        borderBottom: `1px solid ${tokens.borderLight}`,
                        backgroundColor: isUnderperforming ? "#FFFBFB" : "transparent",
                      }}
                    >
                      <td style={{ padding: "10px 12px" }}>
                        <div style={{ fontWeight: 600, color: tokens.textPrimary }}>{r.recipe_code}</div>
                        <div style={{ fontSize: "0.72rem", color: tokens.textMuted }}>{r.recipe_name}</div>
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", fontWeight: 600, color: tokens.textPrimary }}>
                        {r.total_batches.toLocaleString()}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", color: tokens.textSecondary }}>
                        {r.tested_batches_28d.toLocaleString()}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", fontWeight: 700, color: tokens.textPrimary }}>
                        {r.mean_strength_mpa != null ? `${r.mean_strength_mpa.toFixed(1)} MPa` : "—"}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", color: tokens.textMuted }}>
                        {r.target_strength_fck.toFixed(0)} MPa
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          fontWeight: 700,
                          color: (r.strength_margin_mpa ?? 0) >= 0 ? "#059669" : "#DC2626",
                        }}
                      >
                        {r.strength_margin_mpa != null ? `${r.strength_margin_mpa >= 0 ? "+" : ""}${r.strength_margin_mpa.toFixed(1)} MPa` : "—"}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", color: tokens.textSecondary }}>
                        {r.standard_deviation_mpa != null ? `±${r.standard_deviation_mpa.toFixed(1)}` : "—"}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "center", fontWeight: 600 }}>
                        {r.tested_batches_28d > 0 ? (
                          <span style={{ color: r.compliance_rate_pct >= 90 ? "#059669" : "#D97706" }}>
                            {r.compliance_rate_pct.toFixed(1)}%
                          </span>
                        ) : (
                          <span style={{ color: tokens.textMuted }}>—</span>
                        )}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "center" }}>
                        {getStatusBadge(r.stability_status, r.compliance_rate_pct)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: "14px",
              paddingTop: "12px",
              borderTop: `1px solid ${tokens.borderLight}`,
              flexWrap: "wrap",
              gap: "10px",
              fontSize: "0.78rem",
              color: tokens.textMuted,
            }}
          >
            <div>
              Showing <span style={{ fontWeight: 600, color: tokens.textPrimary }}>{startIndex}</span> to{" "}
              <span style={{ fontWeight: 600, color: tokens.textPrimary }}>{endIndex}</span> of{" "}
              <span style={{ fontWeight: 600, color: tokens.textPrimary }}>{totalItems}</span> mix designs
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <button
                type="button"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: "4px 8px",
                  borderRadius: "5px",
                  border: `1px solid ${tokens.border}`,
                  backgroundColor: currentPage === 1 ? "#F8FAFC" : "#FFFFFF",
                  color: currentPage === 1 ? tokens.textMuted : tokens.textPrimary,
                  cursor: currentPage === 1 ? "not-allowed" : "pointer",
                  fontSize: "0.76rem",
                  fontWeight: 600,
                }}
              >
                <ChevronLeft size={14} />
                <span>Prev</span>
              </button>

              <span style={{ padding: "0 6px", fontWeight: 600, color: tokens.textPrimary }}>
                {currentPage} / {totalPages}
              </span>

              <button
                type="button"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: "4px 8px",
                  borderRadius: "5px",
                  border: `1px solid ${tokens.border}`,
                  backgroundColor: currentPage === totalPages ? "#F8FAFC" : "#FFFFFF",
                  color: currentPage === totalPages ? tokens.textMuted : tokens.textPrimary,
                  cursor: currentPage === totalPages ? "not-allowed" : "pointer",
                  fontSize: "0.76rem",
                  fontWeight: 600,
                }}
              >
                <span>Next</span>
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
