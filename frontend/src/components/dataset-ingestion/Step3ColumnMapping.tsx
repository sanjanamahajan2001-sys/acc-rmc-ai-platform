/**
 * Step 3: Column Mapping Review Component.
 * Displays authoritative WS-03.2 Canonical Mapping Engine metrics, multi-file/sheet selectors,
 * column mapping ledger, detected date parser pattern, and physical row traceable preview.
 * Enterprise Operations Light Theme Migration.
 * Zero hardcoded mock numbers or sample rows.
 */

import React, { useEffect, useState } from "react";
import { datasetIngestionApi, SessionMappingPreviewDTO, SheetMappingPreviewDTO } from "../../services/datasetIngestionApi";
import {
  enterpriseLightTokens as tokens,
  primaryButtonBase,
  secondaryButtonBase,
} from "../manual-entry/enterpriseLightTokens";

interface Step3Props {
  sessionId: string;
  onNext: () => void;
  onBack: () => void;
}

export const Step3ColumnMapping: React.FC<Step3Props> = ({ sessionId, onNext, onBack }) => {
  const [mappingPreview, setMappingPreview] = useState<SessionMappingPreviewDTO | null>(null);
  const [selectedFileId, setSelectedFileId] = useState<string>("");
  const [selectedSheetName, setSelectedSheetName] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string>("");

  useEffect(() => {
    const fetchMapping = async () => {
      setLoading(true);
      setErrorMsg("");
      try {
        const res = await datasetIngestionApi.createSessionMappingPreview(sessionId);
        setMappingPreview(res);
        if (res.sheet_previews && res.sheet_previews.length > 0) {
          setSelectedFileId(res.sheet_previews[0].file_id);
          setSelectedSheetName(res.sheet_previews[0].worksheet_name);
        }
      } catch (err: any) {
        setErrorMsg(err.message || "Failed to execute canonical column mapping for session");
      } finally {
        setLoading(false);
      }
    };

    if (sessionId) {
      fetchMapping();
    }
  }, [sessionId]);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "60px 0", color: tokens.textSecondary }}>
        <div style={{ fontSize: "2rem", marginBottom: "12px" }}>⚙️</div>
        <p style={{ fontWeight: 700, color: tokens.textPrimary, margin: "0 0 8px 0", fontSize: "1.05rem" }}>
          Running WS-03.2 Canonical Column Mapping Engine
        </p>
        <div style={{ display: "flex", justifyContent: "center", gap: "10px", marginBottom: "16px" }}>
          <span style={{ backgroundColor: tokens.primaryAccentLight, border: `1px solid ${tokens.primaryAccentBorder}`, padding: "4px 12px", borderRadius: "16px", fontSize: "0.8rem", color: tokens.accent, fontWeight: 600 }}>
            Status: RUNNING
          </span>
          <span style={{ backgroundColor: tokens.surfaceSecondary, border: `1px solid ${tokens.border}`, padding: "4px 12px", borderRadius: "16px", fontSize: "0.8rem", color: tokens.textMuted }}>
            Target: Active Upload Session Files & Worksheets
          </span>
        </div>
        <p style={{ fontSize: "0.85rem", color: tokens.textMuted, maxWidth: "480px", margin: "0 auto 8px auto", lineHeight: 1.5 }}>
          Streaming worksheet chunks, detecting logical header boundaries, resolving exact/alias/regex rules, and building sample preview rows...
        </p>
        <div style={{ fontSize: "0.75rem", color: tokens.statusSuccessText, fontFamily: "monospace", fontWeight: 600 }}>
          Persisting Session Execution Result (MAP-SESSION)
        </div>
      </div>
    );
  }

  if (errorMsg || !mappingPreview) {
    return (
      <div style={{ padding: "20px 0" }}>
        <div
          style={{
            backgroundColor: tokens.statusErrorBg,
            border: `1px solid ${tokens.statusErrorBorder}`,
            color: tokens.statusErrorText,
            padding: "16px",
            borderRadius: "8px",
            fontSize: "0.9rem",
            marginBottom: "20px",
            fontWeight: 500,
          }}
        >
          ⚠️ Mapping Engine Error: {errorMsg || "No mapping results returned for session."}
        </div>
        <button onClick={onBack} style={secondaryButtonBase}>
          ← Back to Upload Folder
        </button>
      </div>
    );
  }

  // Active Sheet & Workbook Filter
  const availableSheets = mappingPreview.sheet_previews;

  // Extract file list from workbook_previews or sheet_previews
  const workbookPreviews = mappingPreview.workbook_previews || [];
  const uniqueFiles = workbookPreviews.length > 0
    ? workbookPreviews.map((wp) => ({ file_id: wp.file_id, filename: wp.filename }))
    : Array.from(new Set(availableSheets.map((s) => JSON.stringify({ file_id: s.file_id, filename: s.filename })))).map(
        (str) => JSON.parse(str)
      );

  // Default selected file if empty
  const currentFileId = selectedFileId || (uniqueFiles.length > 0 ? uniqueFiles[0].file_id : "");

  // Find active workbook metadata
  const currentWorkbookPreview = workbookPreviews.find((wp) => wp.file_id === currentFileId);
  const isSelectedWorkbookDerivedOnly = currentWorkbookPreview
    ? currentWorkbookPreview.is_derived_only
    : availableSheets.filter((s) => s.file_id === currentFileId && s.is_applicable).length === 0;

  // Available operational sheets for selected file
  const operationalSheetsForFile = availableSheets.filter((s) => s.file_id === currentFileId && s.is_applicable);
  const totalDiscoveredForFile = availableSheets.filter((s) => s.file_id === currentFileId).length;

  // Calculate operational-only review requirements across all files
  const operationalReviewTotal = availableSheets
    .filter((s) => s.is_applicable)
    .reduce((sum, s) => sum + s.requires_review_count, 0);

  // Active operational sheet selection (NEVER select an excluded sheet like Mix Designs)
  const activeSheetPreview: SheetMappingPreviewDTO | undefined = isSelectedWorkbookDerivedOnly
    ? undefined
    : operationalSheetsForFile.find((s) => s.worksheet_name === selectedSheetName) || operationalSheetsForFile[0];

  const currentSheetName = isSelectedWorkbookDerivedOnly
    ? ""
    : (activeSheetPreview ? activeSheetPreview.worksheet_name : (selectedSheetName || (operationalSheetsForFile[0]?.worksheet_name || "")));

  const cardStyle: React.CSSProperties = {
    backgroundColor: tokens.surfacePrimary,
    padding: "16px",
    borderRadius: "8px",
    border: `1px solid ${tokens.border}`,
    boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", color: tokens.textPrimary }}>
      {/* Session & Active Sheet Scope Metrics */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        {/* Session Operational Scope */}
        <div style={cardStyle}>
          <div style={{ fontSize: "0.75rem", fontWeight: 700, color: tokens.accent, textTransform: "uppercase", marginBottom: "12px", letterSpacing: "0.03em" }}>
            Session Operational Scope ({mappingPreview.total_files_mapped} Files / {mappingPreview.operational_count ?? mappingPreview.total_sheets_mapped} Operational Sheets)
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
            <div>
              <div style={{ fontSize: "0.7rem", color: tokens.textMuted }}>Session Confidence</div>
              <div style={{ fontSize: "1.25rem", fontWeight: 700, color: tokens.statusSuccessText, marginTop: "2px" }}>{mappingPreview.overall_session_confidence}%</div>
            </div>
            <div>
              <div style={{ fontSize: "0.7rem", color: tokens.textMuted }}>Operational Sheets Review</div>
              <div style={{ fontSize: "1.25rem", fontWeight: 700, color: (mappingPreview.operational_requires_review ?? operationalReviewTotal) > 0 ? tokens.statusWarningText : tokens.statusSuccessText, marginTop: "2px" }}>
                {mappingPreview.operational_requires_review ?? operationalReviewTotal}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.7rem", color: tokens.textMuted }}>Missing Mandatory</div>
              <div style={{ fontSize: "1.25rem", fontWeight: 700, color: mappingPreview.total_missing_mandatory > 0 ? tokens.statusErrorText : tokens.statusSuccessText, marginTop: "2px" }}>
                {mappingPreview.total_missing_mandatory}
              </div>
            </div>
          </div>
          <div style={{ marginTop: "12px", fontSize: "0.72rem", color: tokens.textMuted, display: "flex", justifyContent: "space-between", borderTop: `1px solid ${tokens.borderLight}`, paddingTop: "8px" }}>
            <span>Engine Execution ID: <code style={{ color: tokens.accent, fontFamily: "monospace" }}>{mappingPreview.mapping_execution_id}</code></span>
            <span>Version: {mappingPreview.mapping_engine_version}</span>
          </div>
        </div>

        {/* Active Worksheet Scope or Derived / Reference Only Indicator */}
        <div
          style={{
            ...cardStyle,
            backgroundColor: isSelectedWorkbookDerivedOnly ? tokens.statusWarningBg : tokens.surfacePrimary,
            border: `1px solid ${isSelectedWorkbookDerivedOnly ? tokens.statusWarningBorder : tokens.border}`,
          }}
        >
          <div style={{ fontSize: "0.75rem", fontWeight: 700, color: isSelectedWorkbookDerivedOnly ? tokens.statusWarningText : tokens.statusSuccessText, textTransform: "uppercase", marginBottom: "12px", letterSpacing: "0.03em" }}>
            {isSelectedWorkbookDerivedOnly ? "Workbook Classification: Derived / Reference Only" : `Active Worksheet Scope (${activeSheetPreview ? activeSheetPreview.worksheet_name : "None"})`}
          </div>
          {isSelectedWorkbookDerivedOnly ? (
            <div style={{ fontSize: "0.85rem", color: tokens.textSecondary, lineHeight: 1.5 }}>
              Operational Worksheets: <strong style={{ color: tokens.textPrimary }}>0 / {totalDiscoveredForFile}</strong><br />
              <span style={{ color: tokens.statusWarningText, fontWeight: 600 }}>Raw Operational Ingestion Disabled</span>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
              <div>
                <div style={{ fontSize: "0.7rem", color: tokens.textMuted }}>Worksheet Confidence</div>
                <div style={{ fontSize: "1.25rem", fontWeight: 700, color: tokens.statusSuccessText, marginTop: "2px" }}>
                  {activeSheetPreview ? `${activeSheetPreview.overall_confidence_score}%` : "0%"}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.7rem", color: tokens.textMuted }}>Auto Mapped Columns</div>
                <div style={{ fontSize: "1.25rem", fontWeight: 700, color: tokens.accent, marginTop: "2px" }}>
                  {activeSheetPreview ? `${activeSheetPreview.auto_mapped_count} / ${activeSheetPreview.detected_columns_count}` : "0 / 0"}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.7rem", color: tokens.textMuted }}>Sheet Review Count</div>
                <div style={{ fontSize: "1.25rem", fontWeight: 700, color: activeSheetPreview && activeSheetPreview.requires_review_count > 0 ? tokens.statusWarningText : tokens.statusSuccessText, marginTop: "2px" }}>
                  {activeSheetPreview ? activeSheetPreview.requires_review_count : 0}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* File & Worksheet Multi-Selector Tabs */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {/* Workbook Files Selector */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.8rem", color: tokens.textMuted, fontWeight: 600, minWidth: "90px" }}>Workbook:</span>
          {uniqueFiles.map((f) => {
            const isSelected = f.file_id === currentFileId;
            const wbMeta = workbookPreviews.find((wp) => wp.file_id === f.file_id);
            const isDerived = wbMeta?.is_derived_only;

            return (
              <button
                key={f.file_id}
                type="button"
                onClick={() => {
                  setSelectedFileId(f.file_id);
                  const firstOpSheet = availableSheets.find((s) => s.file_id === f.file_id && s.is_applicable);
                  setSelectedSheetName(firstOpSheet ? firstOpSheet.worksheet_name : "");
                }}
                style={{
                  padding: "6px 14px",
                  borderRadius: "6px",
                  fontSize: "0.8rem",
                  fontWeight: isSelected ? 700 : 500,
                  backgroundColor: isSelected ? tokens.accent : tokens.surfacePrimary,
                  color: isSelected ? "#FFFFFF" : tokens.textPrimary,
                  border: `1px solid ${isSelected ? tokens.accent : tokens.border}`,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  boxShadow: isSelected ? "0 1px 3px rgba(79, 70, 197, 0.2)" : "none",
                }}
              >
                <span>📊 {f.filename}</span>
                {isDerived && (
                  <span
                    style={{
                      fontSize: "0.65rem",
                      backgroundColor: isSelected ? "rgba(255, 255, 255, 0.25)" : tokens.statusWarningBg,
                      color: isSelected ? "#FFFFFF" : tokens.statusWarningText,
                      border: `1px solid ${isSelected ? "rgba(255, 255, 255, 0.4)" : tokens.statusWarningBorder}`,
                      padding: "1px 5px",
                      borderRadius: "3px",
                      fontWeight: 700,
                    }}
                  >
                    REFERENCE
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Operational Sheets Selector */}
        {!isSelectedWorkbookDerivedOnly && (
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.8rem", color: tokens.textMuted, fontWeight: 600, minWidth: "90px" }}>Worksheet:</span>
            {operationalSheetsForFile.map((s) => {
              const isSelected = s.worksheet_name === currentSheetName;
              return (
                <button
                  key={s.worksheet_name}
                  type="button"
                  onClick={() => setSelectedSheetName(s.worksheet_name)}
                  style={{
                    padding: "5px 12px",
                    borderRadius: "6px",
                    fontSize: "0.78rem",
                    fontWeight: isSelected ? 700 : 500,
                    backgroundColor: isSelected ? "#EEF2FF" : tokens.surfacePrimary,
                    color: isSelected ? tokens.accent : tokens.textSecondary,
                    border: `1px solid ${isSelected ? tokens.accent : tokens.border}`,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <span>📄 {s.worksheet_name}</span>
                  {s.requires_review_count > 0 && (
                    <span
                      style={{
                        backgroundColor: tokens.statusWarningBg,
                        color: tokens.statusWarningText,
                        border: `1px solid ${tokens.statusWarningBorder}`,
                        borderRadius: "10px",
                        padding: "0 5px",
                        fontSize: "0.65rem",
                        fontWeight: 700,
                      }}
                    >
                      {s.requires_review_count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Main Workspace: Either Excluded Notice OR Active Operational Sheet View */}
      {isSelectedWorkbookDerivedOnly ? (
        <div
          style={{
            backgroundColor: tokens.statusWarningBg,
            border: `1px solid ${tokens.statusWarningBorder}`,
            borderRadius: "8px",
            padding: "24px",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "2rem", marginBottom: "8px" }}>📋</div>
          <h4 style={{ fontSize: "1.05rem", fontWeight: 700, color: tokens.statusWarningText, margin: "0 0 6px 0" }}>
            Reference / Historical Summary Workbook
          </h4>
          <p style={{ fontSize: "0.85rem", color: tokens.textSecondary, maxWidth: "560px", margin: "0 auto 16px auto", lineHeight: 1.5 }}>
            This workbook (<strong style={{ color: tokens.textPrimary }}>{currentWorkbookPreview?.filename}</strong>) contains aggregated summaries and forecast trend models. The system has automatically classified all {totalDiscoveredForFile} worksheets as reference-only.
          </p>
          <div style={{ backgroundColor: tokens.surfacePrimary, border: `1px solid ${tokens.border}`, padding: "12px 16px", borderRadius: "6px", fontSize: "0.82rem", color: tokens.textPrimary, display: "inline-block" }}>
            ℹ️ Operational mapping ledgers and physical previews are hidden for reference workbooks. No delivery notes or cube strength records will be created from this workbook.
          </div>
        </div>
      ) : (
        activeSheetPreview && (
          <>
            {/* Date Parser Inspection Box */}
            <div style={{ backgroundColor: tokens.surfaceSecondary, border: `1px solid ${tokens.border}`, borderRadius: "8px", padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <span style={{ fontSize: "0.8rem", color: tokens.textMuted }}>Detected Date Parser Pattern: </span>
                <span style={{ fontSize: "0.85rem", color: tokens.accent, fontWeight: 700, fontFamily: "monospace" }}>
                  {activeSheetPreview.date_parser_pattern || "Not detected"}
                </span>
              </div>
              <div>
                <span style={{ fontSize: "0.8rem", color: tokens.textMuted }}>Sample Parsed Value: </span>
                <span style={{ fontSize: "0.85rem", color: tokens.statusSuccessText, fontWeight: 700, fontFamily: "monospace" }}>
                  {activeSheetPreview.date_parser_preview || "Not detected"}
                </span>
              </div>
            </div>

            {/* Unified Schema Column Mapping Ledger */}
            <div>
              <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary, margin: "0 0 10px 0" }}>
                Unified Schema Mapping Ledger ({activeSheetPreview.worksheet_name})
              </h4>
              <div style={{ overflowX: "auto", backgroundColor: tokens.surfacePrimary, borderRadius: "8px", border: `1px solid ${tokens.border}` }}>
                <div style={{ width: "100%", overflowX: "auto", WebkitOverflowScrolling: "touch" }}><table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.85rem" }}>
                  <thead>
                    <tr style={{ backgroundColor: tokens.surfaceSecondary, borderBottom: `1px solid ${tokens.border}`, color: tokens.textMuted }}>
                      <th style={{ padding: "10px 12px" }}>Incoming Header</th>
                      <th style={{ padding: "10px 12px" }}>Canonical Target</th>
                      <th style={{ padding: "10px 12px" }}>Matching Strategy</th>
                      <th style={{ padding: "10px 12px" }}>Similarity Score</th>
                      <th style={{ padding: "10px 12px" }}>Review Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeSheetPreview.ledger.map((item, idx) => (
                      <tr key={idx} style={{ borderBottom: `1px solid ${tokens.borderLight}` }}>
                        <td style={{ padding: "10px 12px", color: tokens.textPrimary, fontWeight: 600 }}>{item.incoming_header}</td>
                        <td style={{ padding: "10px 12px", color: item.canonical_target_id ? tokens.accent : tokens.textMuted }}>
                          {item.canonical_target_name} {item.canonical_target_id && <span style={{ fontSize: "0.75rem", color: tokens.textMuted }}>({item.canonical_target_id})</span>}
                        </td>
                        <td style={{ padding: "10px 12px" }}>
                          <span style={{ padding: "2px 6px", borderRadius: "4px", fontSize: "0.72rem", fontWeight: 700, backgroundColor: tokens.surfaceSecondary, border: `1px solid ${tokens.border}`, color: item.resolution_strategy === "UNMAPPED" ? tokens.textMuted : tokens.statusSuccessText }}>
                            {item.resolution_strategy}
                          </span>
                        </td>
                        <td style={{ padding: "10px 12px", fontWeight: 700, color: item.resolution_strategy === "UNMAPPED" ? tokens.textMuted : tokens.textPrimary }}>
                          {item.resolution_strategy === "UNMAPPED" ? "N/A" : `${(item.similarity_score * 100).toFixed(0)}%`}
                        </td>
                        <td style={{ padding: "10px 12px" }}>
                          {item.requires_review ? (
                            <span style={{ color: tokens.statusWarningText, fontWeight: 700, fontSize: "0.75rem" }}>⚠️ Needs Review</span>
                          ) : (
                            <span style={{ color: tokens.statusSuccessText, fontWeight: 700, fontSize: "0.75rem" }}>✓ Auto Approved</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              </div>
            </div>

            {/* Traceable Physical Source-Derived Data Preview */}
            <div>
              <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary, margin: "0 0 10px 0" }}>
                Traceable Physical Source-Derived Data Preview (First 5 Rows from {activeSheetPreview.filename})
              </h4>
              <div style={{ overflowX: "auto", backgroundColor: tokens.surfacePrimary, borderRadius: "8px", border: `1px solid ${tokens.border}` }}>
                <div style={{ width: "100%", overflowX: "auto", WebkitOverflowScrolling: "touch" }}><table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.8rem" }}>
                  <thead>
                    <tr style={{ backgroundColor: tokens.surfaceSecondary, borderBottom: `1px solid ${tokens.border}`, color: tokens.textMuted }}>
                      <th style={{ padding: "10px 12px" }}>File & Row Lineage</th>
                      {activeSheetPreview.ledger.map((l, i) => (
                        <th key={i} style={{ padding: "10px 12px", color: l.canonical_target_id ? tokens.accent : tokens.textMuted }}>
                          {l.canonical_target_id ? l.canonical_target_name : l.incoming_header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {activeSheetPreview.sample_rows.map((row, rIdx) => (
                      <tr key={rIdx} style={{ borderBottom: `1px solid ${tokens.borderLight}` }}>
                        <td style={{ padding: "10px 12px", fontFamily: "monospace", fontSize: "0.75rem", color: tokens.textMuted }}>
                          Row #{row.physical_excel_row} ({row.worksheet_name})
                        </td>
                        {activeSheetPreview.ledger.map((l, i) => {
                          const val = l.canonical_target_id ? row.canonical_fields[l.canonical_target_id] : row.canonical_fields[l.incoming_header];
                          return (
                            <td key={i} style={{ padding: "10px 12px", color: val !== undefined && val !== null ? tokens.textPrimary : tokens.textMuted }}>
                              {val !== undefined && val !== null ? String(val) : "-"}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              </div>
            </div>
          </>
        )
      )}

      {/* Footer Navigation */}
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "12px" }}>
        <button type="button" onClick={onBack} style={secondaryButtonBase}>
          ← Back
        </button>
        {mappingPreview.can_proceed_confirmation ? (
          <button type="button" onClick={onNext} style={primaryButtonBase}>
            Proceed to Confirmation →
          </button>
        ) : (
          <button
            type="button"
            onClick={onBack}
            style={{
              backgroundColor: tokens.statusWarningBg,
              border: `1px solid ${tokens.statusWarningBorder}`,
              color: tokens.statusWarningText,
              padding: "9px 20px",
              borderRadius: "6px",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Return to Upload
          </button>
        )}
      </div>
    </div>
  );
};
