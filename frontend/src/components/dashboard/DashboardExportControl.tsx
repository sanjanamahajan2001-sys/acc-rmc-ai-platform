import React, { useState } from "react";
import { FileText, Code, Loader2 } from "lucide-react";
import { exportDashboardPDF, exportDashboardJSON } from "../../services/reportingService";
import { enterpriseLightTokens as tokens } from "../manual-entry/enterpriseLightTokens";

interface DashboardExportControlProps {
  plantCode?: string;
  recipeCode?: string;
  dateFrom?: string;
  dateTo?: string;
  runId?: string;
  candidateId?: string;
}

export const DashboardExportControl: React.FC<DashboardExportControlProps> = ({
  plantCode,
  recipeCode,
  dateFrom,
  dateTo,
  runId,
  candidateId,
}) => {
  const [downloadingPdf, setDownloadingPdf] = useState<boolean>(false);
  const [downloadingJson, setDownloadingJson] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleExportPDF = async () => {
    try {
      setDownloadingPdf(true);
      setError(null);
      await exportDashboardPDF({
        plant_code: plantCode,
        recipe_code: recipeCode,
        date_from: dateFrom,
        date_to: dateTo,
        run_id: runId,
        candidate_id: candidateId,
      });
    } catch (err: any) {
      console.error("PDF export failed:", err);
      setError("Failed to export PDF");
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleExportJSON = async () => {
    try {
      setDownloadingJson(true);
      setError(null);
      await exportDashboardJSON({
        plant_code: plantCode,
        recipe_code: recipeCode,
        date_from: dateFrom,
        date_to: dateTo,
        run_id: runId,
        candidate_id: candidateId,
      });
    } catch (err: any) {
      console.error("JSON export failed:", err);
      setError("Failed to export JSON");
    } finally {
      setDownloadingJson(false);
    }
  };

  const btnBaseStyle: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: "5px",
    padding: "6px 12px",
    borderRadius: "6px",
    fontSize: "0.78rem",
    fontWeight: 600,
    cursor: "pointer",
    transition: "all 0.15s ease",
    boxShadow: "0 1px 2px rgba(0,0,0,0.03)",
  };

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "8px",
      }}
      data-testid="dashboard-export-controls"
    >
      {error && (
        <span
          style={{
            fontSize: "0.75rem",
            color: tokens.errorRed,
            fontWeight: 500,
          }}
        >
          {error}
        </span>
      )}

      {/* PDF Export Button */}
      <button
        type="button"
        onClick={handleExportPDF}
        disabled={downloadingPdf}
        style={{
          ...btnBaseStyle,
          backgroundColor: "#DC2626",
          color: "#FFFFFF",
          border: "1px solid #B91C1C",
          opacity: downloadingPdf ? 0.7 : 1,
        }}
        title="Export Authoritative Operations PDF Report"
        data-testid="export-pdf-button"
      >
        {downloadingPdf ? (
          <Loader2 size={13} className="animate-spin" />
        ) : (
          <FileText size={13} />
        )}
        <span>{downloadingPdf ? "Generating..." : "Export PDF"}</span>
      </button>

      {/* JSON Export Button */}
      <button
        type="button"
        onClick={handleExportJSON}
        disabled={downloadingJson}
        style={{
          ...btnBaseStyle,
          backgroundColor: tokens.surfacePrimary,
          color: tokens.textPrimary,
          border: `1px solid ${tokens.border}`,
          opacity: downloadingJson ? 0.7 : 1,
        }}
        title="Export Authoritative Machine-Readable JSON Report"
        data-testid="export-json-button"
      >
        {downloadingJson ? (
          <Loader2 size={13} className="animate-spin" />
        ) : (
          <Code size={13} />
        )}
        <span>{downloadingJson ? "Exporting..." : "Export JSON"}</span>
      </button>
    </div>
  );
};
