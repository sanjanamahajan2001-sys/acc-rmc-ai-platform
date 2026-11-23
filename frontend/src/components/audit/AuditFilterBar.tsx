import React from "react";
import { Search, Filter, RotateCcw, Download } from "lucide-react";
import { AuditQueryParams } from "../../types/audit";
import { enterpriseLightTokens as tokens, formInputStyle, secondaryButtonBase } from "../manual-entry/enterpriseLightTokens";

interface AuditFilterBarProps {
  filters: AuditQueryParams;
  onFilterChange: (newFilters: Partial<AuditQueryParams>) => void;
  onResetFilters: () => void;
  onExport: () => void;
  exporting: boolean;
}

export const AuditFilterBar: React.FC<AuditFilterBarProps> = ({
  filters,
  onFilterChange,
  onResetFilters,
  onExport,
  exporting,
}) => {
  const selectStyle: React.CSSProperties = {
    ...formInputStyle,
    height: "38px",
    padding: "6px 12px",
    fontSize: "0.82rem",
    backgroundColor: "#FFFFFF",
    cursor: "pointer",
    minWidth: "140px",
  };

  return (
    <div
      style={{
        backgroundColor: tokens.surfacePrimary,
        border: `1px solid ${tokens.border}`,
        borderRadius: "8px",
        padding: "14px 16px",
        marginBottom: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
      }}
    >
      {/* Top Row: Search & Action Buttons */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "center", justifyContent: "space-between" }}>
        {/* Keyword Search */}
        <div style={{ position: "relative", flex: "1 1 280px", minWidth: "220px" }}>
          <Search
            size={16}
            color={tokens.textMuted}
            style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)" }}
          />
          <input
            type="text"
            placeholder="Search events by keyword, actor, IP, correlation ID..."
            value={filters.q || ""}
            onChange={(e) => onFilterChange({ q: e.target.value, page: 1 })}
            aria-label="Search audit events"
            style={{
              ...formInputStyle,
              paddingLeft: "36px",
              height: "38px",
              fontSize: "0.82rem",
              width: "100%",
            }}
          />
        </div>

        {/* Buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={onResetFilters}
            aria-label="Reset all filters"
            style={{
              ...secondaryButtonBase,
              minHeight: "38px",
              padding: "6px 14px",
              fontSize: "0.8rem",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <RotateCcw size={14} />
            <span>Reset</span>
          </button>


        </div>
      </div>

      {/* Bottom Row: Multi-Dropdown Filters */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "center" }}>
        {/* Module Filter */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: tokens.textMuted }}>Module:</span>
          <select
            value={filters.module || ""}
            onChange={(e) => onFilterChange({ module: e.target.value || undefined, page: 1 })}
            aria-label="Filter by module"
            style={selectStyle}
          >
            <option value="">All Modules</option>
            <option value="AUTH">Authentication (AUTH)</option>
            <option value="USER_ADMIN">User Management (USER_ADMIN)</option>
            <option value="DATA_INGESTION">Data Ingestion (DATA_INGESTION)</option>
            <option value="MANUAL_ENTRY">Manual Entry (MANUAL_ENTRY)</option>
            <option value="MODEL_TRAINING">Model Training (MODEL_TRAINING)</option>
            <option value="AI_MIX_OPTIMIZATION">Mix Optimization (AI_MIX_OPTIMIZATION)</option>
            <option value="SETTINGS">Settings & Governance (SETTINGS)</option>
            {/* <option value="QUALITY_QA">Quality & QA (QUALITY_QA)</option> */}
            {/* <option value="MASTER_DATA">Master Data (MASTER_DATA)</option> */}
            {/* <option value="SECURITY">Security & RBAC (SECURITY)</option> */}
          </select>
        </div>

        {/* Severity Filter */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: tokens.textMuted }}>Severity:</span>
          <select
            value={filters.severity || ""}
            onChange={(e) => onFilterChange({ severity: e.target.value || undefined, page: 1 })}
            aria-label="Filter by severity"
            style={selectStyle}
          >
            <option value="">All Severities</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>

        {/* Result Filter */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: tokens.textMuted }}>Result:</span>
          <select
            value={filters.result || ""}
            onChange={(e) => onFilterChange({ result: e.target.value || undefined, page: 1 })}
            aria-label="Filter by result"
            style={selectStyle}
          >
            <option value="">All Results</option>
            <option value="SUCCESS">Success</option>
            <option value="FAILURE">Failure</option>
            <option value="DENIED">Denied</option>
            <option value="QUARANTINED">Quarantined / Conflict</option>
          </select>
        </div>

        {/* Date From */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: tokens.textMuted }}>From:</span>
          <input
            type="date"
            value={filters.date_from ? filters.date_from.split("T")[0] : ""}
            onChange={(e) => onFilterChange({ date_from: e.target.value ? `${e.target.value}T00:00:00Z` : undefined, page: 1 })}
            aria-label="Filter start date"
            style={{ ...selectStyle, minWidth: "130px" }}
          />
        </div>

        {/* Date To */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: tokens.textMuted }}>To:</span>
          <input
            type="date"
            value={filters.date_to ? filters.date_to.split("T")[0] : ""}
            onChange={(e) => onFilterChange({ date_to: e.target.value ? `${e.target.value}T23:59:59Z` : undefined, page: 1 })}
            aria-label="Filter end date"
            style={{ ...selectStyle, minWidth: "130px" }}
          />
        </div>
      </div>
    </div>
  );
};
