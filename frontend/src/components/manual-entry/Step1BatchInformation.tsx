/**
 * Step 1: Batch Information & Master Data Selection.
 * Responsive Mobile + Tablet + Desktop Hardening.
 * Enterprise Operations Light Theme Migration.
 */

import React, { useState, useEffect } from "react";
import {
  masterDataService,
  TargetPlant,
  Recipe,
  Customer,
  UserIdentity,
  ManualDraftResponse,
} from "../../services/masterDataService";
import {
  enterpriseLightTokens,
  formInputStyle,
  formLabelStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
} from "./enterpriseLightTokens";

interface Step1Props {
  initialDraft: ManualDraftResponse | null;
  onNext: (draft: ManualDraftResponse) => void;
}

export const Step1BatchInformation: React.FC<Step1Props> = ({ initialDraft, onNext }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [operator, setOperator] = useState<UserIdentity | null>(null);
  const [plants, setPlants] = useState<TargetPlant[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);

  const [selectedPlant, setSelectedPlant] = useState<string>("");
  const [selectedRecipe, setSelectedRecipe] = useState<string>("");
  const [selectedCustomer, setSelectedCustomer] = useState<string>("");
  const [productionDate, setProductionDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [shift, setShift] = useState<string>("DAY_SHIFT");
  const [orderNumber, setOrderNumber] = useState<string>("");
  const [remarks, setRemarks] = useState<string>("");

  const [activeModal, setActiveModal] = useState<"PLANT" | "RECIPE" | "CUSTOMER" | null>(null);
  const [newPlant, setNewPlant] = useState({ plant_name: "", plant_code: "", region: "Western Region" });
  const [newRecipe, setNewRecipe] = useState({ recipe_name: "", recipe_code: "", grade: "M30" });
  const [newCustomer, setNewCustomer] = useState({ legal_name: "", customer_code: "" });
  const [modalSubmitting, setModalSubmitting] = useState<boolean>(false);
  const [modalError, setModalError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMasterData() {
      try {
        setLoading(true);
        const [opData, plantsData, recipesData, custData] = await Promise.all([
          masterDataService.getUserSession(),
          masterDataService.getTargetPlants(),
          masterDataService.getRecipes(),
          masterDataService.getCustomers(),
        ]);
        setOperator(opData);
        setPlants(plantsData);
        setRecipes(recipesData);
        setCustomers(custData);

        if (initialDraft) {
          setSelectedPlant(initialDraft.plant_code || "");
          setSelectedRecipe(initialDraft.recipe_code || "");
          setSelectedCustomer(initialDraft.customer_code || "");
          setProductionDate(initialDraft.production_date || new Date().toISOString().split("T")[0]);
          setShift(initialDraft.shift || "DAY_SHIFT");
          setOrderNumber(initialDraft.order_number || "");
          setRemarks(initialDraft.remarks || "");
        } else {
          if (plantsData.length > 0) setSelectedPlant(plantsData[0].plant_code);
          if (recipesData.length > 0) setSelectedRecipe(recipesData[0].recipe_code);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load master data.");
      } finally {
        setLoading(false);
      }
    }
    loadMasterData();
  }, [initialDraft]);

  const handleAddPlant = async () => {
    if (!newPlant.plant_name || !newPlant.plant_code) {
      setModalError("Plant name and plant code are required.");
      return;
    }
    try {
      setModalSubmitting(true);
      setModalError(null);
      const created = await masterDataService.addTargetPlant(newPlant.plant_name, newPlant.plant_code, newPlant.region);
      setPlants((prev) => [...prev, created]);
      setSelectedPlant(created.plant_code);
      setActiveModal(null);
      setNewPlant({ plant_name: "", plant_code: "", region: "Western Region" });
    } catch (err: any) {
      setModalError(err.message || "Failed to add plant.");
    } finally {
      setModalSubmitting(false);
    }
  };

  const handleAddRecipe = async () => {
    if (!newRecipe.recipe_name || !newRecipe.recipe_code) {
      setModalError("Recipe name and recipe code are required.");
      return;
    }
    try {
      setModalSubmitting(true);
      setModalError(null);
      const created = await masterDataService.addRecipe(newRecipe.recipe_name, newRecipe.recipe_code, newRecipe.grade);
      setRecipes((prev) => [...prev, created]);
      setSelectedRecipe(created.recipe_code);
      setActiveModal(null);
      setNewRecipe({ recipe_name: "", recipe_code: "", grade: "M30" });
    } catch (err: any) {
      setModalError(err.message || "Failed to add recipe.");
    } finally {
      setModalSubmitting(false);
    }
  };

  const handleAddCustomer = async () => {
    if (!newCustomer.legal_name || !newCustomer.customer_code) {
      setModalError("Legal name and customer code are required.");
      return;
    }
    try {
      setModalSubmitting(true);
      setModalError(null);
      const created = await masterDataService.addCustomer(newCustomer.legal_name, newCustomer.customer_code);
      setCustomers((prev) => [...prev, created]);
      setSelectedCustomer(created.customer_code);
      setActiveModal(null);
      setNewCustomer({ legal_name: "", customer_code: "" });
    } catch (err: any) {
      setModalError(err.message || "Failed to add customer.");
    } finally {
      setModalSubmitting(false);
    }
  };

  const handleSaveDraft = async () => {
    if (!selectedPlant) {
      setError("Please select a target production plant.");
      return;
    }
    if (!selectedRecipe) {
      setError("Please select a mix design / recipe.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const res = await masterDataService.createManualDraft({
        plant_code: selectedPlant,
        recipe_code: selectedRecipe,
        customer_code: selectedCustomer || undefined,
        production_date: productionDate,
        shift: shift,
        order_number: orderNumber || undefined,
        remarks: remarks || undefined,
      });
      onNext(res);
    } catch (err: any) {
      setError(err.message || "Failed to create production batch draft.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: "40px", textAlign: "center", color: enterpriseLightTokens.textMuted }}>
        <div>Loading certified master data & authenticated operator identity...</div>
      </div>
    );
  }

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

      {/* Operator Session Context Card with responsive wrap */}
      <div
        style={{
          padding: "14px 18px",
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
        <div style={{ minWidth: "200px" }}>
          <div style={{ fontSize: "0.72rem", color: enterpriseLightTokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>
            Authenticated Operator Identity
          </div>
          <div className="text-wrap-safe" style={{ fontSize: "0.92rem", fontWeight: 700, color: enterpriseLightTokens.textPrimary, marginTop: "2px" }}>
            {operator?.name} ({operator?.operator_id})
          </div>
        </div>
        <span
          style={{
            backgroundColor: enterpriseLightTokens.successGreenLight,
            color: enterpriseLightTokens.successGreen,
            padding: "4px 10px",
            borderRadius: "4px",
            fontSize: "0.75rem",
            fontWeight: 600,
            border: `1px solid ${enterpriseLightTokens.successGreenBorder}`,
            whiteSpace: "nowrap",
          }}
        >
          Active Session ({operator?.role})
        </span>
      </div>

      {/* Server Batch Identifiers Banner (If draft exists) */}
      {initialDraft && (
        <div
          className="responsive-stat-grid"
          style={{
            padding: "14px 18px",
            backgroundColor: enterpriseLightTokens.secondarySurface,
            border: `1px solid ${enterpriseLightTokens.border}`,
            borderRadius: enterpriseLightTokens.radius,
          }}
        >
          <div>
            <div style={{ fontSize: "0.72rem", color: enterpriseLightTokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Server Draft ID</div>
            <div style={{ fontSize: "0.88rem", fontWeight: 700, color: enterpriseLightTokens.primaryAccent, marginTop: "2px" }}>{initialDraft.draft_id}</div>
          </div>
          <div>
            <div style={{ fontSize: "0.72rem", color: enterpriseLightTokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Batch #</div>
            <div style={{ fontSize: "0.88rem", fontWeight: 700, color: enterpriseLightTokens.textPrimary, marginTop: "2px" }}>{initialDraft.batch_number}</div>
          </div>
          <div>
            <div style={{ fontSize: "0.72rem", color: enterpriseLightTokens.textMuted, textTransform: "uppercase", fontWeight: 600 }}>Status</div>
            <div style={{ fontSize: "0.88rem", fontWeight: 700, color: enterpriseLightTokens.textSecondary, marginTop: "2px" }}>{initialDraft.status}</div>
          </div>
        </div>
      )}

      {/* Master Data Selection Form with responsive column grid */}
      <div className="responsive-form-grid">
        {/* Plant Selection */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
            <label style={formLabelStyle}>
              Target Plant Location <span style={{ color: enterpriseLightTokens.errorRed }}>*</span>
            </label>
            <button
              type="button"
              onClick={() => setActiveModal("PLANT")}
              style={{ background: "none", border: "none", color: enterpriseLightTokens.primaryAccent, fontSize: "0.75rem", cursor: "pointer", fontWeight: 600 }}
            >
              + Add Plant
            </button>
          </div>
          <select
            value={selectedPlant}
            onChange={(e) => setSelectedPlant(e.target.value)}
            style={formInputStyle}
            required
          >
            <option value="">-- Select Ready-Mix Plant --</option>
            {plants.map((p) => (
              <option key={p.plant_code} value={p.plant_code}>
                {p.plant_name} ({p.plant_code})
              </option>
            ))}
          </select>
        </div>

        {/* Recipe Selection */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
            <label style={formLabelStyle}>
              Mix Design Recipe <span style={{ color: enterpriseLightTokens.errorRed }}>*</span>
            </label>
            <button
              type="button"
              onClick={() => setActiveModal("RECIPE")}
              style={{ background: "none", border: "none", color: enterpriseLightTokens.primaryAccent, fontSize: "0.75rem", cursor: "pointer", fontWeight: 600 }}
            >
              + Add Mix Design
            </button>
          </div>
          <select
            value={selectedRecipe}
            onChange={(e) => setSelectedRecipe(e.target.value)}
            style={formInputStyle}
            required
          >
            <option value="">-- Select Mix Design / Grade --</option>
            {recipes.map((r) => (
              <option key={r.recipe_code} value={r.recipe_code}>
                {r.recipe_name} ({r.recipe_code} - {r.grade})
              </option>
            ))}
          </select>
        </div>

        {/* Customer Selection */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
            <label style={formLabelStyle}>Customer Account (Optional)</label>
            <button
              type="button"
              onClick={() => setActiveModal("CUSTOMER")}
              style={{ background: "none", border: "none", color: enterpriseLightTokens.primaryAccent, fontSize: "0.75rem", cursor: "pointer", fontWeight: 600 }}
            >
              + Add Customer
            </button>
          </div>
          <select
            value={selectedCustomer || ""}
            onChange={(e) => setSelectedCustomer(e.target.value)}
            style={formInputStyle}
          >
            <option value="">-- No Customer Assigned / Internal Production --</option>
            {customers.map((c) => (
              <option key={c.customer_code} value={c.customer_code}>
                {c.legal_name} ({c.customer_code})
              </option>
            ))}
          </select>
        </div>

        {/* Production Date */}
        <div>
          <label style={formLabelStyle}>
            Production Date <span style={{ color: enterpriseLightTokens.errorRed }}>*</span>
          </label>
          <input
            type="date"
            value={productionDate}
            onChange={(e) => setProductionDate(e.target.value)}
            style={formInputStyle}
            required
          />
        </div>

        {/* Shift */}
        <div>
          <label style={formLabelStyle}>Operational Shift</label>
          <select value={shift} onChange={(e) => setShift(e.target.value)} style={formInputStyle}>
            <option value="DAY_SHIFT">Day Shift (06:00 - 14:00)</option>
            <option value="EVENING_SHIFT">Evening Shift (14:00 - 22:00)</option>
            <option value="NIGHT_SHIFT">Night Shift (22:00 - 06:00)</option>
            <option value="GENERAL_SHIFT">General Operations (09:00 - 18:00)</option>
          </select>
        </div>

        {/* ERP Order Number */}
        <div>
          <label style={formLabelStyle}>ERP / Dispatch Order # (Optional)</label>
          <input
            type="text"
            placeholder="e.g. ORD-2026-0915-442"
            value={orderNumber || ""}
            onChange={(e) => setOrderNumber(e.target.value)}
            style={formInputStyle}
          />
        </div>
      </div>

      {/* Remarks */}
      <div>
        <label style={formLabelStyle}>Batch Execution Remarks (Optional)</label>
        <textarea
          rows={2}
          placeholder="Specific batching instructions, delivery notes, or site constraints..."
          value={remarks || ""}
          onChange={(e) => setRemarks(e.target.value)}
          style={{ ...formInputStyle, resize: "vertical" }}
        />
      </div>

      {/* Action Navigation Footer */}
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "flex-end", gap: "10px", marginTop: "8px" }}>
        <button
          type="button"
          onClick={handleSaveDraft}
          disabled={submitting}
          style={{
            ...primaryButtonStyle,
            opacity: submitting ? 0.7 : 1,
            cursor: submitting ? "not-allowed" : "pointer",
          }}
        >
          {submitting ? "Saving Draft..." : initialDraft ? "Save Step 1 & Proceed →" : "Create Production Draft & Proceed →"}
        </button>
      </div>

      {/* Inline Modal: Add Plant */}
      {activeModal === "PLANT" && (
        <div style={modalOverlayStyle}>
          <div style={modalBoxStyle}>
            <h3 style={modalHeaderStyle}>Add New Production Plant</h3>
            {modalError && <div style={modalErrorStyle}>{modalError}</div>}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={formLabelStyle}>Plant Name *</label>
                <input
                  type="text"
                  placeholder="e.g. Pune Central Batching Unit"
                  value={newPlant.plant_name}
                  onChange={(e) => setNewPlant({ ...newPlant, plant_name: e.target.value })}
                  style={formInputStyle}
                />
              </div>
              <div>
                <label style={formLabelStyle}>Plant Code (Max 16 chars) *</label>
                <input
                  type="text"
                  placeholder="e.g. PLANT-PUNE-01"
                  value={newPlant.plant_code}
                  onChange={(e) => setNewPlant({ ...newPlant, plant_code: e.target.value.toUpperCase() })}
                  style={formInputStyle}
                />
              </div>
              <div>
                <label style={formLabelStyle}>Region</label>
                <input
                  type="text"
                  value={newPlant.region}
                  onChange={(e) => setNewPlant({ ...newPlant, region: e.target.value })}
                  style={formInputStyle}
                />
              </div>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "18px" }}>
              <button type="button" onClick={() => setActiveModal(null)} style={secondaryButtonStyle}>
                Cancel
              </button>
              <button type="button" onClick={handleAddPlant} disabled={modalSubmitting} style={primaryButtonStyle}>
                {modalSubmitting ? "Adding..." : "Save Plant"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Inline Modal: Add Mix Design Recipe */}
      {activeModal === "RECIPE" && (
        <div style={modalOverlayStyle}>
          <div style={modalBoxStyle}>
            <h3 style={modalHeaderStyle}>Add Mix Design Recipe</h3>
            {modalError && <div style={modalErrorStyle}>{modalError}</div>}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={formLabelStyle}>Recipe Name *</label>
                <input
                  type="text"
                  placeholder="e.g. M35 High Flow Pumpable"
                  value={newRecipe.recipe_name}
                  onChange={(e) => setNewRecipe({ ...newRecipe, recipe_name: e.target.value })}
                  style={formInputStyle}
                />
              </div>
              <div>
                <label style={formLabelStyle}>Recipe Code (Max 32 chars) *</label>
                <input
                  type="text"
                  placeholder="e.g. M35_PUMP_STD"
                  value={newRecipe.recipe_code}
                  onChange={(e) => setNewRecipe({ ...newRecipe, recipe_code: e.target.value.toUpperCase() })}
                  style={formInputStyle}
                />
              </div>
              <div>
                <label style={formLabelStyle}>Characteristic Grade</label>
                <select
                  value={newRecipe.grade}
                  onChange={(e) => setNewRecipe({ ...newRecipe, grade: e.target.value })}
                  style={formInputStyle}
                >
                  <option value="M10">M10</option>
                  <option value="M15">M15</option>
                  <option value="M20">M20</option>
                  <option value="M25">M25</option>
                  <option value="M30">M30</option>
                  <option value="M35">M35</option>
                  <option value="M40">M40</option>
                  <option value="M45">M45</option>
                  <option value="M50">M50</option>
                </select>
              </div>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "18px" }}>
              <button type="button" onClick={() => setActiveModal(null)} style={secondaryButtonStyle}>
                Cancel
              </button>
              <button type="button" onClick={handleAddRecipe} disabled={modalSubmitting} style={primaryButtonStyle}>
                {modalSubmitting ? "Adding..." : "Save Recipe"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Inline Modal: Add Customer */}
      {activeModal === "CUSTOMER" && (
        <div style={modalOverlayStyle}>
          <div style={modalBoxStyle}>
            <h3 style={modalHeaderStyle}>Add Customer Account</h3>
            {modalError && <div style={modalErrorStyle}>{modalError}</div>}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={formLabelStyle}>Legal Entity Name *</label>
                <input
                  type="text"
                  placeholder="e.g. Larsen & Toubro Construction Ltd"
                  value={newCustomer.legal_name}
                  onChange={(e) => setNewCustomer({ ...newCustomer, legal_name: e.target.value })}
                  style={formInputStyle}
                />
              </div>
              <div>
                <label style={formLabelStyle}>Customer Code *</label>
                <input
                  type="text"
                  placeholder="e.g. CUST-LT-01"
                  value={newCustomer.customer_code}
                  onChange={(e) => setNewCustomer({ ...newCustomer, customer_code: e.target.value.toUpperCase() })}
                  style={formInputStyle}
                />
              </div>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "18px" }}>
              <button type="button" onClick={() => setActiveModal(null)} style={secondaryButtonStyle}>
                Cancel
              </button>
              <button type="button" onClick={handleAddCustomer} disabled={modalSubmitting} style={primaryButtonStyle}>
                {modalSubmitting ? "Adding..." : "Save Customer"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const modalOverlayStyle: React.CSSProperties = {
  position: "fixed",
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: "rgba(15, 23, 42, 0.5)",
  backdropFilter: "blur(2px)",
  zIndex: 1100,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "16px",
};

const modalBoxStyle: React.CSSProperties = {
  backgroundColor: enterpriseLightTokens.surfaceCard,
  border: `1px solid ${enterpriseLightTokens.border}`,
  borderRadius: enterpriseLightTokens.radiusLarge,
  width: "100%",
  maxWidth: "460px",
  padding: "20px",
  boxShadow: enterpriseLightTokens.shadowModal,
  color: enterpriseLightTokens.textPrimary,
};

const modalHeaderStyle: React.CSSProperties = {
  margin: "0 0 16px 0",
  fontSize: "1.1rem",
  fontWeight: 700,
  color: enterpriseLightTokens.textPrimary,
};

const modalErrorStyle: React.CSSProperties = {
  padding: "8px 12px",
  backgroundColor: enterpriseLightTokens.errorRedLight,
  border: `1px solid ${enterpriseLightTokens.errorRedBorder}`,
  borderRadius: enterpriseLightTokens.radius,
  color: enterpriseLightTokens.errorRed,
  fontSize: "0.8rem",
  marginBottom: "12px",
};
