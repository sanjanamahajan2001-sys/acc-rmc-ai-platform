/**
 * Step 4: Confirmation Component.
 * Session-backed production pre-ingestion confirmation view.
 * Consumes the active session_id, fetches authoritative confirmation summary,
 * displays dataset settings, import scope, workbook breakdown table, and executes server-validated confirmation.
 * Enterprise Operations Light Theme Migration.
 */

import React, { useEffect, useState } from "react";
import { datasetIngestionApi, WorkbookPreviewDTO } from "../../services/datasetIngestionApi";
import { masterDataService, TargetPlant } from "../../services/masterDataService";
import {
  enterpriseLightTokens as tokens,
  primaryButtonBase,
  secondaryButtonBase,
} from "../manual-entry/enterpriseLightTokens";

interface Step4Props {
  sessionId: string;
  formData: any;
  onNext: (jobData: { jobId: string; sessionId: string; confirmationSummary: any }) => void;
  onBack: () => void;
}

export const Step4Confirmation: React.FC<Step4Props> = ({ sessionId, formData, onNext, onBack }) => {
  const [summary, setSummary] = useState<any | null>(null);
  const [plantLabel, setPlantLabel] = useState<string>(formData.targetPlant || "");
  const [loading, setLoading] = useState<boolean>(true);
  const [confirming, setConfirming] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>("");

  useEffect(() => {
    const fetchSummary = async () => {
      setLoading(true);
      setErrorMsg("");
      try {
        const data = await datasetIngestionApi.getConfirmationSummary(sessionId);
        setSummary(data);
        try {
          const plants = await masterDataService.getTargetPlants();
          const found = plants.find(p => p.id === formData.targetPlant || p.plant_code === formData.targetPlant);
          if (found) {
            setPlantLabel(`${found.plant_name} (${found.plant_code})`);
          }
        } catch {
          // ignore
        }
      } catch (err: any) {
        setErrorMsg(err.message || "Failed to load session confirmation summary.");
      } finally {
        setLoading(false);
      }
    };

    if (sessionId) {
      fetchSummary();
    } else {
      setLoading(false);
      setErrorMsg("No active session ID provided.");
    }
  }, [sessionId]);

  const handleStartIngestionJob = async () => {
    if (!summary || !summary.can_proceed_confirmation || confirming) return;

    setConfirming(true);
    setErrorMsg("");
    try {
      const res = await datasetIngestionApi.confirmSession(sessionId);
      onNext({
        jobId: res.job_id,
        sessionId: res.session_id,
        confirmationSummary: summary,
      });
    } catch (err: any) {
      setErrorMsg(err.message || "Session confirmation failed server-side.");
      setConfirming(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "60px 0", color: tokens.textSecondary }}>
        <div style={{ fontSize: "2rem", marginBottom: "12px" }}>📋</div>
        <p style={{ fontWeight: 700, color: tokens.textPrimary, margin: "0 0 6px 0", fontSize: "1.05rem" }}>
          Loading Production Session Confirmation Summary
        </p>
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>
          Reading authoritative session scope and per-workbook reconciliation for session: {sessionId}
        </span>
      </div>
    );
  }

  if (errorMsg && !summary) {
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
          ⚠️ Confirmation Error: {errorMsg}
        </div>
        <button onClick={onBack} style={secondaryButtonBase}>
          ← Back to Column Mapping
        </button>
      </div>
    );
  }

  const workbookPreviews: WorkbookPreviewDTO[] = summary?.workbook_previews || [];
  const operationalSheetsReview = summary?.operational_requires_review ?? (summary?.total_requires_review ?? 0);

  const cardStyle: React.CSSProperties = {
    backgroundColor: tokens.surfacePrimary,
    border: `1px solid ${tokens.border}`,
    borderRadius: "8px",
    padding: "14px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", color: tokens.textPrimary }}>
      {errorMsg && (
        <div
          style={{
            backgroundColor: tokens.statusErrorBg,
            border: `1px solid ${tokens.statusErrorBorder}`,
            color: tokens.statusErrorText,
            padding: "12px 16px",
            borderRadius: "8px",
            fontSize: "0.85rem",
            fontWeight: 500,
          }}
        >
          ⚠️ {errorMsg}
        </div>
      )}

      {/* 1. Dataset Parameters Banner */}
      <div
        style={{
          backgroundColor: tokens.surfaceSecondary,
          border: `1px solid ${tokens.border}`,
          borderRadius: "8px",
          padding: "16px 20px",
        }}
      >
        <div style={{ fontSize: "0.75rem", fontWeight: 700, color: tokens.accent, textTransform: "uppercase", marginBottom: "12px", letterSpacing: "0.03em" }}>
          Target Ingestion Configuration
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px", fontSize: "0.82rem" }}>
          <div>
            <span style={{ color: tokens.textMuted }}>Dataset Name:</span>
            <div style={{ fontWeight: 600, color: tokens.textPrimary, marginTop: "2px" }}>{formData.datasetName}</div>
          </div>
          <div>
            <span style={{ color: tokens.textMuted }}>Period / Target Plant:</span>
            <div style={{ fontWeight: 600, color: tokens.textPrimary, marginTop: "2px" }}>{formData.datasetPeriod} — {plantLabel || formData.targetPlant}</div>
          </div>
          <div>
            <span style={{ color: tokens.textMuted }}>Authenticated Operator:</span>
            <div style={{ fontWeight: 600, color: tokens.textPrimary, marginTop: "2px" }}>{formData.operator}</div>
          </div>
          <div>
            <span style={{ color: tokens.textMuted }}>Session ID:</span>
            <div style={{ fontWeight: 600, color: tokens.accent, fontFamily: "monospace", marginTop: "2px" }}>{sessionId}</div>
          </div>
        </div>
      </div>

      {/* 2. Import Scope Summary Cards */}
      <div>
        <div style={{ fontSize: "0.85rem", fontWeight: 700, color: tokens.textPrimary, marginBottom: "10px" }}>
          Import Scope Summary
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "12px" }}>
          <div style={cardStyle}>
            <div style={{ fontSize: "0.7rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Uploaded Files</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: tokens.textPrimary, marginTop: "4px" }}>{summary?.total_files_mapped ?? 0}</div>
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: "0.7rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Worksheets Found</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: tokens.accent, marginTop: "4px" }}>{summary?.discovered_count ?? 0}</div>
          </div>
          <div style={{ ...cardStyle, border: `1px solid ${tokens.statusSuccessBorder}` }}>
            <div style={{ fontSize: "0.7rem", color: tokens.statusSuccessText, fontWeight: 600, textTransform: "uppercase" }}>Operational Sheets</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: tokens.statusSuccessText, marginTop: "4px" }}>{summary?.operational_count ?? 0}</div>
          </div>
          <div style={{ ...cardStyle, border: `1px solid ${tokens.statusWarningBorder}` }}>
            <div style={{ fontSize: "0.7rem", color: tokens.statusWarningText, fontWeight: 600, textTransform: "uppercase" }}>Excluded / Reference</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: tokens.statusWarningText, marginTop: "4px" }}>{summary?.excluded_count ?? 0}</div>
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: "0.7rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Operational Review</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: operationalSheetsReview > 0 ? tokens.statusWarningText : tokens.statusSuccessText, marginTop: "4px" }}>
              {operationalSheetsReview}
            </div>
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: "0.7rem", color: tokens.textMuted, fontWeight: 600, textTransform: "uppercase" }}>Missing Mandatory</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: (summary?.total_missing_mandatory ?? 0) > 0 ? tokens.statusErrorText : tokens.statusSuccessText, marginTop: "4px" }}>
              {summary?.total_missing_mandatory ?? 0}
            </div>
          </div>
        </div>
        <div style={{ fontSize: "0.75rem", color: tokens.textMuted, marginTop: "8px", fontFamily: "monospace" }}>
          Reconciliation Invariant: {summary?.discovered_count} Discovered = {summary?.operational_count} Operational + {summary?.excluded_count} Excluded
        </div>
      </div>

      {/* 3. Per-Workbook Scope Breakdown Table */}
      <div>
        <div style={{ fontSize: "0.85rem", fontWeight: 700, color: tokens.textPrimary, marginBottom: "10px" }}>
          Per-Workbook Scope Breakdown & Reconciliation
        </div>
        <div style={{ overflowX: "auto", backgroundColor: tokens.surfacePrimary, borderRadius: "8px", border: `1px solid ${tokens.border}` }}>
          <div style={{ width: "100%", overflowX: "auto", WebkitOverflowScrolling: "touch" }}><table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ backgroundColor: tokens.surfaceSecondary, borderBottom: `1px solid ${tokens.border}`, color: tokens.textMuted }}>
                <th style={{ padding: "10px 14px" }}>Workbook Filename</th>
                <th style={{ padding: "10px 14px" }}>Discovered Sheets</th>
                <th style={{ padding: "10px 14px" }}>Operational Sheets</th>
                <th style={{ padding: "10px 14px" }}>Excluded / Reference</th>
                <th style={{ padding: "10px 14px" }}>Classification & Status</th>
                <th style={{ padding: "10px 14px" }}>Default Active Sheet</th>
              </tr>
            </thead>
            <tbody>
              {workbookPreviews.map((wb, idx) => (
                <tr key={idx} style={{ borderBottom: `1px solid ${tokens.borderLight}` }}>
                  <td style={{ padding: "10px 14px", fontWeight: 600, color: tokens.textPrimary }}>{wb.filename}</td>
                  <td style={{ padding: "10px 14px", color: tokens.accent, fontWeight: 600 }}>{wb.total_discovered_sheets}</td>
                  <td style={{ padding: "10px 14px", color: tokens.statusSuccessText, fontWeight: 700 }}>{wb.operational_sheets_count}</td>
                  <td style={{ padding: "10px 14px", color: wb.excluded_sheets_count > 0 ? tokens.statusWarningText : tokens.textMuted }}>{wb.excluded_sheets_count}</td>
                  <td style={{ padding: "10px 14px" }}>
                    <span
                      style={{
                        padding: "3px 8px",
                        borderRadius: "4px",
                        fontSize: "0.72rem",
                        fontWeight: 700,
                        backgroundColor: wb.is_derived_only ? tokens.statusWarningBg : tokens.statusSuccessBg,
                        color: wb.is_derived_only ? tokens.statusWarningText : tokens.statusSuccessText,
                        border: `1px solid ${wb.is_derived_only ? tokens.statusWarningBorder : tokens.statusSuccessBorder}`,
                      }}
                    >
                      {wb.is_derived_only ? "DERIVED / REFERENCE ONLY (0 Records)" : "OPERATIONAL DATASET"}
                    </span>
                  </td>
                  <td style={{ padding: "10px 14px", color: wb.default_active_worksheet ? tokens.statusSuccessText : tokens.textMuted, fontFamily: "monospace", fontSize: "0.8rem" }}>
                    {wb.default_active_worksheet || "None (Disabled)"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table></div>
        </div>
      </div>

      {/* 4. Footer Action Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "12px" }}>
        <button
          type="button"
          onClick={onBack}
          disabled={confirming}
          style={secondaryButtonBase}
        >
          ← Back to Column Mapping
        </button>

        {summary?.can_proceed_confirmation ? (
          <button
            type="button"
            onClick={handleStartIngestionJob}
            disabled={confirming}
            style={{
              ...primaryButtonBase,
              padding: "10px 24px",
              fontSize: "0.9rem",
              opacity: confirming ? 0.7 : 1,
              cursor: confirming ? "not-allowed" : "pointer",
            }}
          >
            {confirming ? "⚡ Starting Ingestion Job..." : "Confirm & Start Ingestion Job →"}
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
            Return to Upload (Raw Ingestion Disabled)
          </button>
        )}
      </div>
    </div>
  );
};
