import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../context/AuthContext";
import {
  mlTrainingApi,
  MLTrainingJobDTO,
  ModelRegistryDTO,
} from "../../services/mlTrainingApi";
import { enterpriseLightTokens as tokens } from "../manual-entry/enterpriseLightTokens";

interface Step6ModelTrainingProps {
  onCloseWizard: () => void;
}

export const Step6ModelTraining: React.FC<Step6ModelTrainingProps> = ({
  onCloseWizard,
}) => {
  const { isSuperAdmin, isAdmin, isQualityHead, isLabTech, isAnalyst } = useAuth();

  // Fine-grained UI authorization
  const canTriggerTraining = isSuperAdmin || isAdmin || isQualityHead;
  const canActivateModel = isSuperAdmin || isAdmin || isQualityHead;
  const canViewML = isSuperAdmin || isAdmin || isQualityHead || isLabTech || isAnalyst;

  // Local component state
  const [activeModel, setActiveModel] = useState<ModelRegistryDTO | null>(null);
  const [allModels, setAllModels] = useState<ModelRegistryDTO[]>([]);
  const [currentJob, setCurrentJob] = useState<MLTrainingJobDTO | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Activation Confirmation Modal State
  const [selectedCandidate, setSelectedCandidate] = useState<ModelRegistryDTO | null>(null);
  const [activationReason, setActivationReason] = useState<string>("Explicit quality approval");
  const [isActivating, setIsActivating] = useState<boolean>(false);

  // Fetch initial active model and registry state
  const loadRegistryData = useCallback(async () => {
    if (!canViewML) {
      setIsLoading(false);
      return;
    }
    try {
      setErrorMsg(null);
      const [active, models] = await Promise.all([
        mlTrainingApi.getActiveModel(),
        mlTrainingApi.listModels(),
      ]);
      setActiveModel(active);
      setAllModels(models || []);
    } catch (err: any) {
      setErrorMsg(
        err?.status === 403
          ? "You do not have permission to view ML Model Registry data."
          : "Unable to load model registry information from operational server."
      );
    } finally {
      setIsLoading(false);
    }
  }, [canViewML]);

  useEffect(() => {
    loadRegistryData();
  }, [loadRegistryData]);

  // Polling loop for active training job
  useEffect(() => {
    if (!currentJob) return;

    // Terminal statuses where polling should immediately stop
    const terminalStates = ["SUCCEEDED", "FAILED", "TIMED_OUT", "CANCELLED", "RESOURCE_REJECTED"];
    if (terminalStates.includes(currentJob.status)) {
      if (currentJob.status === "SUCCEEDED") {
        loadRegistryData();
      }
      return;
    }

    const intervalId = setInterval(async () => {
      try {
        const updated = await mlTrainingApi.getJobStatus(currentJob.job_id);
        setCurrentJob(updated);
        if (updated.status === "SUCCEEDED") {
          loadRegistryData();
        }
      } catch (err) {
        clearInterval(intervalId);
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, [currentJob, loadRegistryData]);

  // Handle submit training job
  const handleStartTraining = async () => {
    if (!canTriggerTraining) {
      setErrorMsg("Unauthorized: Only Quality Head or Administrator can initiate model training.");
      return;
    }
    setIsSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const fp = "train_session_" + Date.now().toString(16).padStart(64, "0").slice(-64);
      const job = await mlTrainingApi.submitTrainingJob({
        dataset_fingerprint: fp,
        observation_count: 50,
        feature_schema_version: "1.0.0",
        execution_timeout_seconds: 600,
        is_dummy_test: false,
      });
      setCurrentJob(job);
      setSuccessMsg("Training job requested successfully. Processing in background.");
    } catch (err: any) {
      if (err?.status === 409) {
        setErrorMsg("A training job is already running. Please wait for the current training run to finish.");
      } else if (err?.status === 403) {
        setErrorMsg("Access Denied: You do not have permission to start training.");
      } else {
        setErrorMsg(err?.message || "Failed to start model training job.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle explicit model activation
  const handleConfirmActivation = async () => {
    if (!selectedCandidate) return;
    setIsActivating(true);
    setErrorMsg(null);

    try {
      await mlTrainingApi.activateModel(selectedCandidate.id, activationReason);
      setSuccessMsg(`Model '${selectedCandidate.model_version}' is now the ACTIVE production model.`);
      setSelectedCandidate(null);
      await loadRegistryData();
    } catch (err: any) {
      if (err?.status === 422) {
        setErrorMsg(`Activation Failed: The model artifact failed integrity or validation checks: ${err?.message}`);
      } else if (err?.status === 403) {
        setErrorMsg("Access Denied: You do not have the required permission to activate models.");
      } else {
        setErrorMsg(err?.message || "Failed to activate model.");
      }
    } finally {
      setIsActivating(false);
    }
  };

  const getStatusDescription = (status: string) => {
    switch (status) {
      case "QUEUED":
        return "Training request has been accepted and is waiting to run.";
      case "PRECHECKING":
        return "Checking data and system resources before training.";
      case "RUNNING":
        return "Model training is currently in progress.";
      case "SUCCEEDED":
        return "Training completed successfully. A candidate model is available for review.";
      case "FAILED":
        return "Training could not be completed. The current production model has not been changed.";
      case "TIMED_OUT":
        return "Training exceeded the allowed execution time. The current production model has not been changed.";
      case "RESOURCE_REJECTED":
        return "Training could not start because the server does not currently have sufficient resources.";
      case "CANCELLED":
        return "Training was cancelled. The current production model remains unchanged.";
      default:
        return status;
    }
  };

  if (!canViewML) {
    return (
      <div style={{ padding: "32px", textAlign: "center", backgroundColor: tokens.surfacePrimary, borderRadius: "8px", border: `1px solid ${tokens.border}` }}>
        <h4 style={{ color: tokens.statusErrorText, margin: "0 0 8px 0" }}>🔒 Access Restricted</h4>
        <p style={{ color: tokens.textSecondary, fontSize: "0.9rem" }}>
          You do not have permission to view or manage ML model training. Please contact your system administrator.
        </p>
        <button
          type="button"
          onClick={onCloseWizard}
          style={{ marginTop: "16px", padding: "8px 16px", backgroundColor: tokens.surfaceSecondary, border: `1px solid ${tokens.border}`, borderRadius: "6px", cursor: "pointer" }}
        >
          Close Wizard
        </button>
      </div>
    );
  }

  const candidateModels = allModels.filter((m) => m.deployment_status === "CANDIDATE");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", color: tokens.textPrimary }}>
      {/* Informational Alerts */}
      {errorMsg && (
        <div style={{ padding: "12px 16px", backgroundColor: tokens.statusErrorBg, border: `1px solid ${tokens.statusErrorBorder}`, borderRadius: "8px", color: tokens.statusErrorText, fontSize: "0.85rem" }}>
          ❌ {errorMsg}
        </div>
      )}
      {successMsg && (
        <div style={{ padding: "12px 16px", backgroundColor: tokens.statusSuccessBg, border: `1px solid ${tokens.statusSuccessBorder}`, borderRadius: "8px", color: tokens.statusSuccessText, fontSize: "0.85rem" }}>
          ✓ {successMsg}
        </div>
      )}

      {/* SECTION 1: Active Production Model Card */}
      <div style={{ backgroundColor: tokens.surfacePrimary, border: `1px solid ${tokens.border}`, borderRadius: "8px", padding: "18px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
          <h4 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
            CURRENT ACTIVE PRODUCTION MODEL
          </h4>
          <span style={{ backgroundColor: tokens.statusSuccessBg, border: `1px solid ${tokens.statusSuccessBorder}`, color: tokens.statusSuccessText, padding: "4px 10px", borderRadius: "12px", fontSize: "0.75rem", fontWeight: 700 }}>
            ● ACTIVE
          </span>
        </div>
        {activeModel ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", fontSize: "0.85rem" }}>
            <div>
              <span style={{ color: tokens.textMuted, display: "block", fontSize: "0.72rem", textTransform: "uppercase" }}>Model Version</span>
              <strong style={{ fontFamily: "monospace", color: tokens.accent }}>{activeModel.model_version}</strong>
            </div>
            <div>
              <span style={{ color: tokens.textMuted, display: "block", fontSize: "0.72rem", textTransform: "uppercase" }}>Algorithm</span>
              <strong>{activeModel.algorithm} ({activeModel.framework})</strong>
            </div>
            <div>
              <span style={{ color: tokens.textMuted, display: "block", fontSize: "0.72rem", textTransform: "uppercase" }}>Activated On</span>
              <span>{new Date(activeModel.deployment_timestamp).toLocaleString()}</span>
            </div>
            <div>
              <span style={{ color: tokens.textMuted, display: "block", fontSize: "0.72rem", textTransform: "uppercase" }}>Schema Version</span>
              <span>v{activeModel.feature_schema_version}</span>
            </div>
          </div>
        ) : (
          <p style={{ margin: 0, fontSize: "0.85rem", color: tokens.textSecondary }}>
            Standard Physical Inference Engine (Baseline Heuristic Active)
          </p>
        )}
      </div>

      {/* SECTION 2: Model Training Execution & Real Telemetry */}
      <div style={{ backgroundColor: tokens.surfacePrimary, border: `1px solid ${tokens.border}`, borderRadius: "8px", padding: "18px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
          <div>
            <h4 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
              MODEL TRAINING ORCHESTRATION & OBSERVABILITY
            </h4>
            <p style={{ margin: "4px 0 0 0", fontSize: "0.8rem", color: tokens.textSecondary }}>
              Train candidate XGBoost and ensemble models on qualified historical and operational production batches.
            </p>
          </div>
          {canTriggerTraining && (
            <button
              type="button"
              onClick={handleStartTraining}
              disabled={Boolean(isSubmitting || (currentJob && ["QUEUED", "PRECHECKING", "RUNNING", "SUCCEEDED"].includes(currentJob.status)))}
              style={{
                backgroundColor: currentJob?.status === "SUCCEEDED" ? tokens.statusSuccessText : tokens.accent,
                color: "#FFFFFF",
                border: "none",
                padding: "10px 20px",
                borderRadius: "6px",
                fontWeight: 600,
                fontSize: "0.85rem",
                cursor: isSubmitting || (currentJob && ["QUEUED", "PRECHECKING", "RUNNING", "SUCCEEDED"].includes(currentJob.status)) ? "not-allowed" : "pointer",
                opacity: isSubmitting || (currentJob && ["QUEUED", "PRECHECKING", "RUNNING"].includes(currentJob.status)) ? 0.6 : currentJob?.status === "SUCCEEDED" ? 0.9 : 1,
              }}
            >
              {isSubmitting
                ? "Submitting Request..."
                : currentJob?.status === "SUCCEEDED"
                ? "✓ Training Completed"
                : currentJob && ["QUEUED", "PRECHECKING", "RUNNING"].includes(currentJob.status)
                ? "Training in Progress..."
                : "Start Model Training"}
            </button>
          )}
        </div>

        {/* Live Training Job Telemetry Dashboard */}
        {currentJob && (
          <div style={{ marginTop: "16px", padding: "16px", border: `1px solid ${tokens.border}`, borderRadius: "8px", backgroundColor: "#F8FAFC" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
              <div>
                <span style={{ fontSize: "0.85rem", fontWeight: 700, color: tokens.textPrimary }}>
                  Job ID: <span style={{ fontFamily: "monospace", color: tokens.accent }}>{currentJob.job_id}</span>
                </span>
                <span style={{ marginLeft: "12px", fontSize: "0.78rem", color: tokens.textMuted }}>
                  Stage: <strong style={{ color: tokens.textPrimary }}>{currentJob.current_stage || currentJob.status}</strong>
                </span>
              </div>
              <span
                style={{
                  padding: "4px 12px",
                  borderRadius: "12px",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  backgroundColor:
                    currentJob.status === "SUCCEEDED"
                      ? tokens.statusSuccessBg
                      : currentJob.status === "FAILED" || currentJob.status === "RESOURCE_REJECTED"
                      ? tokens.statusErrorBg
                      : "#EEF2FF",
                  color:
                    currentJob.status === "SUCCEEDED"
                      ? tokens.statusSuccessText
                      : currentJob.status === "FAILED" || currentJob.status === "RESOURCE_REJECTED"
                      ? tokens.statusErrorText
                      : tokens.accent,
                }}
              >
                {currentJob.status}
              </span>
            </div>

            <p style={{ margin: "4px 0 10px 0", fontSize: "0.82rem", color: tokens.textSecondary }}>
              {getStatusDescription(currentJob.status)}
            </p>

            {/* Factual Execution Metrics Grid (Zero Fake Progress) */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "10px", marginBottom: "14px" }}>
              <div style={{ padding: "10px", backgroundColor: tokens.surfacePrimary, border: `1px solid ${tokens.border}`, borderRadius: "6px", textAlign: "center" }}>
                <span style={{ fontSize: "0.68rem", color: tokens.textMuted, textTransform: "uppercase", display: "block" }}>Records Processed</span>
                <strong style={{ fontSize: "1.05rem", color: tokens.accent }}>{currentJob.records_processed ?? 0}</strong>
              </div>
              <div style={{ padding: "10px", backgroundColor: tokens.surfacePrimary, border: `1px solid ${tokens.border}`, borderRadius: "6px", textAlign: "center" }}>
                <span style={{ fontSize: "0.68rem", color: tokens.textMuted, textTransform: "uppercase", display: "block" }}>Target Observations</span>
                <strong style={{ fontSize: "1.05rem", color: tokens.textPrimary }}>{currentJob.records_total ?? currentJob.observation_count}</strong>
              </div>
              <div style={{ padding: "10px", backgroundColor: tokens.surfacePrimary, border: `1px solid ${tokens.border}`, borderRadius: "6px", textAlign: "center" }}>
                <span style={{ fontSize: "0.68rem", color: tokens.textMuted, textTransform: "uppercase", display: "block" }}>Heartbeat</span>
                <span style={{ fontSize: "0.8rem", color: tokens.textSecondary }}>
                  {currentJob.last_heartbeat_at ? new Date(currentJob.last_heartbeat_at).toLocaleTimeString() : "--"}
                </span>
              </div>
            </div>

            {/* Live Sanitized Execution Logs */}
            {currentJob.execution_logs && currentJob.execution_logs.length > 0 && (
              <div
                style={{
                  backgroundColor: "#1E293B",
                  border: `1px solid ${tokens.border}`,
                  borderRadius: "6px",
                  padding: "12px",
                  fontFamily: tokens.fontMono,
                  fontSize: "0.75rem",
                  color: "#38BDF8",
                  maxHeight: "140px",
                  overflowY: "auto",
                }}
              >
                <div style={{ fontSize: "0.7rem", color: "#94A3B8", marginBottom: "6px", fontWeight: 600 }}>
                  ⚡ Real-Time Execution Milestones:
                </div>
                {currentJob.execution_logs.map((log: any, idx: number) => (
                  <div key={idx} style={{ marginBottom: "3px" }}>
                    <span style={{ color: "#94A3B8" }}>[{new Date(log.timestamp).toLocaleTimeString()}]</span>{" "}
                    <span style={{ color: log.severity === "ERROR" ? "#F87171" : "#4ADE80", fontWeight: 600 }}>
                      [{log.stage}]
                    </span>{" "}
                    <span style={{ color: "#F1F5F9" }}>{log.message}</span>
                  </div>
                ))}
              </div>
            )}

            {currentJob.failure_reason && (
              <div style={{ marginTop: "10px", padding: "8px 12px", backgroundColor: tokens.statusErrorBg, border: `1px solid ${tokens.statusErrorBorder}`, borderRadius: "6px", color: tokens.statusErrorText, fontSize: "0.8rem" }}>
                <strong>Failure Detail:</strong> {currentJob.failure_reason}
              </div>
            )}
          </div>
        )}
      </div>

      {/* SECTION 3: Candidate Models for Review */}
      <div style={{ backgroundColor: tokens.surfacePrimary, border: `1px solid ${tokens.border}`, borderRadius: "8px", padding: "18px" }}>
        <h4 style={{ margin: "0 0 12px 0", fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
          CANDIDATE MODELS AVAILABLE FOR REVIEW
        </h4>
        {candidateModels.length === 0 ? (
          <p style={{ margin: 0, fontSize: "0.85rem", color: tokens.textMuted }}>
            No candidate models currently pending review. Start a training job to generate a new candidate.
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {candidateModels.map((cand) => (
              <div
                key={cand.id}
                style={{
                  border: `1px solid ${tokens.border}`,
                  borderRadius: "6px",
                  padding: "14px",
                  backgroundColor: tokens.surfaceSecondary,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "12px",
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <strong style={{ fontFamily: "monospace", fontSize: "0.9rem", color: tokens.textPrimary }}>
                      {cand.model_version}
                    </strong>
                    <span style={{ backgroundColor: "#FEF3C7", color: "#92400E", padding: "2px 8px", borderRadius: "10px", fontSize: "0.7rem", fontWeight: 700 }}>
                      CANDIDATE
                    </span>
                  </div>
                  <div style={{ fontSize: "0.78rem", color: tokens.textSecondary, marginTop: "4px" }}>
                    Algorithm: {cand.algorithm} ({cand.framework}) | Schema: v{cand.feature_schema_version} | Created: {new Date(cand.created_at).toLocaleString()}
                  </div>
                </div>

                {canActivateModel && (
                  <button
                    type="button"
                    onClick={() => setSelectedCandidate(cand)}
                    style={{
                      backgroundColor: tokens.surfacePrimary,
                      border: `1px solid ${tokens.accent}`,
                      color: tokens.accent,
                      padding: "8px 16px",
                      borderRadius: "6px",
                      fontWeight: 600,
                      fontSize: "0.82rem",
                      cursor: "pointer",
                    }}
                  >
                    Review & Activate
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal: Controlled Model Activation Confirmation */}
      {selectedCandidate && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(15, 23, 42, 0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 3000,
            padding: "16px",
          }}
        >
          <div
            style={{
              backgroundColor: tokens.surfacePrimary,
              border: `1px solid ${tokens.border}`,
              borderRadius: "8px",
              padding: "24px",
              maxWidth: "520px",
              width: "100%",
              boxShadow: tokens.shadowModal,
            }}
          >
            <h3 style={{ margin: "0 0 12px 0", fontSize: "1.1rem", color: tokens.textPrimary }}>
              ⚠️ Confirm Production Model Activation
            </h3>
            <p style={{ fontSize: "0.85rem", color: tokens.textSecondary, lineHeight: 1.5, margin: "0 0 16px 0" }}>
              You are about to promote candidate model <strong style={{ color: tokens.textPrimary }}>{selectedCandidate.model_version}</strong> to <strong>ACTIVE</strong> production status.
            </p>
            <div style={{ backgroundColor: "#FFFBEB", border: "1px solid #FDE68A", padding: "12px", borderRadius: "6px", fontSize: "0.8rem", color: "#92400E", marginBottom: "16px" }}>
              <strong>Controlled Change Notice:</strong>
              <ul style={{ margin: "6px 0 0 0", paddingLeft: "18px" }}>
                <li>The current active model will be atomically set to <strong>RETIRED</strong>.</li>
                <li>Checksum and feature schema will be verified prior to activation.</li>
                <li>This event will be logged in the immutable Security Audit Trail.</li>
              </ul>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: tokens.textPrimary, marginBottom: "6px" }}>
                Activation Reason / Change Reference:
              </label>
              <input
                type="text"
                value={activationReason}
                onChange={(e) => setActivationReason(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: `1px solid ${tokens.border}`,
                  fontSize: "0.85rem",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
              <button
                type="button"
                onClick={() => setSelectedCandidate(null)}
                disabled={isActivating}
                style={{
                  padding: "8px 16px",
                  backgroundColor: tokens.surfaceSecondary,
                  border: `1px solid ${tokens.border}`,
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmActivation}
                disabled={isActivating}
                style={{
                  padding: "8px 18px",
                  backgroundColor: tokens.accent,
                  color: "#FFFFFF",
                  border: "none",
                  borderRadius: "6px",
                  cursor: isActivating ? "not-allowed" : "pointer",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                  opacity: isActivating ? 0.7 : 1,
                }}
              >
                {isActivating ? "Verifying & Activating..." : "Confirm Activation"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer Navigation */}
      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "12px" }}>
        <button
          type="button"
          onClick={onCloseWizard}
          style={{
            backgroundColor: tokens.surfacePrimary,
            border: `1px solid ${tokens.border}`,
            color: tokens.textSecondary,
            padding: "9px 20px",
            borderRadius: "6px",
            fontWeight: 600,
            cursor: "pointer",
            fontSize: "0.85rem",
          }}
        >
          Close Wizard & Return to Dashboard
        </button>
      </div>
    </div>
  );
};
