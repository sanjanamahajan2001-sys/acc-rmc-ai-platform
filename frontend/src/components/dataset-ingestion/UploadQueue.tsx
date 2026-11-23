/**
 * Modular Vite Component: Session Queue & Multi-File Card View.
 * Enterprise Operations Light Theme Migration.
 */

import React from "react";
import { FileUploadTaskDTO } from "../../types/uploadContracts";
import { enterpriseLightTokens as tokens } from "../manual-entry/enterpriseLightTokens";

interface UploadQueueProps {
  tasks: FileUploadTaskDTO[];
  selectedFileId?: string;
  onSelectFile: (fileId: string) => void;
  onCancelTask: (fileId: string) => void;
}

export const UploadQueue: React.FC<UploadQueueProps> = ({
  tasks,
  selectedFileId,
  onSelectFile,
  onCancelTask,
}) => {
  if (tasks.length === 0) return null;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        marginTop: "20px",
      }}
    >
      <h3 style={{ fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary, margin: "0 0 4px 0" }}>
        Ingestion Session Queue ({tasks.length} {tasks.length === 1 ? "File" : "Files"})
      </h3>
      {tasks.map((task) => {
        const isSelected = task.file_id === selectedFileId;
        const isCompleted = task.status === "GENERATING_PREVIEW" || task.status === "COMPLETED";

        return (
          <div
            key={task.file_id}
            onClick={() => onSelectFile(task.file_id)}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "12px 16px",
              backgroundColor: isSelected ? "#EEF2FF" : tokens.surfacePrimary,
              border: `1px solid ${isSelected ? tokens.accent : tokens.border}`,
              borderRadius: "8px",
              cursor: "pointer",
              transition: "all 0.15s ease",
              boxShadow: isSelected ? "0 1px 3px rgba(79, 70, 197, 0.1)" : "0 1px 2px rgba(0,0,0,0.02)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px", flex: 1 }}>
              <div style={{ fontSize: "1.4rem" }}>📊</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontWeight: 600, color: tokens.textPrimary, fontSize: "0.9rem" }}>
                    {task.filename}
                  </span>
                  <span
                    style={{
                      fontSize: "0.72rem",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      fontWeight: 700,
                      backgroundColor: isCompleted ? tokens.statusSuccessBg : tokens.primaryAccentLight,
                      color: isCompleted ? tokens.statusSuccessText : tokens.accent,
                      border: `1px solid ${isCompleted ? tokens.statusSuccessBorder : tokens.primaryAccentBorder}`,
                    }}
                  >
                    {task.status}
                  </span>
                </div>
                <div style={{ fontSize: "0.78rem", color: tokens.textMuted, marginTop: "2px" }}>
                  {task.current_step_description} ({(task.file_size_bytes / 1024).toFixed(1)} KB)
                </div>

                {/* Progress bar */}
                <div
                  style={{
                    width: "100%",
                    height: "4px",
                    backgroundColor: tokens.borderLight,
                    borderRadius: "2px",
                    marginTop: "6px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${task.progress_percentage}%`,
                      height: "100%",
                      backgroundColor: isCompleted ? tokens.statusSuccessText : tokens.accent,
                      transition: "width 0.3s ease",
                    }}
                  />
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onCancelTask(task.file_id);
              }}
              style={{
                background: "transparent",
                border: "none",
                color: tokens.statusErrorText,
                cursor: "pointer",
                padding: "4px 8px",
                fontSize: "0.8rem",
                fontWeight: 600,
                borderRadius: "4px",
              }}
            >
              Cancel
            </button>
          </div>
        );
      })}
    </div>
  );
};
