import React, { useState } from "react";
import { enterpriseLightTokens as tokens } from "../manual-entry/enterpriseLightTokens";
import { Step1DatasetInformation } from "./Step1DatasetInformation";

interface DatasetFormValues {
  datasetName: string;
  datasetPeriod: string;
  datasetType: string;
  targetPlant: string;
  importProfile: string;
  remarks: string;
  operator: string;
}
import { UploadDropZone } from "./UploadDropZone";
import { UploadQueue } from "./UploadQueue";
import { Step3ColumnMapping } from "./Step3ColumnMapping";
import { Step4Confirmation } from "./Step4Confirmation";
import { Step5JobExecution } from "./Step5JobExecution";
import { Step6ModelTraining } from "./Step6ModelTraining";
import {
  datasetIngestionApi,
  RegisteredDatasetDTO,
  UploadSessionDTO,
} from "../../services/datasetIngestionApi";
import { FileUploadTaskDTO } from "../../types/uploadContracts";

interface DatasetIngestionModalWizardProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DatasetIngestionModalWizard: React.FC<DatasetIngestionModalWizardProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [formData, setFormData] = useState<DatasetFormValues>({
    datasetName: "",
    datasetPeriod: "2026-Q1",
    datasetType: "",
    targetPlant: "",
    importProfile: "",
    remarks: "",
    operator: "USER-ADMIN",
  });

  const [registeredDataset, setRegisteredDataset] = useState<RegisteredDatasetDTO | null>(null);
  const [activeSession, setActiveSession] = useState<UploadSessionDTO | null>(null);
  const [tasks, setTasks] = useState<FileUploadTaskDTO[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [confirmedJob, setConfirmedJob] = useState<{ jobId: string; sessionId: string } | null>(null);

  const handleFormChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleProceedToUploadFolder = async () => {
    setIsProcessing(true);
    try {
      // 1. Register Dataset Context in Backend
      const dataset = await datasetIngestionApi.registerDataset({
        dataset_name: formData.datasetName,
        dataset_period: formData.datasetPeriod,
        dataset_type_id: formData.datasetType,
        target_plant_id: formData.targetPlant,
        import_profile_id: formData.importProfile,
        operator_id: "USER-ADMIN",
        remarks: formData.remarks,
      });
      setRegisteredDataset(dataset);

      // 2. Create Persistent Upload Session bound to dataset_id
      const session = await datasetIngestionApi.createSession(dataset.dataset_id, formData.operator);
      setActiveSession(session);

      setCurrentStep(2);
    } catch (err: any) {
      alert(`Error initializing ingestion context: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFilesSelected = async (files: File[]) => {
    if (!activeSession) return;

    for (const file of files) {
      try {
        const res = await datasetIngestionApi.discoverWorkbook(activeSession.session_id, file);
        const task: FileUploadTaskDTO = {
          file_id: res.file.file_id,
          session_id: activeSession.session_id,
          filename: res.file.filename,
          file_size_bytes: res.file.file_size_bytes,
          status: "DISCOVERY_COMPLETE" as any,
          progress_percentage: 100,
          current_step_description: `Discovered ${res.file.worksheet_count} worksheets (${res.file.worksheet_names.join(", ")})`,
          worksheet_names: res.file.worksheet_names,
          total_rows_found: 0,
          rows_mapped: 0,
          rows_valid: 0,
          rows_invalid: 0,
          enqueued_at: new Date().toISOString(),
        };

        setTasks((prevTasks) => [...prevTasks, task]);
        setSelectedFileId(task.file_id);
      } catch (err: any) {
        alert(`Failed to discover file ${file.name}: ${err.message}`);
      }
    }
  };

  const steps = [
    "Dataset Information",
    "Upload Folder",
    "Column Mapping",
    "Confirmation",
    "Job Status",
    "Model Training",
  ];

  return (
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
        alignItems: "center",
        justifyContent: "center",
        zIndex: 2000,
        padding: "10px",
      }}
    >
      <div
        style={{
          width: "1020px",
          maxWidth: "98vw",
          maxHeight: "95vh",
          backgroundColor: tokens.surfacePrimary,
          border: `1px solid ${tokens.border}`,
          borderRadius: "12px",
          boxShadow: tokens.shadowModal,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: "18px 24px",
            borderBottom: `1px solid ${tokens.border}`,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            backgroundColor: tokens.surfaceSecondary,
          }}
        >
          <div>
            <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: tokens.textPrimary, margin: 0 }}>
              Dataset Import Wizard — Step {currentStep} of {steps.length}: {steps[currentStep - 1]}
            </h3>
            <p style={{ fontSize: "0.8rem", color: tokens.textMuted, margin: "3px 0 0 0" }}>
              ACC Ready-Mix Concrete AI Platform — Production Ingestion & Model Training Pipeline
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: tokens.textMuted,
              fontSize: "1.3rem",
              cursor: "pointer",
              padding: "4px 8px",
              lineHeight: 1,
            }}
          >
            ✕
          </button>
        </div>

        {/* Wizard Stepper Header */}
        <div
          style={{
            display: "flex",
            borderBottom: `1px solid ${tokens.border}`,
            backgroundColor: tokens.surfaceSecondary,
            overflowX: "auto",
            whiteSpace: "nowrap",
            WebkitOverflowScrolling: "touch",
          }}
        >
          {steps.map((label, idx) => {
            const stepNum = idx + 1;
            const isActive = stepNum === currentStep;
            const isCompleted = stepNum < currentStep;

            return (
              <div
                key={stepNum}
                className="wizard-stepper-item"
                style={{
                  textAlign: "center",
                  fontSize: "0.75rem",
                  fontWeight: isActive ? 700 : isCompleted ? 600 : 400,
                  color: isActive ? tokens.accent : isCompleted ? tokens.statusSuccessText : tokens.textMuted,
                  borderBottom: isActive ? `2px solid ${tokens.accent}` : "2px solid transparent",
                  backgroundColor: isActive ? "#EEF2FF" : "transparent",
                  transition: "all 0.15s ease",
                  padding: "10px 14px",
                }}
              >
                {isCompleted ? "✓ " : `${stepNum}. `}
                {label}
              </div>
            );
          })}
        </div>

        {/* Modal Body View per Step */}
        <div style={{ padding: "16px", overflowY: "auto", flex: 1, backgroundColor: tokens.pageBg }}>
          {currentStep === 1 && (
            <Step1DatasetInformation
              formData={formData}
              onChange={handleFormChange}
              onNext={handleProceedToUploadFolder}
            />
          )}

          {currentStep === 2 && (
            <div>
              <UploadDropZone onFilesSelected={handleFilesSelected} disabled={isProcessing} />
              <UploadQueue
                tasks={tasks}
                selectedFileId={selectedFileId || undefined}
                onSelectFile={(id) => setSelectedFileId(id)}
                onCancelTask={(id) => setTasks((prev) => prev.filter((t) => t.file_id !== id))}
              />
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: "24px" }}>
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  style={{
                    backgroundColor: tokens.surfacePrimary,
                    border: `1px solid ${tokens.border}`,
                    color: tokens.textSecondary,
                    padding: "9px 18px",
                    borderRadius: "6px",
                    fontWeight: 600,
                    cursor: "pointer",
                    fontSize: "0.85rem",
                  }}
                >
                  ← Back
                </button>
                <button
                  type="button"
                  disabled={tasks.length === 0}
                  onClick={() => setCurrentStep(3)}
                  style={{
                    backgroundColor: tasks.length > 0 ? tokens.accent : tokens.border,
                    color: tasks.length > 0 ? "#FFFFFF" : tokens.textMuted,
                    border: "none",
                    padding: "9px 22px",
                    borderRadius: "6px",
                    fontWeight: 600,
                    cursor: tasks.length > 0 ? "pointer" : "not-allowed",
                    fontSize: "0.85rem",
                    boxShadow: tasks.length > 0 ? "0 1px 3px rgba(79, 70, 197, 0.3)" : "none",
                  }}
                >
                  Proceed to Column Mapping →
                </button>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <Step3ColumnMapping
              sessionId={activeSession?.session_id || ""}
              onNext={() => setCurrentStep(4)}
              onBack={() => setCurrentStep(2)}
            />
          )}

          {currentStep === 4 && (
            <Step4Confirmation
              sessionId={activeSession?.session_id || ""}
              formData={formData}
              onNext={(jobData) => {
                setConfirmedJob({ jobId: jobData.jobId, sessionId: jobData.sessionId });
                setCurrentStep(5);
              }}
              onBack={() => setCurrentStep(3)}
            />
          )}

          {currentStep === 5 && (
            <Step5JobExecution
              jobData={confirmedJob}
              onCloseModal={onClose}
              onProceedToTraining={() => setCurrentStep(6)}
            />
          )}

          {currentStep === 6 && (
            <Step6ModelTraining onCloseWizard={onClose} />
          )}
        </div>
      </div>
    </div>
  );
};
