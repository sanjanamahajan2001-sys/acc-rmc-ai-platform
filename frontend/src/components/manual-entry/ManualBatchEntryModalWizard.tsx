/**
 * Modular Vite Component: In-Dashboard 6-Step Manual Production Entry Modal Wizard.
 * Enterprise Operations Light Theme Migration.
 * Responsive Mobile + Tablet + Desktop Hardening.
 */

import React, { useState, useEffect, useRef } from "react";
import { masterDataService, ManualDraftResponse } from "../../services/masterDataService";
import { Step1BatchInformation } from "./Step1BatchInformation";
import { Step2MachineParameters } from "./Step2MachineParameters";
import { Step3MaterialConsumption } from "./Step3MaterialConsumption";
import { Step4LaboratoryQA } from "./Step4LaboratoryQA";
import { Step5QualityChecks } from "./Step5QualityChecks";
import { Step6FinalReviewSubmit } from "./Step6FinalReviewSubmit";
import { enterpriseLightTokens as tokens } from "./enterpriseLightTokens";

interface ManualBatchEntryModalWizardProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ManualBatchEntryModalWizard: React.FC<ManualBatchEntryModalWizardProps> = ({
  isOpen,
  onClose,
}) => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [draft, setDraft] = useState<ManualDraftResponse | null>(null);
  const [, setSubmittedBatchId] = useState<string | null>(null);
  const stepperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      const activeDraftId = localStorage.getItem("active_draft_id");
      if (activeDraftId) {
        masterDataService
          .getManualDraft(activeDraftId)
          .then((d) => {
            setDraft(d);
            if (d.status === "SUBMITTED") {
              localStorage.removeItem("active_draft_id");
              setDraft(null);
              setCurrentStep(1);
            } else if (d.current_step && d.current_step >= 1) {
              setCurrentStep(d.current_step);
            }
          })
          .catch(() => {
            localStorage.removeItem("active_draft_id");
            setDraft(null);
            setCurrentStep(1);
          });
      } else {
        setDraft(null);
        setCurrentStep(1);
      }
    }
  }, [isOpen]);

  // Scroll active tab into view on step change
  useEffect(() => {
    if (stepperRef.current) {
      const activeEl = stepperRef.current.children[currentStep - 1] as HTMLElement;
      if (activeEl) {
        activeEl.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      }
    }
  }, [currentStep]);

  if (!isOpen) return null;

  const steps = [
    "Batch Information",
    "Machine Parameters",
    "Material Consumption",
    "Laboratory QA",
    "Quality Checks",
    "Final Review & Submit",
  ];

  const handleStep1Success = (createdDraft: ManualDraftResponse) => {
    setDraft(createdDraft);
    localStorage.setItem("active_draft_id", createdDraft.draft_id);
    setCurrentStep(2);
  };

  const handleStep2Success = (updatedDraft?: ManualDraftResponse) => {
    if (!updatedDraft) return;
    setDraft(updatedDraft);
    localStorage.setItem("active_draft_id", updatedDraft.draft_id);
    setCurrentStep(3);
  };

  const handleStep3Success = (updatedDraft?: ManualDraftResponse) => {
    if (!updatedDraft) return;
    setDraft(updatedDraft);
    localStorage.setItem("active_draft_id", updatedDraft.draft_id);
    setCurrentStep(4);
  };

  const handleStep4Success = (updatedDraft?: ManualDraftResponse) => {
    if (!updatedDraft) return;
    setDraft(updatedDraft);
    localStorage.setItem("active_draft_id", updatedDraft.draft_id);
    setCurrentStep(5);
  };

  const handleStep5Success = (updatedDraft?: ManualDraftResponse) => {
    if (!updatedDraft) return;
    setDraft(updatedDraft);
    localStorage.setItem("active_draft_id", updatedDraft.draft_id);
    setCurrentStep(6);
  };

  const handleFinalSubmitSuccess = (batchId: string) => {
    setSubmittedBatchId(batchId);
    localStorage.removeItem("active_draft_id");
  };

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
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "8px",
      }}
    >
      <div className="modal-dialog-responsive">
        {/* Header */}
        <div
          className="modal-header-responsive"
          style={{
            padding: "14px 20px",
            borderBottom: `1px solid ${tokens.border}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            backgroundColor: tokens.surfaceSecondary,
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          <div>
            <h2 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: tokens.textPrimary }}>
              📝 Manual Production Batch Entry Wizard
            </h2>
            <div style={{ fontSize: "0.75rem", color: tokens.textMuted, marginTop: "2px" }}>
              Step {currentStep} of 6: <span style={{ color: tokens.accent, fontWeight: 600 }}>{steps[currentStep - 1]}</span>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            {draft && (
              <button
                type="button"
                onClick={() => {
                  localStorage.removeItem("active_draft_id");
                  setDraft(null);
                  setCurrentStep(1);
                }}
                style={{
                  backgroundColor: tokens.surfacePrimary,
                  border: `1px solid ${tokens.border}`,
                  color: tokens.accent,
                  padding: "6px 10px",
                  borderRadius: "6px",
                  fontSize: "0.72rem",
                  cursor: "pointer",
                  fontWeight: 600,
                  boxShadow: "0 1px 2px rgba(0, 0, 0, 0.04)",
                }}
              >
                ➕ Start New Batch
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              style={{
                background: "none",
                border: "none",
                color: tokens.textMuted,
                fontSize: "1.2rem",
                cursor: "pointer",
                padding: "4px 8px",
                lineHeight: 1,
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Stepper Header with horizontal scroll and no tab squishing */}
        <div ref={stepperRef} className="wizard-stepper-container">
          {steps.map((label, idx) => {
            const stepNum = idx + 1;
            const isActive = currentStep === stepNum;
            const isCompleted = currentStep > stepNum;
            return (
              <div
                key={label}
                className="wizard-stepper-item"
                onClick={() => {
                  if (isCompleted && draft) setCurrentStep(stepNum);
                }}
                style={{
                  fontWeight: isActive ? 700 : isCompleted ? 600 : 400,
                  color: isActive ? tokens.accent : isCompleted ? tokens.statusSuccessText : tokens.textMuted,
                  borderBottom: isActive ? `2px solid ${tokens.accent}` : "2px solid transparent",
                  backgroundColor: isActive ? "#EEF2FF" : "transparent",
                  cursor: isCompleted ? "pointer" : "default",
                  transition: "all 0.15s ease",
                }}
              >
                {isCompleted ? "✓ " : `${stepNum}. `}
                {label}
              </div>
            );
          })}
        </div>

        {/* Modal Body */}
        <div className="modal-body-responsive" style={{ padding: "18px 20px", overflowY: "auto", flex: 1, backgroundColor: tokens.pageBg }}>
          {currentStep === 1 && (
            <Step1BatchInformation initialDraft={draft} onNext={handleStep1Success} />
          )}

          {currentStep === 2 && (
            <Step2MachineParameters
              draft={draft || ({ draft_id: localStorage.getItem("active_draft_id") } as any)}
              onBack={() => setCurrentStep(1)}
              onNext={handleStep2Success}
            />
          )}

          {currentStep === 3 && (
            <Step3MaterialConsumption
              draft={draft || ({ draft_id: localStorage.getItem("active_draft_id") } as any)}
              onBack={() => setCurrentStep(2)}
              onSuccess={handleStep3Success}
            />
          )}

          {currentStep === 4 && (
            <Step4LaboratoryQA
              draft={draft || ({ draft_id: localStorage.getItem("active_draft_id") } as any)}
              onBack={() => setCurrentStep(3)}
              onSuccess={handleStep4Success}
            />
          )}

          {currentStep === 5 && (
            <Step5QualityChecks
              draft={draft || ({ draft_id: localStorage.getItem("active_draft_id") } as any)}
              onBack={() => setCurrentStep(4)}
              onNext={handleStep5Success}
            />
          )}

          {currentStep === 6 && (
            <Step6FinalReviewSubmit
              draft={draft || ({ draft_id: localStorage.getItem("active_draft_id") || "ACTIVE-DRAFT" } as any)}
              onBack={() => setCurrentStep(5)}
              onSuccessSubmit={handleFinalSubmitSuccess}
            />
          )}
        </div>
      </div>
    </div>
  );
};
