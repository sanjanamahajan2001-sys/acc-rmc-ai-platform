/**
 * ACC RMC Standalone Page: Dataset Ingestion.
 * Route: /acc/dataset-ingestion
 * Unified Enterprise Layout with Left Navigation & Top Navbar.
 */

import React, { useState } from "react";
import { DatasetIngestionModalWizard } from "../components/dataset-ingestion/DatasetIngestionModalWizard";
import { AppShell } from "../components/AppShell";
import {
  enterpriseLightTokens as tokens,
  primaryButtonBase,
} from "../components/manual-entry/enterpriseLightTokens";

export const DatasetIngestionPage: React.FC = () => {
  const [wizardOpen, setWizardOpen] = useState<boolean>(false);

  const handleClose = () => {
    setWizardOpen(false);
  };

  return (
    <AppShell>
      {/* Page Container */}
      <main className="page-main-container">
        {/* Breadcrumb & Header */}
        <div style={{ marginBottom: "24px" }}>
          <div style={{ fontSize: "0.75rem", color: tokens.textMuted, marginBottom: "6px" }}>
            ACC Platform / Data Ingestion / <span style={{ color: tokens.primaryAccent, fontWeight: 600 }}>Dataset Ingestion</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
            <div data-tour="ingestion-header">
              <h1 style={{ fontSize: "1.25rem", fontWeight: 800, margin: 0, color: tokens.textPrimary }}>
                Dataset Ingestion & Discovery
              </h1>
              <p style={{ fontSize: "0.8rem", color: tokens.textMuted, margin: "3px 0 0 0" }}>
                Upload Excel batching, commercial ERP, and QA cube workbooks with automated schema mapping
              </p>
            </div>
          </div>
        </div>

        {/* Feature Hero Card */}
        <div data-tour="ingestion-pipeline-card"
          style={{
            backgroundColor: tokens.surfacePrimary,
            border: `1px solid ${tokens.border}`,
            borderRadius: "10px",
            padding: "32px 24px",
            boxShadow: tokens.shadowCard,
            textAlign: "center",
            marginBottom: "24px",
          }}
        >
          <div style={{ fontSize: "2.5rem", marginBottom: "12px" }}>📥</div>
          <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: tokens.textPrimary, margin: "0 0 8px 0" }}>
            Automated 5-Step Ingestion Pipeline
          </h2>
          <p
            style={{
              maxWidth: "650px",
              margin: "0 auto 24px auto",
              fontSize: "0.86rem",
              color: tokens.textSecondary,
              lineHeight: 1.6,
            }}
          >
            Streamline complex multi-tab plant telemetry into the canonical SQL database. Perform automated header discovery,
            column mapping resolution, pre-ingestion validation checks, and asynchronous persistence with zero data loss.
          </p>

          <button
            type="button"
            onClick={() => setWizardOpen(true)}
            aria-label="Open Ingestion Modal"
            data-tour="ingestion-open-modal-btn"
            style={{
              ...primaryButtonBase,
              minHeight: "44px",
              padding: "10px 28px",
              fontSize: "0.88rem",
              margin: "0 auto",
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              boxShadow: "0 2px 6px rgba(37, 99, 235, 0.25)",
            }}
          >
            <span>🚀</span> Open Ingestion Modal
          </button>
        </div>

        {/* Ingestion Wizard Component */}
        <DatasetIngestionModalWizard
          isOpen={wizardOpen}
          onClose={handleClose}
        />
      </main>
    </AppShell>
  );
};
