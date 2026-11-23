/**
 * Main Vite Page: Operations Dashboard Dataset Ingestion Module.
 */

import React, { useState } from "react";
import { UploadDropZone } from "../components/dataset-ingestion/UploadDropZone";
import { UploadQueue } from "../components/dataset-ingestion/UploadQueue";
import { ValidationSummaryCards } from "../components/dataset-ingestion/ValidationSummaryCards";
import { ValidationTable } from "../components/dataset-ingestion/ValidationTable";
import { datasetIngestionApi } from "../services/datasetIngestionApi";
import { FileUploadTaskDTO, UploadSessionDTO } from "../types/uploadContracts";
import { ValidationPreviewDTO } from "../types/validationContracts";

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
      session = await datasetIngestionApi.createSession("OPERATOR-UI-01");
      setActiveSession(session);
    }

    const newTasks: FileUploadTaskDTO[] = [];
    for (const file of files) {
      const task = await datasetIngestionApi.enqueueFile(session.session_id, file);
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
      const prev = await datasetIngestionApi.simulateFileLifecycle(
        session.session_id,
        newTasks[0].file_id,
        (updatedTask) => {
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
        backgroundColor: "#0c0f16",
        color: "#f3f4f6",
        fontFamily: "'Outfit', sans-serif",
      }}
    >
      {/* Module Title Header */}
      <div style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 800, color: "#ffffff" }}>
            Dataset Ingestion Wizard
          </h2>
          <p style={{ fontSize: "0.85rem", color: "#9ca3af", marginTop: "4px" }}>
            ACC Ready-Mix Concrete AI Platform — Workstream WS-03.4 Production Import Experience
          </p>
        </div>
        {activeSession && (
          <div
            style={{
              padding: "6px 14px",
              backgroundColor: "rgba(0, 229, 255, 0.1)",
              border: "1px solid rgba(0, 229, 255, 0.2)",
              borderRadius: "6px",
              fontSize: "0.8rem",
              fontWeight: 600,
              color: "#00e5ff",
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
            <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#ffffff" }}>
              Validation Preview: {preview.filename}
            </h3>

            {/* Worksheet Tabs */}
            <div style={{ display: "flex", gap: "8px" }}>
              {["BatchData", "Summary", "QualityLogs"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  style={{
                    padding: "6px 16px",
                    borderRadius: "6px",
                    border: `1px solid ${activeTab === tab ? "#00e5ff" : "rgba(255, 255, 255, 0.1)"}`,
                    backgroundColor: activeTab === tab ? "rgba(0, 229, 255, 0.15)" : "rgba(20, 24, 35, 0.5)",
                    color: activeTab === tab ? "#00e5ff" : "#9ca3af",
                    fontWeight: 600,
                    cursor: "pointer",
                    fontSize: "0.85rem",
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
