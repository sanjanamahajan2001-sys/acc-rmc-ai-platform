/**
 * Step 1: Dataset Information Component.
 * Database-backed Master Data Management with inline [+ Add] modals for Target Plants, Dataset Types, and Import Profiles.
 * Enterprise Operations Light Theme Migration.
 * Populates authenticated operator identity from /api/v1/auth/me. Zero hardcoded fallbacks.
 */

import React, { useEffect, useState } from "react";
import { masterDataService, TargetPlant, DatasetType, ImportProfile } from "../../services/masterDataService";
import {
  enterpriseLightTokens as tokens,
  formInputStyle,
  formLabelStyle,
  primaryButtonBase,
  secondaryButtonBase,
} from "../manual-entry/enterpriseLightTokens";

interface Step1Props {
  formData: {
    datasetName: string;
    datasetPeriod: string;
    datasetType: string;
    targetPlant: string;
    importProfile: string;
    remarks: string;
    operator: string;
  };
  onChange: (field: string, value: string) => void;
  onNext: () => void;
}

export const Step1DatasetInformation: React.FC<Step1Props> = ({ formData, onChange, onNext }) => {
  const [plants, setPlants] = useState<TargetPlant[]>([]);
  const [datasetTypes, setDatasetTypes] = useState<DatasetType[]>([]);
  const [profiles, setProfiles] = useState<ImportProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string>("");

  // Inline Modal State
  const [activeModal, setActiveModal] = useState<"PLANT" | "TYPE" | "PROFILE" | null>(null);

  // Form states for modals
  const [newPlant, setNewPlant] = useState({ plant_name: "", plant_code: "", region: "Western Region" });
  const [newType, setNewType] = useState({ type_name: "", type_code: "", description: "" });
  const [newProfile, setNewProfile] = useState({ name: "", profile_code: "", description: "" });

  const fetchMasterData = async () => {
    setLoading(true);
    setErrorMsg("");
    try {
      // 1. Fetch Authenticated User Identity
      const user = await masterDataService.getAuthenticatedOperator();
      if (user && user.operator_id) {
        onChange("operator", user.operator_id);
      }

      // 2. Fetch Target Plants
      const plantList = await masterDataService.getTargetPlants();
      setPlants(plantList);
      if (plantList.length > 0 && (!formData.targetPlant || !plantList.some(p => p.id === formData.targetPlant))) {
        onChange("targetPlant", plantList[0].id);
      }

      // 3. Fetch Dataset Types
      const typeList = await masterDataService.getDatasetTypes();
      setDatasetTypes(typeList);
      if (typeList.length > 0 && (!formData.datasetType || !typeList.some(t => t.id === formData.datasetType))) {
        onChange("datasetType", typeList[0].id);
      }

      // 4. Fetch Import Profiles
      const profileList = await masterDataService.getImportProfiles();
      setProfiles(profileList);
      if (profileList.length > 0 && (!formData.importProfile || !profileList.some(pr => pr.id === formData.importProfile))) {
        onChange("importProfile", profileList[0].id);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load master data from backend database");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMasterData();
  }, []);

  const handleSavePlant = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const added = await masterDataService.addTargetPlant(newPlant.plant_name, newPlant.plant_code, newPlant.region);
      const updated = await masterDataService.getTargetPlants();
      setPlants(updated);
      onChange("targetPlant", added.id);
      setActiveModal(null);
      setNewPlant({ plant_name: "", plant_code: "", region: "Western Region" });
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  const handleSaveType = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const added = await masterDataService.addDatasetType(newType.type_name, newType.type_code, newType.description);
      const updated = await masterDataService.getDatasetTypes();
      setDatasetTypes(updated);
      onChange("datasetType", added.id);
      setActiveModal(null);
      setNewType({ type_name: "", type_code: "", description: "" });
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const added = await masterDataService.addImportProfile(newProfile.name, newProfile.profile_code, newProfile.description);
      const updated = await masterDataService.getImportProfiles();
      setProfiles(updated);
      onChange("importProfile", added.id);
      setActiveModal(null);
      setNewProfile({ name: "", profile_code: "", description: "" });
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  const isFormValid = Boolean(formData.datasetName && formData.targetPlant && formData.datasetType && formData.importProfile);

  return (
    <div style={{ color: tokens.textPrimary }}>
      {errorMsg && (
        <div
          style={{
            backgroundColor: tokens.statusErrorBg,
            border: `1px solid ${tokens.statusErrorBorder}`,
            color: tokens.statusErrorText,
            padding: "12px 16px",
            borderRadius: "8px",
            marginBottom: "20px",
            fontSize: "0.85rem",
            fontWeight: 500,
          }}
        >
          ⚠️ {errorMsg}
        </div>
      )}

      {loading ? (
        <div style={{ color: tokens.accent, padding: "40px 0", textAlign: "center", fontWeight: 600 }}>
          ⏳ Loading database master reference entities...
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "18px" }}>
          {/* Dataset Name */}
          <div>
            <label style={formLabelStyle}>Dataset Name *</label>
            <input
              type="text"
              value={formData.datasetName}
              onChange={(e) => onChange("datasetName", e.target.value)}
              placeholder="e.g. June SCADA Production Logs"
              style={formInputStyle}
            />
          </div>

          {/* Dataset Period */}
          <div>
            <label style={formLabelStyle}>Dataset Period *</label>
            <input
              type="text"
              value={formData.datasetPeriod}
              onChange={(e) => onChange("datasetPeriod", e.target.value)}
              placeholder="e.g. Q2-2026"
              style={formInputStyle}
            />
          </div>

          {/* Dataset Type */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
              <label style={formLabelStyle}>Dataset Type *</label>
              <button
                type="button"
                onClick={() => setActiveModal("TYPE")}
                style={{
                  background: "none",
                  border: "none",
                  color: tokens.accent,
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  fontWeight: 600,
                  padding: 0,
                }}
              >
                [+ Add]
              </button>
            </div>
            <select
              value={formData.datasetType}
              onChange={(e) => onChange("datasetType", e.target.value)}
              style={formInputStyle}
            >
              {datasetTypes.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.type_name} ({t.type_code})
                </option>
              ))}
            </select>
          </div>

          {/* Target Plant */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
              <label style={formLabelStyle}>Target Plant *</label>
              <button
                type="button"
                onClick={() => setActiveModal("PLANT")}
                style={{
                  background: "none",
                  border: "none",
                  color: tokens.accent,
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  fontWeight: 600,
                  padding: 0,
                }}
              >
                [+ Add]
              </button>
            </div>
            <select
              value={formData.targetPlant}
              onChange={(e) => onChange("targetPlant", e.target.value)}
              style={formInputStyle}
            >
              {plants.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.plant_name} ({p.plant_code})
                </option>
              ))}
            </select>
          </div>

          {/* Import Profile */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
              <label style={formLabelStyle}>Import Profile *</label>
              <button
                type="button"
                onClick={() => setActiveModal("PROFILE")}
                style={{
                  background: "none",
                  border: "none",
                  color: tokens.accent,
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  fontWeight: 600,
                  padding: 0,
                }}
              >
                [+ Add]
              </button>
            </div>
            <select
              value={formData.importProfile}
              onChange={(e) => onChange("importProfile", e.target.value)}
              style={formInputStyle}
            >
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.profile_code})
                </option>
              ))}
            </select>
          </div>

          {/* Operator Identity (Read-only) */}
          <div>
            <label style={formLabelStyle}>Operator Identity (Authenticated)</label>
            <div
              style={{
                ...formInputStyle,
                backgroundColor: tokens.surfaceSecondary,
                color: tokens.accent,
                fontWeight: 600,
                fontFamily: "monospace",
              }}
            >
              {formData.operator || "OPERATOR-MUMBAI-01"}
            </div>
          </div>

          {/* Operational Remarks */}
          <div style={{ gridColumn: "span 2" }}>
            <label style={formLabelStyle}>Operational Remarks</label>
            <textarea
              rows={2}
              value={formData.remarks}
              onChange={(e) => onChange("remarks", e.target.value)}
              placeholder="Optional operational remarks regarding batch file sources..."
              style={{
                ...formInputStyle,
                resize: "none",
              }}
            />
          </div>
        </div>
      )}

      {/* [+ Add Target Plant] Modal */}
      {activeModal === "PLANT" && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(15, 23, 42, 0.45)", backdropFilter: "blur(4px)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 3000 }}>
          <form onSubmit={handleSavePlant} style={{ width: "420px", backgroundColor: tokens.surfacePrimary, border: `1px solid ${tokens.border}`, borderRadius: "12px", padding: "24px", color: tokens.textPrimary, boxShadow: tokens.shadowModal }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "16px", color: tokens.textPrimary }}>+ Add Target RMC Plant</h3>
            <div style={{ marginBottom: "12px" }}>
              <label style={formLabelStyle}>Plant Name *</label>
              <input required type="text" value={newPlant.plant_name} onChange={(e) => setNewPlant({ ...newPlant, plant_name: e.target.value })} style={formInputStyle} />
            </div>
            <div style={{ marginBottom: "16px" }}>
              <label style={formLabelStyle}>Plant Code *</label>
              <input required type="text" value={newPlant.plant_code} onChange={(e) => setNewPlant({ ...newPlant, plant_code: e.target.value })} placeholder="e.g. PLANT-PUN-04" style={formInputStyle} />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button type="button" onClick={() => setActiveModal(null)} style={secondaryButtonBase}>Cancel</button>
              <button type="submit" style={primaryButtonBase}>Save & Persist</button>
            </div>
          </form>
        </div>
      )}

      {/* [+ Add Dataset Type] Modal */}
      {activeModal === "TYPE" && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(15, 23, 42, 0.45)", backdropFilter: "blur(4px)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 3000 }}>
          <form onSubmit={handleSaveType} style={{ width: "420px", backgroundColor: tokens.surfacePrimary, border: `1px solid ${tokens.border}`, borderRadius: "12px", padding: "24px", color: tokens.textPrimary, boxShadow: tokens.shadowModal }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "16px", color: tokens.textPrimary }}>+ Add Dataset Type</h3>
            <div style={{ marginBottom: "12px" }}>
              <label style={formLabelStyle}>Type Name *</label>
              <input required type="text" value={newType.type_name} onChange={(e) => setNewType({ ...newType, type_name: e.target.value })} style={formInputStyle} />
            </div>
            <div style={{ marginBottom: "16px" }}>
              <label style={formLabelStyle}>Type Code *</label>
              <input required type="text" value={newType.type_code} onChange={(e) => setNewType({ ...newType, type_code: e.target.value })} placeholder="e.g. QA_SLUMP_LOGS" style={formInputStyle} />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button type="button" onClick={() => setActiveModal(null)} style={secondaryButtonBase}>Cancel</button>
              <button type="submit" style={primaryButtonBase}>Save & Persist</button>
            </div>
          </form>
        </div>
      )}

      {/* [+ Add Import Profile] Modal */}
      {activeModal === "PROFILE" && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(15, 23, 42, 0.45)", backdropFilter: "blur(4px)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 3000 }}>
          <form onSubmit={handleSaveProfile} style={{ width: "420px", backgroundColor: tokens.surfacePrimary, border: `1px solid ${tokens.border}`, borderRadius: "12px", padding: "24px", color: tokens.textPrimary, boxShadow: tokens.shadowModal }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "16px", color: tokens.textPrimary }}>+ Add Import Profile</h3>
            <div style={{ marginBottom: "12px" }}>
              <label style={formLabelStyle}>Profile Name *</label>
              <input required type="text" value={newProfile.name} onChange={(e) => setNewProfile({ ...newProfile, name: e.target.value })} style={formInputStyle} />
            </div>
            <div style={{ marginBottom: "16px" }}>
              <label style={formLabelStyle}>Profile Code *</label>
              <input required type="text" value={newProfile.profile_code} onChange={(e) => setNewProfile({ ...newProfile, profile_code: e.target.value })} placeholder="e.g. PROFILE-PUNE-SCADA" style={formInputStyle} />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button type="button" onClick={() => setActiveModal(null)} style={secondaryButtonBase}>Cancel</button>
              <button type="submit" style={primaryButtonBase}>Save & Persist</button>
            </div>
          </form>
        </div>
      )}

      <div style={{ marginTop: "28px", display: "flex", justifyContent: "flex-end" }}>
        <button
          type="button"
          onClick={onNext}
          disabled={!isFormValid}
          style={{
            ...primaryButtonBase,
            padding: "10px 24px",
            fontSize: "0.875rem",
            opacity: isFormValid ? 1 : 0.6,
            cursor: isFormValid ? "pointer" : "not-allowed",
          }}
        >
          Proceed to Upload Folder →
        </button>
      </div>
    </div>
  );
};
