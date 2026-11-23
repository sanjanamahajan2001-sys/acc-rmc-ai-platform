import React, { useState, useMemo } from "react";
import { Zap, Info, ChevronLeft, ChevronRight, HelpCircle, ShieldCheck, Search } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { BinderEfficiencyDTO } from "../../../services/reportingService";

interface BinderIntensityMatrixProps {
  data: BinderEfficiencyDTO | null;
  isLoading: boolean;
}

export const BinderIntensityMatrix: React.FC<BinderIntensityMatrixProps> = ({
  data,
  isLoading,
}) => {
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [searchTerm, setSearchTerm] = useState<string>("");

  const rawRecipes = useMemo(() => data?.recipes || [], [data?.recipes]);
  const fleetSummary = data?.fleet_summary;

  const filteredRecipes = useMemo(() => {
    if (!searchTerm.trim()) return rawRecipes;
    const term = searchTerm.toLowerCase();
    return rawRecipes.filter(
      (r) =>
        r.recipe_code.toLowerCase().includes(term) ||
        r.grade.toLowerCase().includes(term)
    );
  }, [rawRecipes, searchTerm]);

  const totalItems = filteredRecipes.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  // Reset page when data or search changes
  React.useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, rawRecipes.length, data?.scope_metadata?.plant_code]);

  const paginatedRecipes = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRecipes.slice(start, start + pageSize);
  }, [filteredRecipes, currentPage, pageSize]);

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
          height: "240px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "20px",
        }}
      >
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>Loading binder intensity efficiency matrix...</span>
      </div>
    );
  }

  const getReliabilityBadge = (status: string) => {
    switch (status) {
      case "RELIABLE":
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
            Reliable (≥30 tests)
          </span>
        );
      case "LIMITED":
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
            Limited (5-29 tests)
          </span>
        );
      case "VERY_LOW":
        return (
          <span
            style={{
              fontSize: "0.68rem",
              fontWeight: 600,
              padding: "2px 8px",
              borderRadius: "4px",
              backgroundColor: "#FFF7ED",
              color: "#EA580C",
              border: "1px solid #FFEDD5",
            }}
          >
            Very Low (&lt;5 tests)
          </span>
        );
      case "NO_TESTS":
      default:
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
            No 28D Tests
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
      {/* Header & Fleet Benchmark Banner */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "16px",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Zap size={18} color="#D97706" />
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
              Binder Intensity & Material Efficiency Matrix
            </h3>
          </div>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.78rem", color: tokens.textMuted }}>
            Specific binder consumption efficiency per unit of achieved 28-day compressive strength (kg/m³/MPa)
          </p>
        </div>

        {/* Fleet Summary KPI Banner */}
        {fleetSummary && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "14px",
              padding: "6px 14px",
              backgroundColor: "#FFFBEB",
              border: "1px solid #FDE68A",
              borderRadius: "8px",
              fontSize: "0.78rem",
              flexWrap: "wrap",
            }}
          >
            <div>
              <span style={{ color: "#92400E", fontWeight: 500 }}>Fleet Mean Intensity: </span>
              <strong style={{ color: "#78350F", fontSize: "0.88rem" }}>
                {fleetSummary.fleet_avg_binder_intensity != null ? `${fleetSummary.fleet_avg_binder_intensity.toFixed(2)} kg/m³/MPa` : "—"}
              </strong>
            </div>
            <div style={{ height: "14px", width: "1px", backgroundColor: "#FCD34D" }} />
            <div>
              <span style={{ color: "#92400E", fontWeight: 500 }}>Tested Batches: </span>
              <strong style={{ color: "#78350F" }}>
                {fleetSummary.tested_28d_batch_count.toLocaleString()} / {fleetSummary.total_production_batches.toLocaleString()}
              </strong>
            </div>
          </div>
        )}
      </div>

      {/* Search and Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "4px 10px",
            borderRadius: "6px",
            border: `1px solid ${tokens.border}`,
            backgroundColor: "#F8FAFC",
          }}
        >
          <Search size={14} color={tokens.textMuted} />
          <input
            type="text"
            placeholder="Filter by grade / mix..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              border: "none",
              backgroundColor: "transparent",
              fontSize: "0.78rem",
              color: tokens.textPrimary,
              outline: "none",
              width: "150px",
            }}
          />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.78rem", color: tokens.textMuted }}>
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
      </div>

      {/* Table */}
      {filteredRecipes.length === 0 ? (
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
            {searchTerm ? "No recipes match the search filter" : "No binder efficiency records found for selected scope"}
          </div>
        </div>
      ) : (
        <>
          <div className="dashboard-contained-scroll">
            <table className="dashboard-matrix-table">
              <thead>
                <tr style={{ borderBottom: `2px solid ${tokens.borderLight}`, textAlign: "left" }}>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem" }}>
                    Grade / Recipe Code
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Total Batches
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    28D Tested
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Cement (kg/m³)
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Total Binder (kg/m³)
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    W/B
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Mean 28D Strength
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Binder Intensity
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "center" }}>
                    Reliability
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedRecipes.map((r) => {
                  return (
                    <tr
                      key={r.recipe_code}
                      style={{
                        borderBottom: `1px solid ${tokens.borderLight}`,
                      }}
                    >
                      <td style={{ padding: "10px 12px" }}>
                        <div style={{ fontWeight: 600, color: tokens.textPrimary }}>{r.recipe_code}</div>
                        <div style={{ fontSize: "0.72rem", color: tokens.textMuted }}>Grade: {r.grade} (fck: {r.target_strength_fck_mpa.toFixed(0)} MPa)</div>
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", fontWeight: 600, color: tokens.textPrimary }}>
                        {r.total_batches.toLocaleString()}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", color: tokens.textSecondary }}>
                        {r.tested_batches_28d.toLocaleString()}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", color: tokens.textSecondary }}>
                        {r.cement_content_kg_m3 != null ? `${r.cement_content_kg_m3.toFixed(1)}` : "—"}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", fontWeight: 600, color: tokens.textPrimary }}>
                        {r.total_binder_content_kg_m3 != null ? `${r.total_binder_content_kg_m3.toFixed(1)}` : "—"}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", fontWeight: 600, color: "#0369A1" }}>
                        {r.actual_wb_ratio != null ? r.actual_wb_ratio.toFixed(3) : "—"}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", fontWeight: 700, color: tokens.textPrimary }}>
                        {r.mean_28d_strength_mpa != null ? `${r.mean_28d_strength_mpa.toFixed(1)} MPa` : "—"}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          fontWeight: 800,
                          color: "#B45309",
                        }}
                      >
                        {r.binder_intensity_index_kg_m3_per_mpa != null ? (
                          <>
                            {r.binder_intensity_index_kg_m3_per_mpa.toFixed(2)}{" "}
                            <span style={{ fontSize: "0.68rem", fontWeight: 400, color: tokens.textMuted }}>kg/m³/MPa</span>
                          </>
                        ) : (
                          <span style={{ color: tokens.textMuted }}>—</span>
                        )}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "center" }}>
                        {getReliabilityBadge(r.sample_size_status)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
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
              <span style={{ fontWeight: 600, color: tokens.textPrimary }}>{totalItems}</span> recipes
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
