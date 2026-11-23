/**
 * Step 3: Material Consumption & Authoritative SSD Mix Intelligence.
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

interface Step3Props {
  draft: ManualDraftResponse;
  onBack: () => void;
  onSuccess: (updatedDraft: ManualDraftResponse) => void;
}

export const Step3MaterialConsumption: React.FC<Step3Props> = ({ draft, onBack, onSuccess }) => {
  const [cementKg, setCementKg] = useState<number>(318.0);
  const [flyAshKg, setFlyAshKg] = useState<number>(0.0);
  const [ggbsKg, setGgbsKg] = useState<number>(135.0);
  const [waterKg, setWaterKg] = useState<number>(160.0);
  const [admixKg, setAdmixKg] = useState<number>(3.9);
  const [fineAggKg, setFineAggKg] = useState<number>(780.0);
  const [coarseAggKg, setCoarseAggKg] = useState<number>(1080.0);

  const [fineMoisture, setFineMoisture] = useState<number>(2.0);
  const [fineAbs, setFineAbs] = useState<number>(1.2);
  const [coarseMoisture, setCoarseMoisture] = useState<number>(0.8);
  const [coarseAbs, setCoarseAbs] = useState<number>(0.5);

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (draft) {
      if (draft.cement_kg_m3 !== undefined && draft.cement_kg_m3 !== null) setCementKg(draft.cement_kg_m3);
      if (draft.fly_ash_kg_m3 !== undefined && draft.fly_ash_kg_m3 !== null) setFlyAshKg(draft.fly_ash_kg_m3);
      if (draft.ggbs_kg_m3 !== undefined && draft.ggbs_kg_m3 !== null) setGgbsKg(draft.ggbs_kg_m3);
      if (draft.water_kg_m3 !== undefined && draft.water_kg_m3 !== null) setWaterKg(draft.water_kg_m3);
      if (draft.admixture_kg_m3 !== undefined && draft.admixture_kg_m3 !== null) setAdmixKg(draft.admixture_kg_m3);
      if (draft.fine_aggregate_kg_m3 !== undefined && draft.fine_aggregate_kg_m3 !== null) setFineAggKg(draft.fine_aggregate_kg_m3);
      if (draft.coarse_aggregate_kg_m3 !== undefined && draft.coarse_aggregate_kg_m3 !== null) setCoarseAggKg(draft.coarse_aggregate_kg_m3);

      if (draft.fine_aggregate_moisture_pct !== undefined && draft.fine_aggregate_moisture_pct !== null) setFineMoisture(draft.fine_aggregate_moisture_pct);
      if (draft.fine_aggregate_absorption_pct !== undefined && draft.fine_aggregate_absorption_pct !== null) setFineAbs(draft.fine_aggregate_absorption_pct);
      if (draft.coarse_aggregate_moisture_pct !== undefined && draft.coarse_aggregate_moisture_pct !== null) setCoarseMoisture(draft.coarse_aggregate_moisture_pct);
      if (draft.coarse_aggregate_absorption_pct !== undefined && draft.coarse_aggregate_absorption_pct !== null) setCoarseAbs(draft.coarse_aggregate_absorption_pct);
    }
  }, [draft]);

  const liveTotalBinder = cementKg + flyAshKg + ggbsKg;
  const fineFreeWater = fineAggKg * ((fineMoisture - fineAbs) / 100.0);
  const coarseFreeWater = coarseAggKg * ((coarseMoisture - coarseAbs) / 100.0);
  const totalFreeWaterFromAggs = fineFreeWater + coarseFreeWater;
  const liveEffectiveWater = +(waterKg + totalFreeWaterFromAggs).toFixed(2);
  const liveWB = liveTotalBinder > 0 ? +(liveEffectiveWater / liveTotalBinder).toFixed(3) : 0;

  const costCement = cementKg * 5.8;
  const costFlyAsh = flyAshKg * 1.5;
  const costGgbs = ggbsKg * 3.2;
  const costWater = waterKg * 0.15;
  const costAdmix = admixKg * 65.0;
  const costFine = fineAggKg * 1.1;
  const costCoarse = coarseAggKg * 0.95;
  const liveCost = +(costCement + costFlyAsh + costGgbs + costWater + costAdmix + costFine + costCoarse).toFixed(2);

  const sg = draft.sg_provenance;
  const liveYieldVolume = sg
    ? +(
        (cementKg / sg.cement_sg +
          flyAshKg / sg.fly_ash_sg +
          ggbsKg / sg.ggbs_sg +
          waterKg / sg.water_sg +
          admixKg / sg.admix_sg +
          fineAggKg / sg.fine_agg_sg +
          coarseAggKg / sg.coarse_agg_sg) /
          1000.0 +
        (sg.entrained_air_pct || 1.0) / 100.0
      ).toFixed(3)
    : null;

  const totalMass = cementKg + flyAshKg + ggbsKg + waterKg + admixKg + fineAggKg + coarseAggKg;
  const liveDensity = liveYieldVolume && liveYieldVolume > 0 ? +(totalMass / liveYieldVolume).toFixed(1) : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const payload = {
        cement_kg_m3: cementKg,
        fly_ash_kg_m3: flyAshKg,
        ggbs_kg_m3: ggbsKg,
        water_kg_m3: waterKg,
        admixture_kg_m3: admixKg,
        fine_aggregate_kg_m3: fineAggKg,
        coarse_aggregate_kg_m3: coarseAggKg,
        fine_aggregate_moisture_pct: fineMoisture,
        fine_aggregate_absorption_pct: fineAbs,
        coarse_aggregate_moisture_pct: coarseMoisture,
        coarse_aggregate_absorption_pct: coarseAbs,
      };

      const updated = await masterDataService.updateStep3MaterialConsumption(draft.draft_id, payload);
      onSuccess(updated);
    } catch (err: any) {
      setError(err.message || "Failed to save material consumption parameters.");
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

      {/* Header Context Banner */}
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
        {/* Binder & Liquid Group */}
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
            1. Binder & Liquid Consumption Proportions (kg/m³)
          </div>
          <div className="responsive-form-grid">
            <div>
              <label style={formLabelStyle}>Cement [OPC/PPC] (kg/m³) *</label>
              <input
                type="number"
                step="0.1"
                value={cementKg}
                onChange={(e) => setCementKg(parseFloat(e.target.value) || 0)}
                style={formInputStyle}
                required
              />
            </div>
            <div>
              <label style={formLabelStyle}>Fly Ash (kg/m³)</label>
              <input
                type="number"
                step="0.1"
                value={flyAshKg}
                onChange={(e) => setFlyAshKg(parseFloat(e.target.value) || 0)}
                style={formInputStyle}
              />
            </div>
            <div>
              <label style={formLabelStyle}>GGBS (kg/m³)</label>
              <input
                type="number"
                step="0.1"
                value={ggbsKg}
                onChange={(e) => setGgbsKg(parseFloat(e.target.value) || 0)}
                style={formInputStyle}
              />
            </div>
            <div>
              <label style={formLabelStyle}>Batch Water Added (kg/m³) *</label>
              <input
                type="number"
                step="0.1"
                value={waterKg}
                onChange={(e) => setWaterKg(parseFloat(e.target.value) || 0)}
                style={formInputStyle}
                required
              />
            </div>
          </div>
        </div>

        {/* Aggregates & Admixtures */}
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
            2. Aggregates (Basis: SSD) & Chemical Admixtures (kg/m³)
          </div>
          <div className="responsive-form-grid">
            <div>
              <label style={formLabelStyle}>Fine Aggregate / Sand [SSD] (kg/m³) *</label>
              <input
                type="number"
                step="0.1"
                value={fineAggKg}
                onChange={(e) => setFineAggKg(parseFloat(e.target.value) || 0)}
                style={formInputStyle}
                required
              />
            </div>
            <div>
              <label style={formLabelStyle}>Coarse Aggregate / Jelly [SSD] (kg/m³) *</label>
              <input
                type="number"
                step="0.1"
                value={coarseAggKg}
                onChange={(e) => setCoarseAggKg(parseFloat(e.target.value) || 0)}
                style={formInputStyle}
                required
              />
            </div>
            <div>
              <label style={formLabelStyle}>Chemical Admixture (kg/m³)</label>
              <input
                type="number"
                step="0.01"
                value={admixKg}
                onChange={(e) => setAdmixKg(parseFloat(e.target.value) || 0)}
                style={formInputStyle}
              />
            </div>
          </div>
        </div>

        {/* Moisture & Absorption Parameters */}
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
            3. Aggregate Moisture & Absorption Parameters (%)
          </div>
          <div className="responsive-form-grid">
            <div>
              <label style={formLabelStyle}>Fine Agg Moisture %</label>
              <input
                type="number"
                step="0.1"
                value={fineMoisture}
                onChange={(e) => setFineMoisture(parseFloat(e.target.value) || 0)}
                style={formInputStyle}
              />
            </div>
            <div>
              <label style={formLabelStyle}>Fine Agg Absorption %</label>
              <input
                type="number"
                step="0.1"
                value={fineAbs}
                onChange={(e) => setFineAbs(parseFloat(e.target.value) || 0)}
                style={formInputStyle}
              />
            </div>
            <div>
              <label style={formLabelStyle}>Coarse Agg Moisture %</label>
              <input
                type="number"
                step="0.1"
                value={coarseMoisture}
                onChange={(e) => setCoarseMoisture(parseFloat(e.target.value) || 0)}
                style={formInputStyle}
              />
            </div>
            <div>
              <label style={formLabelStyle}>Coarse Agg Absorption %</label>
              <input
                type="number"
                step="0.1"
                value={coarseAbs}
                onChange={(e) => setCoarseAbs(parseFloat(e.target.value) || 0)}
                style={formInputStyle}
              />
            </div>
          </div>
        </div>

        {/* Domain Intelligence Preview Card */}
        <div
          style={{
            backgroundColor: enterpriseLightTokens.secondarySurface,
            border: `1px solid ${enterpriseLightTokens.border}`,
            padding: "16px 20px",
            borderRadius: enterpriseLightTokens.radius,
          }}
        >
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: enterpriseLightTokens.primaryAccent, marginBottom: "10px" }}>
            Domain Calculation & Mix Intelligence Preview
          </div>
          <div className="responsive-stat-grid" style={{ fontSize: "0.85rem", marginBottom: "10px" }}>
            <div>Total Binder: <strong style={{ color: enterpriseLightTokens.textPrimary }}>{liveTotalBinder} kg/m³</strong></div>
            <div>Effective Water: <strong style={{ color: enterpriseLightTokens.textPrimary }}>{liveEffectiveWater} kg/m³</strong></div>
            <div>W / B Ratio: <strong style={{ color: enterpriseLightTokens.primaryAccent }}>{liveWB}</strong></div>
            <div>Theoretical Yield: <strong style={{ color: enterpriseLightTokens.textPrimary }}>{liveYieldVolume !== null ? `${liveYieldVolume} m³` : "Resolving..."}</strong></div>
            <div>Density: <strong style={{ color: enterpriseLightTokens.textPrimary }}>{liveDensity !== null ? `${liveDensity} kg/m³` : "Resolving..."}</strong></div>
            <div>Material Cost: <strong style={{ color: enterpriseLightTokens.textPrimary }}>₹{liveCost.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / m³</strong></div>
          </div>
          <div style={{ fontSize: "0.75rem", color: enterpriseLightTokens.textMuted, borderTop: `1px solid ${enterpriseLightTokens.borderLight}`, paddingTop: "8px", display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: "6px" }}>
            <div>
              NMSA: <strong>{draft.sg_provenance?.nmsa_mm ?? "--"} mm</strong> | 
              Air Content: <strong>{draft.sg_provenance?.entrained_air_pct !== undefined ? `${draft.sg_provenance?.entrained_air_pct}%` : "Resolving..."}</strong> | 
              Source: <strong>{draft.sg_provenance?.air_standard_reference ?? "IS 10262:2019"} ({draft.sg_provenance?.air_standard_section ?? "Section 5.2 / Table 3"})</strong>
            </div>
            <div>Full AI 28D Strength Prediction & Gated Optimization derived upon saving.</div>
          </div>
        </div>

        {/* Action Navigation Footer */}
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "10px", marginTop: "8px" }}>
          <button
            type="button"
            onClick={onBack}
            style={secondaryButtonStyle}
          >
            ← Back to Step 2
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
            {isSubmitting ? "Executing Calculations & Saving..." : "Save Step 3 & Proceed to Step 4 →"}
          </button>
        </div>
      </form>
    </div>
  );
};
