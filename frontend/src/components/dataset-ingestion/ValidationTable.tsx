/**
 * Modular Vite Component: Interactive Validation Data Table.
 * Enterprise Operations Light Theme Migration.
 */

import React, { useState } from "react";
import { ValidationPreviewRowDTO } from "../../types/validationContracts";
import {
  enterpriseLightTokens as tokens,
  formInputStyle,
} from "../manual-entry/enterpriseLightTokens";

interface ValidationTableProps {
  rows: ValidationPreviewRowDTO[];
  onSelectRow?: (row: ValidationPreviewRowDTO) => void;
}

export const ValidationTable: React.FC<ValidationTableProps> = ({ rows, onSelectRow }) => {
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedRow, setSelectedRow] = useState<ValidationPreviewRowDTO | null>(null);

  if (!rows || rows.length === 0) {
    return (
      <div style={{ padding: "30px", textAlign: "center", color: tokens.textMuted }}>
        No validation rows available for this preview.
      </div>
    );
  }

  // Extract dynamic headers from first row
  const dynamicFieldKeys = Object.keys(rows[0]?.canonical_row?.fields || {});

  // Filter & Search
  const filteredRows = rows.filter((row) => {
    const matchesStatus =
      filterStatus === "ALL" ||
      (filterStatus === "PASSED" && row.is_valid) ||
      (filterStatus === "QUARANTINED" && row.quarantine_recommended) ||
      (filterStatus === "WARNING" && row.severity === "WARNING");

    const matchesSearch =
      !searchQuery ||
      row.excel_row_number.toString().includes(searchQuery) ||
      row.preview_row_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      row.validation_trace_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      JSON.stringify(row.canonical_row.fields).toLowerCase().includes(searchQuery.toLowerCase());

    return matchesStatus && matchesSearch;
  });

  return (
    <div
      style={{
        backgroundColor: tokens.surfacePrimary,
        border: `1px solid ${tokens.border}`,
        borderRadius: "8px",
        padding: "16px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
        color: tokens.textPrimary,
      }}
    >
      {/* Toolbar Controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "14px",
          gap: "12px",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {["ALL", "PASSED", "WARNING", "QUARANTINED"].map((status) => {
            const isSelected = filterStatus === status;
            return (
              <button
                key={status}
                type="button"
                onClick={() => setFilterStatus(status)}
                style={{
                  padding: "5px 12px",
                  borderRadius: "6px",
                  border: `1px solid ${isSelected ? tokens.accent : tokens.border}`,
                  backgroundColor: isSelected ? "#EEF2FF" : tokens.surfacePrimary,
                  color: isSelected ? tokens.accent : tokens.textSecondary,
                  fontWeight: isSelected ? 700 : 500,
                  cursor: "pointer",
                  fontSize: "0.78rem",
                  transition: "all 0.15s ease",
                }}
              >
                {status}
              </button>
            );
          })}
        </div>

        <input
          type="text"
          placeholder="Search row ID, trace ID or values..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            ...formInputStyle,
            width: "260px",
            padding: "6px 12px",
            fontSize: "0.8rem",
          }}
        />
      </div>

      {/* Dynamic Table Rendering */}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.82rem" }}>
          <thead>
            <tr style={{ backgroundColor: tokens.surfaceSecondary, borderBottom: `1px solid ${tokens.border}`, color: tokens.textMuted }}>
              <th style={{ padding: "8px 10px" }}>Preview Row ID</th>
              <th style={{ padding: "8px 10px" }}>Excel Row</th>
              <th style={{ padding: "8px 10px" }}>Worksheet</th>
              {/* Dynamic Headers from backend */}
              {dynamicFieldKeys.map((key) => (
                <th key={key} style={{ padding: "8px 10px", color: tokens.accent }}>
                  {key.replace("FIELD_", "")}
                </th>
              ))}
              <th style={{ padding: "8px 10px" }}>Status</th>
              <th style={{ padding: "8px 10px" }}>Quality Score</th>
              <th style={{ padding: "8px 10px" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => (
              <tr
                key={row.preview_row_id}
                onClick={() => {
                  setSelectedRow(row);
                  if (onSelectRow) onSelectRow(row);
                }}
                style={{
                  borderBottom: `1px solid ${tokens.borderLight}`,
                  backgroundColor: row.quarantine_recommended ? tokens.statusErrorBg : "transparent",
                  cursor: "pointer",
                }}
              >
                <td style={{ padding: "8px 10px", fontFamily: "monospace", fontSize: "0.75rem", color: tokens.accent }}>{row.preview_row_id}</td>
                <td style={{ padding: "8px 10px", fontWeight: 700, color: tokens.textPrimary }}>#{row.excel_row_number}</td>
                <td style={{ padding: "8px 10px", color: tokens.textSecondary }}>{row.worksheet_name}</td>

                {/* Dynamic Cell Values from backend canonical_row.fields */}
                {dynamicFieldKeys.map((key) => (
                  <td key={key} style={{ padding: "8px 10px", color: tokens.textPrimary }}>
                    {row.canonical_row.fields[key] !== undefined && row.canonical_row.fields[key] !== null
                      ? String(row.canonical_row.fields[key])
                      : "-"}
                  </td>
                ))}

                <td style={{ padding: "8px 10px" }}>
                  <span
                    style={{
                      padding: "2px 6px",
                      borderRadius: "4px",
                      fontSize: "0.72rem",
                      fontWeight: 700,
                      backgroundColor: row.is_valid ? tokens.statusSuccessBg : tokens.statusErrorBg,
                      color: row.is_valid ? tokens.statusSuccessText : tokens.statusErrorText,
                      border: `1px solid ${row.is_valid ? tokens.statusSuccessBorder : tokens.statusErrorBorder}`,
                    }}
                  >
                    {row.validation_status}
                  </span>
                </td>
                <td style={{ padding: "8px 10px", fontWeight: 700, color: row.quality_score >= 90 ? tokens.statusSuccessText : tokens.statusWarningText }}>
                  {row.quality_score.toFixed(0)}%
                </td>
                <td style={{ padding: "8px 10px" }}>
                  <button
                    type="button"
                    style={{ background: "none", border: "none", color: tokens.accent, cursor: "pointer", fontWeight: 600, fontSize: "0.78rem", padding: 0 }}
                  >
                    Inspect Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Row Detail Drawer Modal */}
      {selectedRow && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(15, 23, 42, 0.45)",
            backdropFilter: "blur(4px)",
            display: "flex",
            justifyContent: "flex-end",
            zIndex: 3000,
          }}
        >
          <div style={{ width: "480px", backgroundColor: tokens.surfacePrimary, borderLeft: `1px solid ${tokens.border}`, padding: "28px", overflowY: "auto", color: tokens.textPrimary, boxShadow: tokens.shadowModal }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: 0, color: tokens.textPrimary }}>Excel Row #{selectedRow.excel_row_number} Inspector</h3>
              <button
                type="button"
                onClick={() => setSelectedRow(null)}
                style={{ background: "none", border: "none", color: tokens.textMuted, fontSize: "1.2rem", cursor: "pointer", padding: "4px 8px" }}
              >
                ✕
              </button>
            </div>

            <div style={{ marginBottom: "12px" }}>
              <div style={{ fontSize: "0.75rem", color: tokens.textMuted }}>Preview Row ID</div>
              <div style={{ fontFamily: "monospace", fontSize: "0.85rem", color: tokens.accent, fontWeight: 600 }}>{selectedRow.preview_row_id}</div>
            </div>

            <div style={{ marginBottom: "16px" }}>
              <div style={{ fontSize: "0.75rem", color: tokens.textMuted }}>Validation Trace ID</div>
              <div style={{ fontFamily: "monospace", fontSize: "0.85rem", color: tokens.accent, fontWeight: 600 }}>{selectedRow.validation_trace_id}</div>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <h4 style={{ fontSize: "0.88rem", color: tokens.textPrimary, marginBottom: "8px", fontWeight: 700 }}>Backend Parsed Canonical Values</h4>
              <pre style={{ backgroundColor: tokens.surfaceSecondary, border: `1px solid ${tokens.border}`, padding: "12px", borderRadius: "6px", fontSize: "0.78rem", color: tokens.textPrimary, overflowX: "auto", fontFamily: tokens.fontMono }}>
                {JSON.stringify(selectedRow.canonical_row.fields, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
