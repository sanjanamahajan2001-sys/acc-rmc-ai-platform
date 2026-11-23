/**
 * ACC RMC Standalone Page: Manual Production Entry.
 * Route: /acc/manual-production-entry
 * Unified Enterprise Layout with Left Navigation & Top Navbar.
 */

import React, { useState } from "react";
import { ManualBatchEntryModalWizard } from "../components/manual-entry/ManualBatchEntryModalWizard";
import { AppShell } from "../components/AppShell";
import {
  enterpriseLightTokens as tokens,
  primaryButtonBase,
} from "../components/manual-entry/enterpriseLightTokens";

export const ManualProductionEntryPage: React.FC = () => {
  const [modalOpen, setModalOpen] = useState<boolean>(false);

  const handleClose = () => {
    setModalOpen(false);
  };

  return (
    <AppShell>
      {/* Page Container */}
      <main className="page-main-container">
        {/* Breadcrumb & Header */}
        <div style={{ marginBottom: "24px" }}>
          <div style={{ fontSize: "0.75rem", color: tokens.textMuted, marginBottom: "6px" }}>
            ACC Platform / Data Ingestion / <span style={{ color: tokens.primaryAccent, fontWeight: 600 }}>Manual Batch Entry</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
            <div data-tour="manual-entry-header">
              <h1 style={{ fontSize: "1.25rem", fontWeight: 800, margin: 0, color: tokens.textPrimary }}>
                Manual Batch Entry Console
              </h1>
              <p style={{ fontSize: "0.8rem", color: tokens.textMuted, margin: "3px 0 0 0" }}>
                Record single-batch SCADA tickets, moisture corrections, and QA cube break results
              </p>
            </div>
          </div>
        </div>

        {/* Feature Hero Card */}
        <div
          data-tour="manual-entry-hero-card"
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
          <div style={{ fontSize: "2.5rem", marginBottom: "12px" }}>📋</div>
          <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: tokens.textPrimary, margin: "0 0 8px 0" }}>
            Manual Production & Quality Logging Console
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
            Capture ad-hoc batch tickets, verify aggregate water corrections, inspect material proportions against mix designs,
            and register compressive strength break certificates directly into the live operational database with full transactional safety.
          </p>

          <button
            type="button"
            onClick={() => setModalOpen(true)}
            aria-label="Open Batch Entry Modal"
            data-tour="manual-entry-open-modal-btn"
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
            <span>⚡</span> Open Batch Entry Modal
          </button>
        </div>

        {/* Manual Batch Entry Wizard Component */}
        <ManualBatchEntryModalWizard
          isOpen={modalOpen}
          onClose={handleClose}
        />
      </main>
    </AppShell>
  );
};
