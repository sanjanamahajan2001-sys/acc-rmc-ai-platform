import React, { useState, useMemo } from "react";
import { Package, Info, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { MaterialConsumptionSummaryDTO } from "../../../services/reportingService";

interface MaterialConsumptionMatrixProps {
  data: MaterialConsumptionSummaryDTO | null;
  isLoading: boolean;
}

export const MaterialConsumptionMatrix: React.FC<MaterialConsumptionMatrixProps> = ({
  data,
  isLoading,
}) => {
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [searchTerm, setSearchTerm] = useState<string>("");

  const rawItems = useMemo(() => data?.items || [], [data?.items]);

  const filteredItems = useMemo(() => {
    if (!searchTerm.trim()) return rawItems;
    const term = searchTerm.toLowerCase();
    return rawItems.filter(
      (item) =>
        item.material_name.toLowerCase().includes(term) ||
        item.material_code.toLowerCase().includes(term) ||
        item.broad_category.toLowerCase().includes(term) ||
        item.category.toLowerCase().includes(term)
    );
  }, [rawItems, searchTerm]);

  const totalItems = filteredItems.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  // Reset pagination when data or search changes
  React.useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, rawItems.length, data?.scope_metadata?.plant_code]);

  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredItems.slice(start, start + pageSize);
  }, [filteredItems, currentPage, pageSize]);

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
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>Loading material consumption matrix...</span>
      </div>
    );
  }

  const getCategoryBadge = (broadCategory: string) => {
    const cat = (broadCategory || "").toUpperCase();
    if (cat.includes("BINDER") || cat.includes("CEMENT")) {
      return { bg: "#EFF6FF", color: "#1D4ED8", border: "#BFDBFE" };
    }
    if (cat.includes("MINERAL")) {
      return { bg: "#F5F3FF", color: "#6D28D9", border: "#DDD6FE" };
    }
    if (cat.includes("AGGREGATE")) {
      return { bg: "#F0FDF4", color: "#15803D", border: "#BBF7D0" };
    }
    if (cat.includes("WATER")) {
      return { bg: "#F0F9FF", color: "#0369A1", border: "#BAE6FD" };
    }
    if (cat.includes("CHEMICAL") || cat.includes("ADMIXTURE")) {
      return { bg: "#FAF5FF", color: "#7E22CE", border: "#E9D5FF" };
    }
    return { bg: "#F8FAFC", color: "#64748B", border: "#E2E8F0" };
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
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Package size={18} color={tokens.primaryAccent} />
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
              Material Consumption & Specific Density Matrix
            </h3>
          </div>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.78rem", color: tokens.textMuted }}>
            Authoritative batch weighment aggregation, planned vs actual variance, and density per cubic meter (kg/m³)
          </p>
        </div>

        {/* Search and Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
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
              placeholder="Search material..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                border: "none",
                backgroundColor: "transparent",
                fontSize: "0.78rem",
                color: tokens.textPrimary,
                outline: "none",
                width: "130px",
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
          </div>
        </div>
      </div>

      {/* Table */}
      {filteredItems.length === 0 ? (
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
            {searchTerm ? "No materials match the search term" : "No material consumption records found for selected scope"}
          </div>
        </div>
      ) : (
        <>
          <div className="dashboard-contained-scroll">
            <table className="dashboard-matrix-table">
              <thead>
                <tr style={{ borderBottom: `2px solid ${tokens.borderLight}`, textAlign: "left" }}>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem" }}>
                    Material
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem" }}>
                    Category
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Batches
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Planned (kg)
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Actual Batched (kg)
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Variance (kg)
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Variance (%)
                  </th>
                  <th style={{ padding: "10px 12px", color: tokens.textMuted, fontWeight: 700, textTransform: "uppercase", fontSize: "0.7rem", textAlign: "right" }}>
                    Unit Density
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedItems.map((item) => {
                  const badgeStyle = getCategoryBadge(item.broad_category || item.category);
                  const isHighVariance = Math.abs(item.variance_percentage) > 3.0;

                  return (
                    <tr
                      key={item.material_code}
                      style={{
                        borderBottom: `1px solid ${tokens.borderLight}`,
                        backgroundColor: isHighVariance ? "#FFFBFB" : "transparent",
                      }}
                    >
                      <td style={{ padding: "10px 12px" }}>
                        <div style={{ fontWeight: 600, color: tokens.textPrimary }}>{item.material_name}</div>
                        <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontFamily: tokens.fontMono }}>
                          {item.material_code}
                        </div>
                      </td>
                      <td style={{ padding: "10px 12px" }}>
                        <span
                          style={{
                            fontSize: "0.68rem",
                            fontWeight: 600,
                            padding: "2px 8px",
                            borderRadius: "4px",
                            backgroundColor: badgeStyle.bg,
                            color: badgeStyle.color,
                            border: `1px solid ${badgeStyle.border}`,
                          }}
                        >
                          {item.broad_category || item.category}
                        </span>
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", color: tokens.textSecondary, fontWeight: 500 }}>
                        {item.batch_count.toLocaleString()}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", color: tokens.textMuted }}>
                        {item.planned_quantity_kg.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", fontWeight: 700, color: tokens.textPrimary }}>
                        {item.actual_quantity_kg.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          fontWeight: 600,
                          color: item.variance_quantity_kg === 0 ? tokens.textMuted : item.variance_quantity_kg > 0 ? tokens.warningAmber : "#2563EB",
                        }}
                      >
                        {item.variance_quantity_kg >= 0 ? "+" : ""}
                        {item.variance_quantity_kg.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          fontWeight: 700,
                          color: Math.abs(item.variance_percentage) <= 2.0 ? tokens.successGreen : Math.abs(item.variance_percentage) <= 3.0 ? tokens.warningAmber : tokens.errorRed,
                        }}
                      >
                        {item.variance_percentage >= 0 ? "+" : ""}
                        {item.variance_percentage.toFixed(2)}%
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", fontWeight: 700, color: tokens.textPrimary }}>
                        {item.consumption_kg_per_m3.toFixed(1)} <span style={{ fontSize: "0.7rem", color: tokens.textMuted, fontWeight: 400 }}>kg/m³</span>
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
              <span style={{ fontWeight: 600, color: tokens.textPrimary }}>{totalItems}</span> materials
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
