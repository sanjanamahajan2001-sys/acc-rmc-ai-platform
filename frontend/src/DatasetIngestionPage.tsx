/**
 * Main Vite Page: Operations Dashboard Dataset Ingestion Module.
 * Enterprise Operations Light Theme Migration.
 */

import React, { useState } from "react";
import { UploadDropZone } from "./components/dataset-ingestion/UploadDropZone";
import { UploadQueue } from "./components/dataset-ingestion/UploadQueue";
import { ValidationSummaryCards } from "./components/dataset-ingestion/ValidationSummaryCards";
import { ValidationTable } from "./components/dataset-ingestion/ValidationTable";
import { datasetIngestionApi } from "./services/datasetIngestionApi";
import { FileUploadTaskDTO, UploadSessionDTO } from "./types/uploadContracts";
import { ValidationPreviewDTO } from "./types/validationContracts";
import { enterpriseLightTokens as tokens } from "./components/manual-entry/enterpriseLightTokens";

export const DatasetIngestionPage: React.FC = () => {
  const [activeSession, setActiveSession] = useState<UploadSessionDTO | null>(null);
  const [tasks, setTasks] = useState<FileUploadTaskDTO[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<string | undefined>();
  const [preview, setPreview] = useState<ValidationPreviewDTO | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>("BatchData");

  const handleFilesSelected = async (files: File[]) => {
    let session = activeSession;
    if (!session) {
      session = await (datasetIngestionApi as any).createSession("OPERATOR-UI-01", "DSET-01");
      setActiveSession(session);
    }

    const newTasks: FileUploadTaskDTO[] = [];
    for (const file of files) {
      const task = await (datasetIngestionApi as any).enqueueFile(session!.session_id, file);
      newTasks.push(task);
    }

    const updatedTasks = [...tasks, ...newTasks];
    setTasks(updatedTasks);
    if (!selectedFileId && newTasks.length > 0) {
      setSelectedFileId(newTasks[0].file_id);
    }

    // Auto-run simulation for first enqueued task
    if (newTasks.length > 0) {
      setIsProcessing(true);
      const prev = await (datasetIngestionApi as any).simulateFileLifecycle(
        session!.session_id,
        newTasks[0].file_id,
        (updatedTask: any) => {
          setTasks((prevTasks) =>
            prevTasks.map((t) => (t.file_id === updatedTask.file_id ? updatedTask : t))
          );
        }
      );
      setPreview(prev);
      setIsProcessing(false);
    }
  };

  const handleCancelTask = (fileId: string) => {
    setTasks((prev) => prev.filter((t) => t.file_id !== fileId));
    if (selectedFileId === fileId) {
      setSelectedFileId(undefined);
      setPreview(null);
    }
  };

  return (
    <div
      style={{
        padding: "30px 40px",
        minHeight: "100vh",
        backgroundColor: tokens.pageBg,
        color: tokens.textPrimary,
        fontFamily: tokens.fontFamily,
      }}
    >
      {/* Module Title Header */}
      <div style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ fontSize: "1.35rem", fontWeight: 800, color: tokens.textPrimary, margin: 0 }}>
            Dataset Ingestion Wizard
          </h2>
          <p style={{ fontSize: "0.85rem", color: tokens.textMuted, marginTop: "4px" }}>
            ACC Ready-Mix Concrete AI Platform — Workstream WS-03.4 Production Import Experience
          </p>
        </div>
        {activeSession && (
          <div
            style={{
              padding: "6px 14px",
              backgroundColor: tokens.primaryAccentLight,
              border: `1px solid ${tokens.primaryAccentBorder}`,
              borderRadius: "6px",
              fontSize: "0.8rem",
              fontWeight: 600,
              color: tokens.accent,
            }}
          >
            Session ID: {activeSession.session_id}
          </div>
        )}
      </div>

      {/* Upload Drag & Drop Zone */}
      <UploadDropZone onFilesSelected={handleFilesSelected} disabled={isProcessing} />

      {/* Multi-File Upload Queue */}
      <UploadQueue
        tasks={tasks}
        selectedFileId={selectedFileId}
        onSelectFile={(id) => setSelectedFileId(id)}
        onCancelTask={handleCancelTask}
      />

      {/* Validation Preview & Statistics View */}
      {preview && (
        <div style={{ marginTop: "32px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: tokens.textPrimary, margin: 0 }}>
              Validation Preview: {preview.filename}
            </h3>

            {/* Worksheet Tabs */}
            <div style={{ display: "flex", gap: "8px" }}>
              {["BatchData", "Summary", "QualityLogs"].map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setActiveTab(tab)}
                  style={{
                    padding: "6px 14px",
                    borderRadius: "6px",
                    border: `1px solid ${activeTab === tab ? tokens.accent : tokens.border}`,
                    backgroundColor: activeTab === tab ? "#EEF2FF" : tokens.surfacePrimary,
                    color: activeTab === tab ? tokens.accent : tokens.textSecondary,
                    fontWeight: activeTab === tab ? 700 : 500,
                    cursor: "pointer",
                    fontSize: "0.82rem",
                  }}
                >
                  📄 {tab}
                </button>
              ))}
            </div>
          </div>

          {/* Validation Summary Cards */}
          <ValidationSummaryCards statistics={preview.summary.statistics} />

          {/* Interactive Preview Table */}
          <ValidationTable rows={preview.preview_rows} />
        </div>
      )}
    </div>
  );
};
