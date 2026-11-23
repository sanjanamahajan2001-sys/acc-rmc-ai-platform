/**
 * Step 2: Machine & Batch Dispatch Parameters.
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

interface Step2Props {
  draft: ManualDraftResponse;
  onBack: () => void;
  onNext: (updatedDraft: ManualDraftResponse) => void;
}

export const Step2MachineParameters: React.FC<Step2Props> = ({ draft, onBack, onNext }) => {
  const [startTime, setStartTime] = useState<string>("09:15:00");
  const [endTime, setEndTime] = useState<string>("09:17:15");
  const [mixerTime, setMixerTime] = useState<number>(45);
  const [truckNumber, setTruckNumber] = useState<string>("TM-MUM-402");
  const [deliveryChallan, setDeliveryChallan] = useState<string>("");
  const [moistureCorrection, setMoistureCorrection] = useState<number>(1.0);
  const [targetSlump, setTargetSlump] = useState<number>(125);
  const [orderNumber, setOrderNumber] = useState<string>("");

  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (draft) {
      if (draft.batch_start_time) setStartTime(draft.batch_start_time || "09:15:00");
      if (draft.batch_end_time) setEndTime(draft.batch_end_time || "09:17:15");
      if (draft.mixer_time_seconds !== undefined && draft.mixer_time_seconds !== null) setMixerTime(draft.mixer_time_seconds);
      if (draft.truck_number !== undefined && draft.truck_number !== null) setTruckNumber(draft.truck_number || "");
      if (draft.delivery_challan !== undefined && draft.delivery_challan !== null) setDeliveryChallan(draft.delivery_challan || "");
      if (draft.aggregate_moisture_correction !== undefined && draft.aggregate_moisture_correction !== null) setMoistureCorrection(draft.aggregate_moisture_correction);
      if (draft.target_slump_mm !== undefined && draft.target_slump_mm !== null) setTargetSlump(draft.target_slump_mm);
      if (draft.order_number !== undefined && draft.order_number !== null) setOrderNumber(draft.order_number || "");
    }
  }, [draft]);

  const calculateDurationPreview = (): string => {
    if (!startTime || !endTime) return "-- min -- sec";
    try {
      const s = startTime.split(":").map(Number);
      const e = endTime.split(":").map(Number);
      const startSecs = s[0] * 3600 + s[1] * 60 + (s[2] || 0);
      const endSecs = e[0] * 3600 + e[1] * 60 + (e[2] || 0);
      const diff = endSecs - startSecs;
      if (diff <= 0) return "End time must be after start time";
      const mins = Math.floor(diff / 60);
      const secs = diff % 60;
      return `${mins} min ${secs} sec`;
    } catch {
      return "--";
    }
  };

  const handleSaveStep2 = async () => {
    if (!startTime || !endTime) {
      setError("Batch start and end times are required.");
      return;
    }
    if (!truckNumber) {
      setError("Transit mixer truck identifier is required.");
      return;
    }
    if (!deliveryChallan) {
      setError("Delivery challan number is required.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const res = await masterDataService.updateStep2MachineParams(draft.draft_id, {
        batch_start_time: startTime,
        batch_end_time: endTime,
        mixer_time_seconds: mixerTime,
        truck_number: truckNumber,
        delivery_challan: deliveryChallan,
        order_number: orderNumber || undefined,
        aggregate_moisture_correction: moistureCorrection,
        target_slump_mm: targetSlump,
      });
      onNext(res);
    } catch (err: any) {
      setError(err.message || "Failed to save machine parameters.");
    } finally {
      setSubmitting(false);
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

      {/* Draft Context Banner with responsive 4-column auto-fit */}
      <div
        className="responsive-4col-grid"
        style={{
          padding: "14px 18px",
          backgroundColor: enterpriseLightTokens.surfaceCard,
          border: `1px solid ${enterpriseLightTokens.border}`,
          borderRadius: enterpriseLightTokens.radius,
          boxShadow: enterpriseLightTokens.shadowCard,
        }}
      >
        <div>
          <div style={{ fontSize: "0.72rem", color: enterpriseLightTokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Draft ID</div>
          <div style={{ fontSize: "0.88rem", fontWeight: 700, color: enterpriseLightTokens.primaryAccent, marginTop: "2px" }}>{draft.draft_id}</div>
        </div>
        <div>
          <div style={{ fontSize: "0.72rem", color: enterpriseLightTokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Batch Number</div>
          <div style={{ fontSize: "0.88rem", fontWeight: 700, color: enterpriseLightTokens.textPrimary, marginTop: "2px" }}>{draft.batch_number}</div>
        </div>
        <div>
          <div style={{ fontSize: "0.72rem", color: enterpriseLightTokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Target Plant</div>
          <div className="text-wrap-safe" style={{ fontSize: "0.82rem", fontWeight: 600, color: enterpriseLightTokens.textSecondary, marginTop: "2px" }}>{draft.plant_name}</div>
        </div>
        <div>
          <div style={{ fontSize: "0.72rem", color: enterpriseLightTokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Mix Design</div>
          <div className="text-wrap-safe" style={{ fontSize: "0.82rem", fontWeight: 600, color: enterpriseLightTokens.textSecondary, marginTop: "2px" }}>{draft.recipe_name}</div>
        </div>
      </div>

      {/* Form Fields Grid - Responsive 3 Column (Stacks to 1 on Mobile) */}
      <div
        className="responsive-3col-grid"
        style={{
          backgroundColor: enterpriseLightTokens.surfaceCard,
          padding: "18px 20px",
          borderRadius: enterpriseLightTokens.radius,
          border: `1px solid ${enterpriseLightTokens.border}`,
          boxShadow: enterpriseLightTokens.shadowCard,
        }}
      >
        {/* Batch Start Time */}
        <div>
          <label style={formLabelStyle}>
            Batch Start Time <span style={{ color: enterpriseLightTokens.errorRed }}>*</span>
          </label>
          <input
            type="time"
            step="1"
            value={startTime || ""}
            onChange={(e) => setStartTime(e.target.value)}
            style={formInputStyle}
          />
        </div>

        {/* Batch End Time */}
        <div>
          <label style={formLabelStyle}>
            Batch End Time <span style={{ color: enterpriseLightTokens.errorRed }}>*</span>
          </label>
          <input
            type="time"
            step="1"
            value={endTime || ""}
            onChange={(e) => setEndTime(e.target.value)}
            style={formInputStyle}
          />
        </div>

        {/* Calculated Duration Preview */}
        <div>
          <label style={formLabelStyle}>Calculated Batch Duration</label>
          <div
            style={{
              padding: "9px 12px",
              backgroundColor: enterpriseLightTokens.secondarySurface,
              border: `1px solid ${enterpriseLightTokens.border}`,
              borderRadius: enterpriseLightTokens.radius,
              fontSize: "0.85rem",
              fontWeight: 600,
              color: enterpriseLightTokens.primaryAccent,
            }}
          >
            ⏱️ {calculateDurationPreview()}
          </div>
        </div>

        {/* Mixer Time Seconds */}
        <div>
          <label style={formLabelStyle}>
            Mixer Time (Seconds) <span style={{ color: enterpriseLightTokens.errorRed }}>*</span>
          </label>
          <input
            type="number"
            min="1"
            max="600"
            value={mixerTime}
            onChange={(e) => setMixerTime(Number(e.target.value))}
            style={formInputStyle}
          />
          <span style={{ fontSize: "0.7rem", color: enterpriseLightTokens.textMuted }}>Typical range: 30 - 120 sec</span>
        </div>

        {/* Truck Identifier */}
        <div>
          <label style={formLabelStyle}>
            Transit Mixer Truck # <span style={{ color: enterpriseLightTokens.errorRed }}>*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. TM-MUM-402"
            value={truckNumber || ""}
            onChange={(e) => setTruckNumber(e.target.value)}
            style={formInputStyle}
          />
        </div>

        {/* Delivery Challan */}
        <div>
          <label style={formLabelStyle}>
            Delivery Challan Number <span style={{ color: enterpriseLightTokens.errorRed }}>*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. DC-20260915-001"
            value={deliveryChallan || ""}
            onChange={(e) => setDeliveryChallan(e.target.value)}
            style={formInputStyle}
          />
        </div>

        {/* Moisture Correction % */}
        <div>
          <label style={formLabelStyle}>Aggregate Moisture Correction (%)</label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="15"
            value={moistureCorrection}
            onChange={(e) => setMoistureCorrection(Number(e.target.value))}
            style={formInputStyle}
          />
          <span style={{ fontSize: "0.7rem", color: enterpriseLightTokens.textMuted }}>Applied batching correction factor</span>
        </div>

        {/* Target Slump mm */}
        <div>
          <label style={formLabelStyle}>
            Design Target Slump (mm) <span style={{ color: enterpriseLightTokens.errorRed }}>*</span>
          </label>
          <input
            type="number"
            step="5"
            min="0"
            max="300"
            value={targetSlump}
            onChange={(e) => setTargetSlump(Number(e.target.value))}
            style={formInputStyle}
          />
          <span style={{ fontSize: "0.7rem", color: enterpriseLightTokens.textMuted }}>Slump cone tolerance: ±25mm</span>
        </div>

        {/* Order / Dispatch Reference */}
        <div>
          <label style={formLabelStyle}>Dispatch Order Reference (Optional)</label>
          <input
            type="text"
            placeholder="e.g. ORD-MUM-892"
            value={orderNumber || ""}
            onChange={(e) => setOrderNumber(e.target.value)}
            style={formInputStyle}
          />
        </div>
      </div>

      {/* Navigation Actions */}
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "10px", marginTop: "8px" }}>
        <button
          type="button"
          onClick={onBack}
          disabled={submitting}
          style={secondaryButtonStyle}
        >
          ← Back to Step 1
        </button>

        <button
          type="button"
          onClick={handleSaveStep2}
          disabled={submitting}
          style={{
            ...primaryButtonStyle,
            opacity: submitting ? 0.7 : 1,
            cursor: submitting ? "not-allowed" : "pointer",
          }}
        >
          {submitting ? "Saving Parameters..." : "Save Step 2 & Proceed to Step 3 →"}
        </button>
      </div>
    </div>
  );
};
