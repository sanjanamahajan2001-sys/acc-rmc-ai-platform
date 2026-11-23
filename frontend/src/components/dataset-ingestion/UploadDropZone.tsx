/**
 * Modular Vite Component: Drag & Drop Ingestion File Upload Zone.
 * Enterprise Operations Light Theme Migration.
 */

import React, { useRef, useState } from "react";
import {
  enterpriseLightTokens as tokens,
  primaryButtonBase,
} from "../manual-entry/enterpriseLightTokens";

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
      e.target.value = "";
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && fileInputRef.current?.click()}
      style={{
        border: `2px dashed ${isDragOver ? tokens.accent : tokens.border}`,
        borderRadius: "10px",
        padding: "36px 20px",
        textAlign: "center",
        backgroundColor: isDragOver ? "#EEF2FF" : tokens.surfacePrimary,
        cursor: disabled ? "not-allowed" : "pointer",
        transition: "all 0.2s ease",
        boxShadow: isDragOver ? "0 0 15px rgba(79, 70, 197, 0.15)" : "none",
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
      <div style={{ fontSize: "2.4rem", marginBottom: "10px", color: tokens.accent }}>📂</div>
      <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: tokens.textPrimary, margin: "0 0 6px 0" }}>
        Drag & Drop Excel or CSV Datasets Here
      </h3>
      <p style={{ fontSize: "0.85rem", color: tokens.textMuted, margin: "0 0 16px 0" }}>
        Supports <strong style={{ color: tokens.accent }}>.xlsx</strong>, <strong style={{ color: tokens.accent }}>.xls</strong>, and <strong style={{ color: tokens.accent }}>.csv</strong> files (Max 50MB per file)
      </p>
      <button
        type="button"
        disabled={disabled}
        onClick={(e) => {
          e.stopPropagation();
          if (!disabled && fileInputRef.current) {
            fileInputRef.current.click();
          }
        }}
        style={{
          ...primaryButtonBase,
          padding: "9px 22px",
          fontSize: "0.85rem",
          cursor: disabled ? "not-allowed" : "pointer",
        }}
      >
        Browse Computer
      </button>
    </div>
  );
};
