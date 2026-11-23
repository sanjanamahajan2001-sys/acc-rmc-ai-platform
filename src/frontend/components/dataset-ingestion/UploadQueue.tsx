/**
 * Modular Vite Component: Session Queue & Multi-File Card View.
 */

import React from "react";
import { FileUploadTaskDTO } from "../../types/uploadContracts";

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
        gap: "12px",
        marginTop: "20px",
      }}
    >
      <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#f3f4f6" }}>
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
              padding: "14px 18px",
              backgroundColor: isSelected ? "rgba(0, 229, 255, 0.08)" : "rgba(20, 24, 35, 0.7)",
              border: `1px solid ${isSelected ? "#00e5ff" : "rgba(255, 255, 255, 0.08)"}`,
              borderRadius: "10px",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "14px", flex: 1 }}>
              <div style={{ fontSize: "1.5rem" }}>📊</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontWeight: 600, color: "#ffffff", fontSize: "0.95rem" }}>
                    {task.filename}
                  </span>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontWeight: 600,
                      backgroundColor: isCompleted ? "rgba(0, 255, 135, 0.15)" : "rgba(0, 229, 255, 0.15)",
                      color: isCompleted ? "#00ff87" : "#00e5ff",
                      border: `1px solid ${isCompleted ? "rgba(0, 255, 135, 0.3)" : "rgba(0, 229, 255, 0.3)"}`,
                    }}
                  >
                    {task.status}
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#9ca3af", marginTop: "4px" }}>
                  {task.current_step_description} ({(task.file_size_bytes / 1024).toFixed(1)} KB)
                </div>

                {/* Progress bar */}
                <div
                  style={{
                    width: "100%",
                    height: "4px",
                    backgroundColor: "rgba(255, 255, 255, 0.1)",
                    borderRadius: "2px",
                    marginTop: "8px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${task.progress_percentage}%`,
                      height: "100%",
                      backgroundColor: isCompleted ? "#00ff87" : "#00e5ff",
                      transition: "width 0.3s ease",
                    }}
                  />
                </div>
              </div>
            </div>

            <button
              onClick={(e) => {
                e.stopPropagation();
                onCancelTask(task.file_id);
              }}
              style={{
                background: "transparent",
                border: "none",
                color: "#ef4444",
                cursor: "pointer",
                padding: "6px 12px",
                fontSize: "0.85rem",
                borderRadius: "6px",
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
