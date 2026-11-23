/**
 * Step 5: Real-Time Ingestion Job Execution Component.
 * Polls the real FastAPI backend endpoint /api/v1/ingestion/jobs/{job_id}
 * Displays progress, stage status, records persisted/rejected, and live log stream.
 * Enterprise Operations Light Theme Migration.
 * Zero simulated transitions or mock states.
 */

import React, { useEffect, useState } from "react";
import { datasetIngestionApi } from "../../services/datasetIngestionApi";
import {
  enterpriseLightTokens as tokens,
  primaryButtonBase,
  secondaryButtonBase,
} from "../manual-entry/enterpriseLightTokens";

export interface IngestionJobStatusDTO {
  job_id: string;
  session_id: string;
  dataset_id?: string;
  mapping_execution_id?: string;
  status: string;
  current_stage: string;
  progress_percent: string;
  worksheets_discovered: number;
  worksheets_processed: number;
  excluded_records: number;
  records_persisted: number;
  records_rejected: number;
  logs: string[];
}

interface Step5Props {
  jobData: { jobId: string; sessionId: string } | null;
  onCloseModal: () => void;
  onProceedToTraining?: () => void;
}

export const Step5JobExecution: React.FC<Step5Props> = ({ jobData, onCloseModal, onProceedToTraining }) => {
  const [jobStatus, setJobStatus] = useState<IngestionJobStatusDTO | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string>("");

  useEffect(() => {
    if (!jobData?.jobId) {
      setLoading(false);
      setErrorMsg("No active Ingestion Job ID found.");
      return;
    }

    let isSubscribed = true;
    let pollInterval: any = null;

    const fetchStatus = async () => {
      try {
        const res = await datasetIngestionApi.getJobStatus(jobData.jobId);
        if (isSubscribed) {
          setJobStatus(res);
          setLoading(false);

          if (res.status === "COMPLETED" || res.status === "FAILED") {
            if (pollInterval) clearInterval(pollInterval);
          }
        }
      } catch (err: any) {
        if (isSubscribed) {
          setErrorMsg(err.message || "Failed to fetch backend job status.");
          setLoading(false);
        }
      }
    };

    fetchStatus();
    pollInterval = setInterval(fetchStatus, 3000);

    return () => {
      isSubscribed = false;
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [jobData]);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "60px 0", color: tokens.textSecondary }}>
        <div style={{ fontSize: "2rem", marginBottom: "12px" }}>⚙️</div>
        <p style={{ fontWeight: 700, color: tokens.textPrimary, margin: "0 0 6px 0", fontSize: "1.05rem" }}>
          Connecting to Production Job Worker...
        </p>
        <span style={{ fontSize: "0.85rem", color: tokens.textMuted }}>
          Retrieving authoritative job status for Job ID: {jobData?.jobId || "N/A"}
        </span>
      </div>
    );
  }

  if (errorMsg) {
    return (
      <div
        style={{
          padding: "24px",
          backgroundColor: tokens.statusErrorBg,
          border: `1px solid ${tokens.statusErrorBorder}`,
          borderRadius: "8px",
          color: tokens.statusErrorText,
        }}
      >
        <h4 style={{ fontSize: "1.05rem", fontWeight: 700, margin: "0 0 8px 0" }}>❌ Ingestion Job Error</h4>
        <p style={{ fontSize: "0.85rem", color: tokens.textPrimary, marginBottom: "16px" }}>{errorMsg}</p>
        <button
          type="button"
          onClick={onCloseModal}
          style={secondaryButtonBase}
        >
          Close Wizard
        </button>
      </div>
    );
  }

  const isCompleted = jobStatus?.status === "COMPLETED";

  const metricCardStyle: React.CSSProperties = {
    padding: "14px",
    backgroundColor: tokens.surfacePrimary,
    border: `1px solid ${tokens.border}`,
    borderRadius: "8px",
    textAlign: "center",
    boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", color: tokens.textPrimary }}>
      {/* Header Info Banner */}
      <div
        style={{
          padding: "16px 20px",
          backgroundColor: tokens.surfaceSecondary,
          border: `1px solid ${tokens.border}`,
          borderRadius: "8px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <div style={{ fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.04em", color: tokens.textMuted, fontWeight: 600 }}>Ingestion Job ID</div>
          <div style={{ fontSize: "1.05rem", fontWeight: 700, color: tokens.accent, fontFamily: "monospace", marginTop: "2px" }}>{jobStatus?.job_id}</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.04em", color: tokens.textMuted, fontWeight: 600 }}>Session ID</div>
          <div style={{ fontSize: "0.85rem", fontWeight: 600, color: tokens.textPrimary, fontFamily: "monospace", marginTop: "2px" }}>{jobStatus?.session_id}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <span
            style={{
              backgroundColor: isCompleted ? tokens.statusSuccessBg : tokens.primaryAccentLight,
              border: `1px solid ${isCompleted ? tokens.statusSuccessBorder : tokens.primaryAccentBorder}`,
              color: isCompleted ? tokens.statusSuccessText : tokens.accent,
              padding: "6px 14px",
              borderRadius: "20px",
              fontSize: "0.82rem",
              fontWeight: 700,
            }}
          >
            {jobStatus?.status} ({jobStatus?.progress_percent})
          </span>
        </div>
      </div>

      {/* Progress & Current Stage Card */}
      <div style={{ padding: "18px 20px", backgroundColor: tokens.surfacePrimary, border: `1px solid ${tokens.border}`, borderRadius: "8px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: tokens.textPrimary }}>
            Current Stage: <span style={{ color: tokens.accent, fontWeight: 700 }}>{jobStatus?.current_stage}</span>
          </span>
          <span style={{ fontSize: "0.85rem", fontWeight: 700, color: tokens.statusSuccessText }}>{jobStatus?.progress_percent}</span>
        </div>
        <div style={{ width: "100%", height: "8px", backgroundColor: tokens.borderLight, borderRadius: "4px", overflow: "hidden" }}>
          <div
            style={{
              width: jobStatus?.progress_percent || "0%",
              height: "100%",
              backgroundColor: isCompleted ? tokens.statusSuccessText : tokens.accent,
              transition: "width 0.3s ease",
            }}
          />
        </div>
      </div>

      {/* Real Ingestion Execution Metric Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "12px" }}>
        <div style={metricCardStyle}>
          <div style={{ fontSize: "0.7rem", color: tokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Worksheets Discovered</div>
          <div style={{ fontSize: "1.3rem", fontWeight: 700, color: tokens.textPrimary, marginTop: "4px" }}>{jobStatus?.worksheets_discovered}</div>
        </div>
        <div style={metricCardStyle}>
          <div style={{ fontSize: "0.7rem", color: tokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Operational Processed</div>
          <div style={{ fontSize: "1.3rem", fontWeight: 700, color: tokens.accent, marginTop: "4px" }}>{jobStatus?.worksheets_processed}</div>
        </div>
        <div style={metricCardStyle}>
          <div style={{ fontSize: "0.7rem", color: tokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Excluded Worksheets</div>
          <div style={{ fontSize: "1.3rem", fontWeight: 700, color: tokens.statusWarningText, marginTop: "4px" }}>{jobStatus?.excluded_records}</div>
        </div>
        <div style={metricCardStyle}>
          <div style={{ fontSize: "0.7rem", color: tokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Records Persisted</div>
          <div style={{ fontSize: "1.3rem", fontWeight: 700, color: tokens.statusSuccessText, marginTop: "4px" }}>{jobStatus?.records_persisted}</div>
        </div>
        <div style={metricCardStyle}>
          <div style={{ fontSize: "0.7rem", color: tokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Records Rejected</div>
          <div style={{ fontSize: "1.3rem", fontWeight: 700, color: tokens.textMuted, marginTop: "4px" }}>{jobStatus?.records_rejected}</div>
        </div>
      </div>

      {/* Live Backend Execution Log */}
      <div
        style={{
          backgroundColor: "#1E293B",
          border: `1px solid ${tokens.border}`,
          borderRadius: "8px",
          padding: "16px",
          fontFamily: tokens.fontMono,
          fontSize: "0.78rem",
          color: "#4ADE80",
          maxHeight: "180px",
          overflowY: "auto", overflowX: "auto", WebkitOverflowScrolling: "touch",
        }}
      >
        <div style={{ fontSize: "0.72rem", color: "#94A3B8", marginBottom: "8px", fontWeight: 600 }}>⚡ Live Backend Execution Log</div>
        {jobStatus?.logs && jobStatus.logs.length > 0 ? (
          jobStatus.logs.map((log: string, idx: number) => (
            <div key={idx} style={{ marginBottom: "3px" }}>{log}</div>
          ))
        ) : (
          <div style={{ color: "#94A3B8" }}>
            {jobStatus?.status === "COMPLETED" ? "No additional backend log events emitted." : "Waiting for initial backend worker log events..."}
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "12px" }}>
        <button
          type="button"
          onClick={onCloseModal}
          style={secondaryButtonBase}
        >
          Continue in Background & Close Modal
        </button>
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            type="button"
            onClick={onCloseModal}
            style={secondaryButtonBase}
          >
            Return to Dashboard
          </button>
          {onProceedToTraining && (
            <button
              type="button"
              onClick={onProceedToTraining}
              style={{
                ...primaryButtonBase,
                backgroundColor: tokens.accent,
              }}
            >
              Proceed to Step 6: Model Training →
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
