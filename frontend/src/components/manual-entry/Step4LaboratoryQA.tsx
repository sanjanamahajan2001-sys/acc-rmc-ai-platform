/**
 * Step 4: Laboratory QA & Strength Test Calibration.
 * Responsive Mobile + Tablet + Desktop Hardening.
 * Enterprise Operations Light Theme Migration.
 */

import React, { useState, useEffect } from "react";
import { masterDataService, ManualDraftResponse } from "../../services/masterDataService";
import {
  enterpriseLightTokens,
  formInputStyle,
  formLabelStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
} from "./enterpriseLightTokens";

interface Step4Props {
  draft: ManualDraftResponse;
  onBack: () => void;
  onSuccess: (updatedDraft: ManualDraftResponse) => void;
}

export const Step4LaboratoryQA: React.FC<Step4Props> = ({ draft, onBack, onSuccess }) => {
  const get28DayDate = (baseDateStr: string) => {
    try {
      const d = new Date(baseDateStr);
      d.setDate(d.getDate() + 28);
      return d.toISOString().split("T")[0];
    } catch {
      return "";
    }
  };

  const defaultCasting = draft.production_date || new Date().toISOString().split("T")[0];

  const [qaCubeId, setQaCubeId] = useState<string>(
    draft.qa_cube_id || `QC-${draft.recipe_code || "MIX"}-PUN-${Math.floor(1000 + Math.random() * 9000)}`
  );
  const [technicianId, setTechnicianId] = useState<string>(draft.lab_technician_id || "TECH-MUM-01");
  const [technicianName, setTechnicianName] = useState<string>(draft.lab_technician_name || "Rahul Kumar");
  const [castingDate, setCastingDate] = useState<string>(draft.casting_date || defaultCasting);
  const [testingDate28Day, setTestingDate28Day] = useState<string>(
    draft.testing_date_28_day || get28DayDate(defaultCasting)
  );

  const [result7DayMpa, setResult7DayMpa] = useState<string>(
    draft.result_7_day_mpa ? String(draft.result_7_day_mpa) : "30.8"
  );
  const [result28DayMpa, setResult28DayMpa] = useState<string>(
    draft.result_28_day_mpa ? String(draft.result_28_day_mpa) : "51.3"
  );

  const [failureReasonCode, setFailureReasonCode] = useState<string>(draft.failure_reason_code || "NONE");
  const [failureReasonText, setFailureReasonText] = useState<string>(draft.failure_reason_text || "");
  const [laboratoryRemarks, setLaboratoryRemarks] = useState<string>(draft.laboratory_remarks || "");

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const calculateDaysDiff = () => {
    if (!castingDate || !testingDate28Day) return null;
    const c = new Date(castingDate);
    const t = new Date(testingDate28Day);
    const diffTime = t.getTime() - c.getTime();
    return Math.round(diffTime / (1000 * 3600 * 24));
  };

  const daysDiff = calculateDaysDiff();
  const isExact28DayCuring = daysDiff === 28;

  const targetGradeMpa = draft.qa_metadata?.target_strength_mpa || 40.0;
  const num28Day = parseFloat(result28DayMpa) || 0;
  const strengthMargin = +(num28Day - targetGradeMpa).toFixed(2);
  const isAssessmentPass = num28Day >= targetGradeMpa && isExact28DayCuring;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!qaCubeId) {
      setError("QA Specimen Cube ID is required.");
      return;
    }
    if (!result28DayMpa || isNaN(num28Day) || num28Day <= 0) {
      setError("Authoritative 28-day compressive strength (MPa) is required.");
      return;
    }
    if (failureReasonCode !== "NONE" && !failureReasonText.trim()) {
      setError("An explanatory failure detail is mandatory when Failure Reason Code is not NONE.");
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        qa_cube_id: qaCubeId,
        lab_technician_id: technicianId,
        lab_technician_name: technicianName,
        casting_date: castingDate,
        testing_date_28_day: testingDate28Day,
        result_7_day_mpa: result7DayMpa ? parseFloat(result7DayMpa) : undefined,
        result_28_day_mpa: num28Day,
        failure_reason_code: failureReasonCode,
        failure_reason_text: failureReasonText || undefined,
        approved_by_user_id: draft.operator_id || "OPERATOR-MUMBAI-01",
        approved_by_display_name: draft.operator_name || "Sanjana Sharma",
        laboratory_remarks: laboratoryRemarks || undefined,
      };

      const updated = await masterDataService.updateStep4LaboratoryQA(draft.draft_id, payload);
      onSuccess(updated);
    } catch (err: any) {
      setError(err.message || "Failed to save Laboratory QA data.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "18px", color: enterpriseLightTokens.textPrimary }}>
      {error && (
        <div
          style={{
            padding: "12px 16px",
            backgroundColor: enterpriseLightTokens.errorRedLight,
            border: `1px solid ${enterpriseLightTokens.errorRedBorder}`,
            borderRadius: enterpriseLightTokens.radius,
            color: enterpriseLightTokens.errorRed,
            fontSize: "0.85rem",
          }}
        >
          {error}
        </div>
      )}

      {/* Draft Context Banner */}
      <div
        style={{
          padding: "12px 18px",
          backgroundColor: enterpriseLightTokens.surfaceCard,
          border: `1px solid ${enterpriseLightTokens.border}`,
          borderRadius: enterpriseLightTokens.radius,
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "10px",
          boxShadow: enterpriseLightTokens.shadowCard,
        }}
      >
        <div>
          <span style={{ fontSize: "0.72rem", color: enterpriseLightTokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Batch Target:</span>
          <span style={{ fontSize: "0.88rem", fontWeight: 700, color: enterpriseLightTokens.textPrimary, marginLeft: "6px" }}>
            {draft.batch_number} ({draft.recipe_name})
          </span>
        </div>
        <div>
          <span style={{ fontSize: "0.72rem", color: enterpriseLightTokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Plant:</span>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: enterpriseLightTokens.textSecondary, marginLeft: "6px" }}>
            {draft.plant_name}
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
        {/* 1. QA Cube Identification */}
        <div
          style={{
            backgroundColor: enterpriseLightTokens.surfaceCard,
            padding: "18px 20px",
            borderRadius: enterpriseLightTokens.radius,
            border: `1px solid ${enterpriseLightTokens.border}`,
            boxShadow: enterpriseLightTokens.shadowCard,
          }}
        >
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: enterpriseLightTokens.textPrimary, marginBottom: "12px" }}>
            1. Specimen Identification & Laboratory Technician
          </div>
          <div className="responsive-form-grid">
            <div>
              <label style={formLabelStyle}>QA Cube Specimen Identifier *</label>
              <input
                type="text"
                value={qaCubeId || ""}
                onChange={(e) => setQaCubeId(e.target.value)}
                style={formInputStyle}
                required
              />
            </div>
            <div>
              <label style={formLabelStyle}>Lab Technician ID *</label>
              <input
                type="text"
                value={technicianId || ""}
                onChange={(e) => setTechnicianId(e.target.value)}
                style={formInputStyle}
                required
              />
            </div>
            <div>
              <label style={formLabelStyle}>Lab Technician Name *</label>
              <input
                type="text"
                value={technicianName || ""}
                onChange={(e) => setTechnicianName(e.target.value)}
                style={formInputStyle}
                required
              />
            </div>
          </div>
        </div>

        {/* 2. Curing Dates & Calculated Age */}
        <div
          style={{
            backgroundColor: enterpriseLightTokens.surfaceCard,
            padding: "18px 20px",
            borderRadius: enterpriseLightTokens.radius,
            border: `1px solid ${enterpriseLightTokens.border}`,
            boxShadow: enterpriseLightTokens.shadowCard,
          }}
        >
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: enterpriseLightTokens.textPrimary, marginBottom: "12px" }}>
            2. Curing Schedule & Test Timeline
          </div>
          <div className="responsive-form-grid">
            <div>
              <label style={formLabelStyle}>Casting Date *</label>
              <input
                type="date"
                value={castingDate || ""}
                onChange={(e) => {
                  const newCasting = e.target.value;
                  setCastingDate(newCasting);
                  if (newCasting) {
                    setTestingDate28Day(get28DayDate(newCasting));
                  }
                }}
                style={formInputStyle}
                required
              />
            </div>
            <div>
              <label style={formLabelStyle}>Testing Date (28-Day) *</label>
              <input
                type="date"
                value={testingDate28Day || ""}
                onChange={(e) => setTestingDate28Day(e.target.value)}
                style={{
                  ...formInputStyle,
                  borderColor: isExact28DayCuring ? enterpriseLightTokens.border : enterpriseLightTokens.errorRed,
                }}
                required
              />
            </div>
            <div>
              <label style={formLabelStyle}>Curing Age (Calculated Days)</label>
              <input
                type="text"
                value={isExact28DayCuring ? `${daysDiff} Days` : daysDiff !== null ? `${daysDiff} Days (Expected 28D)` : "INVALID SCHEDULE"}
                disabled
                style={{
                  ...formInputStyle,
                  backgroundColor: enterpriseLightTokens.secondarySurface,
                  color: isExact28DayCuring ? enterpriseLightTokens.primaryAccent : enterpriseLightTokens.errorRed,
                  fontWeight: 700,
                }}
              />
            </div>
          </div>
        </div>

        {/* 3. Compressive Strength Results */}
        <div
          style={{
            backgroundColor: enterpriseLightTokens.surfaceCard,
            padding: "18px 20px",
            borderRadius: enterpriseLightTokens.radius,
            border: `1px solid ${enterpriseLightTokens.border}`,
            boxShadow: enterpriseLightTokens.shadowCard,
          }}
        >
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: enterpriseLightTokens.textPrimary, marginBottom: "12px" }}>
            3. Compressive Strength Results (MPa)
          </div>
          <div className="responsive-form-grid">
            <div>
              <label style={formLabelStyle}>7-Day Result (MPa) [Optional]</label>
              <input
                type="number"
                step="0.1"
                value={result7DayMpa || ""}
                onChange={(e) => setResult7DayMpa(e.target.value)}
                placeholder="e.g. 30.8"
                style={formInputStyle}
              />
            </div>
            <div>
              <label style={formLabelStyle}>28-Day Result (MPa) *</label>
              <input
                type="number"
                step="0.1"
                value={result28DayMpa || ""}
                onChange={(e) => setResult28DayMpa(e.target.value)}
                placeholder="e.g. 51.3"
                style={formInputStyle}
                required
              />
            </div>
          </div>
        </div>

        {/* 4. Failure Reason Governance & Remarks */}
        <div
          style={{
            backgroundColor: enterpriseLightTokens.surfaceCard,
            padding: "18px 20px",
            borderRadius: enterpriseLightTokens.radius,
            border: `1px solid ${enterpriseLightTokens.border}`,
            boxShadow: enterpriseLightTokens.shadowCard,
          }}
        >
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: enterpriseLightTokens.textPrimary, marginBottom: "12px" }}>
            4. Governance, Rejection Reason & Remarks
          </div>
          <div className="responsive-form-grid" style={{ marginBottom: "14px" }}>
            <div>
              <label style={formLabelStyle}>Failure Reason Code *</label>
              <select
                value={failureReasonCode || "NONE"}
                onChange={(e) => setFailureReasonCode(e.target.value)}
                style={formInputStyle}
              >
                <option value="NONE">NONE (Compliant / Within Tolerances)</option>
                <option value="LOW_STRENGTH">LOW_STRENGTH (Strength Below Target)</option>
                <option value="SPECIMEN_DEFECT">SPECIMEN_DEFECT (Physical Cube Flaw / Honeycombing)</option>
                <option value="TESTING_ERROR">TESTING_ERROR (Machine Load Rate Failure)</option>
                <option value="CURING_ISSUE">CURING_ISSUE (Water Bath Temp Excursion)</option>
                <option value="DATE_EXCEPTION">DATE_EXCEPTION (Tested Outside 28D Window)</option>
                <option value="EQUIPMENT_ISSUE">EQUIPMENT_ISSUE (Compression Machine Calibration)</option>
                <option value="OTHER">OTHER (See Detailed Remarks)</option>
              </select>
            </div>
            <div>
              <label style={formLabelStyle}>Explanatory Detail (Required if Code != NONE)</label>
              <input
                type="text"
                placeholder="Required for non-compliance codes"
                value={failureReasonText || ""}
                onChange={(e) => setFailureReasonText(e.target.value)}
                disabled={failureReasonCode === "NONE"}
                style={{
                  ...formInputStyle,
                  backgroundColor: failureReasonCode === "NONE" ? enterpriseLightTokens.secondarySurface : "#FFFFFF",
                }}
              />
            </div>
          </div>
          <div>
            <label style={formLabelStyle}>Laboratory Observations & Remarks</label>
            <textarea
              rows={2}
              value={laboratoryRemarks || ""}
              onChange={(e) => setLaboratoryRemarks(e.target.value)}
              style={{ ...formInputStyle, resize: "vertical" }}
            />
          </div>
        </div>

        {/* Live Quality Assessment Panel with wrap */}
        <div
          style={{
            padding: "16px 20px",
            backgroundColor: isAssessmentPass ? enterpriseLightTokens.successGreenLight : enterpriseLightTokens.warningAmberLight,
            border: `1px solid ${isAssessmentPass ? enterpriseLightTokens.successGreenBorder : enterpriseLightTokens.warningAmberBorder}`,
            borderRadius: enterpriseLightTokens.radius,
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <div>
            <div style={{ fontSize: "0.85rem", fontWeight: 700, color: isAssessmentPass ? enterpriseLightTokens.successGreen : enterpriseLightTokens.warningAmber }}>
              Preliminary QA Assessment: {isAssessmentPass ? "COMPLIANT / READY FOR GATE" : "REVIEW REQUIRED / DEFICIT DETECTED"}
            </div>
            <div style={{ fontSize: "0.8rem", color: enterpriseLightTokens.textSecondary, marginTop: "4px" }}>
              Target Grade: <strong>{targetGradeMpa} MPa</strong> | 28D Result: <strong>{num28Day} MPa</strong> | Margin: <strong>{strengthMargin >= 0 ? `+${strengthMargin}` : strengthMargin} MPa</strong>
            </div>
          </div>
          <div style={{ textAlign: "left", fontSize: "0.75rem", color: enterpriseLightTokens.textMuted }}>
            Approved By: <strong>{draft.operator_name || "Operator"}</strong>
          </div>
        </div>

        {/* Action Navigation Footer */}
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "10px", marginTop: "8px" }}>
          <button
            type="button"
            onClick={onBack}
            style={secondaryButtonStyle}
          >
            ← Back to Step 3
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              ...primaryButtonStyle,
              opacity: isSubmitting ? 0.7 : 1,
              cursor: isSubmitting ? "not-allowed" : "pointer",
            }}
          >
            {isSubmitting ? "Saving QA Parameters..." : "Save Step 4 & Proceed to Step 5 →"}
          </button>
        </div>
      </form>
    </div>
  );
};
