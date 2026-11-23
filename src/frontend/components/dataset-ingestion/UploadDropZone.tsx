/**
 * Modular Vite Component: Drag & Drop Ingestion File Upload Zone.
 */

import React, { useRef, useState } from "react";

interface UploadDropZoneProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

export const UploadDropZone: React.FC<UploadDropZoneProps> = ({ onFilesSelected, disabled }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const selected = Array.from(e.dataTransfer.files);
      onFilesSelected(selected);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selected = Array.from(e.target.files);
      onFilesSelected(selected);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && fileInputRef.current?.click()}
      style={{
        border: `2px dashed ${isDragOver ? "#00e5ff" : "rgba(255, 255, 255, 0.15)"}`,
        borderRadius: "12px",
        padding: "40px 20px",
        textAlign: "center",
        backgroundColor: isDragOver ? "rgba(0, 229, 255, 0.05)" : "rgba(20, 24, 35, 0.5)",
        cursor: disabled ? "not-allowed" : "pointer",
        transition: "all 0.3s ease",
        backdropFilter: "blur(12px)",
        boxShadow: isDragOver ? "0 0 25px rgba(0, 229, 255, 0.2)" : "none",
      }}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        multiple
        accept=".xlsx,.xls,.csv"
        style={{ display: "none" }}
      />
      <div style={{ fontSize: "2.5rem", marginBottom: "12px", color: "#00e5ff" }}>📂</div>
      <h3 style={{ fontSize: "1.1rem", fontWeight: 600, color: "#ffffff", marginBottom: "8px" }}>
        Drag & Drop Excel or CSV Datasets Here
      </h3>
      <p style={{ fontSize: "0.85rem", color: "#9ca3af", marginBottom: "16px" }}>
        Supports <span style={{ color: "#00e5ff" }}>.xlsx</span>, <span style={{ color: "#00e5ff" }}>.xls</span>, and <span style={{ color: "#00e5ff" }}>.csv</span> files (Max 50MB per file)
      </p>
      <button
        type="button"
        disabled={disabled}
        style={{
          background: "linear-gradient(135deg, #00e5ff 0%, #0088ff 100%)",
          color: "#0c0f16",
          border: "none",
          padding: "10px 24px",
          borderRadius: "8px",
          fontWeight: 700,
          cursor: disabled ? "not-allowed" : "pointer",
          fontSize: "0.9rem",
          boxShadow: "0 4px 14px rgba(0, 229, 255, 0.3)",
        }}
      >
        Browse Computer
      </button>
    </div>
  );
};
