import { RecommendationGovernanceGate } from "./RecommendationGovernanceGate";
import { RecipeImpactComparison } from "./RecipeImpactComparison";
import { CostImpactComparison } from "./CostImpactComparison";
import { BatchPlantIcon, MixerTruckIcon } from "../../icons";
import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Zap,
  Target,
  ShieldCheck,
  Cpu,
  Layers,
  Award,
  AlertCircle,
  RefreshCw,
  AlertTriangle,
  FileText,
  Info,
} from "lucide-react";
import {
  ParetoFrontierChart,
  OptimizationCandidateDTO,
} from "./ParetoFrontierChart";
import {
  optimizationService,
  OptimizationRunResponse,
  CandidateEvaluationResponse,
} from "../../../services/optimizationService";
import { masterDataService, Recipe } from "../../../services/masterDataService";

interface MixOptimizationSectionProps {
  selectedPlant?: string;
  onActiveRunChange?: (runId: string | null) => void;
  onActiveCandidateChange?: (candidateId: string | null) => void;
}

export const MixOptimizationSection: React.FC<MixOptimizationSectionProps> = ({
  selectedPlant = "PLANT-01",
  onActiveRunChange,
  onActiveCandidateChange,
}) => {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [selectedRecipeCode, setSelectedRecipeCode] = useState<string>("");
  const [selectedObjective, setSelectedObjective] = useState<"MINIMIZE_BINDER" | "MINIMIZE_COST" | "BALANCED">("MINIMIZE_BINDER");
  const [latestRun, setLatestRun] = useState<OptimizationRunResponse | null>(null);
  const [evaluationResult, setEvaluationResult] = useState<CandidateEvaluationResponse | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<OptimizationCandidateDTO | null>(null);

  const [isLoadingRecipes, setIsLoadingRecipes] = useState<boolean>(true);
  const [isTriggering, setIsTriggering] = useState<boolean>(false);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const tokens = {
    surfacePrimary: "#FFFFFF",
    surfaceSecondary: "#F8FAFC",
    border: "#E2E8F0",
    borderLight: "#F1F5F9",
    textPrimary: "#0F172A",
    textSecondary: "#475569",
    textMuted: "#94A3B8",
    primaryAccent: "#2563EB",
    primaryAccentLight: "rgba(37, 99, 235, 0.08)",
    successGreen: "#059669",
    successGreenLight: "rgba(5, 150, 105, 0.08)",
    warningAmber: "#D97706",
    warningAmberLight: "rgba(217, 119, 6, 0.08)",
    dangerRed: "#DC2626",
    dangerRedLight: "rgba(220, 38, 38, 0.08)",
    fontMono: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
    radius: "8px",
    radiusLarge: "12px",
  };

  useEffect(() => {
    onActiveRunChange?.(latestRun?.run_id ?? null);
  }, [latestRun, onActiveRunChange]);

  useEffect(() => {
    const candId = (selectedCandidate?.id || (selectedCandidate as any)?.candidate_id) ?? null;
    onActiveCandidateChange?.(candId);
  }, [selectedCandidate, onActiveCandidateChange]);

  useEffect(() => {
    fetchMasterRecipes();
  }, [selectedPlant]);

  const fetchMasterRecipes = async () => {
    setIsLoadingRecipes(true);
    try {
      const items = await masterDataService.getRecipes();
      setRecipes(items || []);
      if (items && items.length > 0) {
        setSelectedRecipeCode(items[0].recipe_code);
        fetchLatestRun(items[0].recipe_code);
      }
    } catch (err) {
      console.error("Failed to load master recipes:", err);
    } finally {
      setIsLoadingRecipes(false);
    }
  };

  const fetchLatestRun = async (recipeCode: string) => {
    try {
      const data = await optimizationService.getLatestRun(recipeCode, selectedPlant);
      if (data && data.run_id) {
        setLatestRun(data);
        await fetchCandidates(data.run_id);
      } else {
        setLatestRun(null);
        setEvaluationResult(null);
        setSelectedCandidate(null);
      }
    } catch (err) {
      console.error("Failed to fetch latest run:", err);
    }
  };

  const fetchCandidates = async (runId: string) => {
    try {
      const data = await optimizationService.evaluateRun(runId);
      if (data) {
        setEvaluationResult(data);
        if (data.candidates && data.candidates.length > 0) {
          const firstPareto = data.candidates.find((c) => c.is_feasible && c.is_non_dominated);
          const firstFeasible = data.candidates.find((c) => c.is_feasible);
          setSelectedCandidate((firstPareto || firstFeasible || data.candidates[0]) as unknown as OptimizationCandidateDTO);
        }
      }
    } catch (err) {
      console.error("Failed to fetch candidates:", err);
    }
  };

  const handleRecipeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const code = e.target.value;
    setSelectedRecipeCode(code);
    fetchLatestRun(code);
  };

  const handleTriggerRun = async () => {
    if (!selectedRecipeCode) return;
    setIsTriggering(true);
    setErrorMessage(null);

    try {
      const selected = recipes.find((r) => r.recipe_code === selectedRecipeCode);
      const recipeId = selected ? selected.id : selectedRecipeCode;

      const runData = await optimizationService.triggerRun({
        recipe_id: recipeId,
        plant_code: selectedPlant,
        optimization_objective: selectedObjective,
      });

      setLatestRun(runData);
      if (runData && runData.run_id) {
        await fetchCandidates(runData.run_id);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to trigger AI optimization run");
    } finally {
      setIsTriggering(false);
    }
  };

  const evaluateRun = async (runId: string) => {
    setIsEvaluating(true);
    setErrorMessage(null);
    try {
      const evalData = await optimizationService.evaluateRun(runId);
      setEvaluationResult(evalData);
      if (evalData.candidates && evalData.candidates.length > 0) {
        const firstPareto = evalData.candidates.find((c) => c.is_feasible && c.is_non_dominated);
        const firstFeasible = evalData.candidates.find((c) => c.is_feasible);
        setSelectedCandidate((firstPareto || firstFeasible || evalData.candidates[0]) as unknown as OptimizationCandidateDTO);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Candidate solver evaluation failed");
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "clamp(16px, 3vw, 24px)",
        width: "100%",
        maxWidth: "100%",
        boxSizing: "border-box",
      }}
    >
      {/* 1. Header & Configuration Toolbar */}
      <div
        style={{
          backgroundColor: tokens.surfacePrimary,
          border: `1px solid ${tokens.border}`,
          borderRadius: tokens.radiusLarge,
          padding: "clamp(16px, 3vw, 20px)",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
          boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: tokens.radius,
                backgroundColor: tokens.primaryAccentLight,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <BatchPlantIcon size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ margin: 0, fontSize: "clamp(1rem, 2.5vw, 1.15rem)", fontWeight: 700, color: tokens.textPrimary }}>
                  AI Mix Optimization & Target Workspace
                </h2>
                <span
                  style={{
                    fontSize: "0.68rem",
                    backgroundColor: tokens.primaryAccentLight,
                    color: tokens.primaryAccent,
                    padding: "2px 6px",
                    borderRadius: "4px",
                    fontWeight: 700,
                  }}
                >
                  Active Candidate Solver & Pareto Frontier
                </span>
              </div>
              <p style={{ margin: 0, fontSize: "0.8rem", color: tokens.textMuted }}>
                Physical volume balance, IS standard validation, ML inference, and Pareto frontier solver
              </p>
            </div>
          </div>

          {/* Model Status Badge */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "4px 10px",
              borderRadius: "20px",
              backgroundColor: tokens.warningAmberLight,
              border: "1px solid rgba(217, 119, 6, 0.2)",
              fontSize: "0.75rem",
              fontWeight: 600,
              color: tokens.warningAmber,
            }}
          >
            <ShieldCheck size={14} />
            <span>ACTIVE — BASELINE MODEL | Analytical Prediction (Limited Validation)</span>
          </div>
        </div>

        {/* Controls Row */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "12px",
            alignItems: "flex-end",
          }}
        >
          {/* Target Master Mix Dropdown */}
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <label style={{ fontSize: "0.78rem", fontWeight: 600, color: tokens.textSecondary }}>
              Target Master Mix Design:
            </label>
            <select
              value={selectedRecipeCode}
              onChange={handleRecipeChange}
              disabled={isLoadingRecipes || isTriggering || isEvaluating}
              style={{
                padding: "8px 12px",
                borderRadius: tokens.radius,
                border: `1px solid ${tokens.border}`,
                backgroundColor: tokens.surfaceSecondary,
                fontSize: "0.85rem",
                color: tokens.textPrimary,
                fontWeight: 600,
                outline: "none",
                cursor: "pointer",
              }}
            >
              {recipes.map((r) => (
                <option key={r.id} value={r.recipe_code}>
                  {r.recipe_code} ({r.grade}) — {r.recipe_name}
                </option>
              ))}
            </select>
          </div>

          {/* Optimization Objective Dropdown */}
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <label style={{ fontSize: "0.78rem", fontWeight: 600, color: tokens.textSecondary }}>
              Optimization Objective:
            </label>
            <select
              value={selectedObjective}
              onChange={(e) => setSelectedObjective(e.target.value as any)}
              disabled={isTriggering || isEvaluating}
              style={{
                padding: "8px 12px",
                borderRadius: tokens.radius,
                border: `1px solid ${tokens.border}`,
                backgroundColor: tokens.surfaceSecondary,
                fontSize: "0.85rem",
                color: tokens.textPrimary,
                fontWeight: 600,
                outline: "none",
                cursor: "pointer",
              }}
            >
              <option value="MINIMIZE_BINDER">MINIMIZE BINDER INTENSITY (kg/m³)</option>
              <option value="MINIMIZE_COST">MINIMIZE COST (₹/m³) — [Pricing Guard Active]</option>
              <option value="BALANCED">BALANCED MULTI-OBJECTIVE (Cost & Binder)</option>
            </select>
          </div>

          {/* Action Trigger Button */}
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={handleTriggerRun}
              disabled={isTriggering || isEvaluating || !selectedRecipeCode}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                padding: "9px 18px",
                borderRadius: tokens.radius,
                backgroundColor: isTriggering || isEvaluating ? tokens.textMuted : tokens.primaryAccent,
                color: "#FFFFFF",
                fontSize: "0.85rem",
                fontWeight: 700,
                border: "none",
                cursor: isTriggering || isEvaluating ? "not-allowed" : "pointer",
                transition: "background-color 0.2s",
                boxShadow: "0 2px 4px rgba(37, 99, 235, 0.2)",
                flex: 1,
              }}
            >
              {isTriggering || isEvaluating ? <RefreshCw size={16} className="animate-spin" /> : <Zap size={16} />}
              {isTriggering
                ? "Creating Snapshot..."
                : isEvaluating
                ? "Evaluating Solver..."
                : "Run AI Optimization"}
            </button>
          </div>
        </div>

        {/* Objective Warnings / Notices */}
        {selectedObjective === "MINIMIZE_COST" && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "8px 12px",
              borderRadius: tokens.radius,
              backgroundColor: tokens.warningAmberLight,
              border: "1px solid rgba(217, 119, 6, 0.25)",
              color: tokens.warningAmber,
              fontSize: "0.78rem",
              fontWeight: 600,
            }}
          >
            <AlertTriangle size={15} />
            <span>
              Material pricing is not currently configured in the database snapshot. Optimization will evaluate Binder Intensity as the primary objective.
            </span>
          </div>
        )}

        {selectedObjective === "BALANCED" && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "8px 12px",
              borderRadius: tokens.radius,
              backgroundColor: tokens.primaryAccentLight,
              border: "1px solid rgba(37, 99, 235, 0.2)",
              color: tokens.primaryAccent,
              fontSize: "0.78rem",
              fontWeight: 600,
            }}
          >
            <Info size={15} />
            <span>
              Balanced multi-criteria solver presents the full non-dominated Pareto frontier for engineering inspection.
            </span>
          </div>
        )}

        {/* Error Notice */}
        {errorMessage && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "8px 12px",
              borderRadius: tokens.radius,
              backgroundColor: tokens.dangerRedLight,
              border: "1px solid rgba(220, 38, 38, 0.2)",
              color: tokens.dangerRed,
              fontSize: "0.8rem",
              fontWeight: 600,
            }}
          >
            <AlertCircle size={16} />
            <span>{errorMessage}</span>
          </div>
        )}
      </div>

      {/* 2. Run Context Banner & Diagnostics (If Run Exists) */}
      {latestRun && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "12px",
          }}
        >
          {/* Target Strength Context Card */}
          <div
            style={{
              backgroundColor: tokens.surfacePrimary,
              border: `1px solid ${tokens.border}`,
              borderRadius: tokens.radius,
              padding: "14px 16px",
              display: "flex",
              flexDirection: "column",
              gap: "6px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ margin: 0, fontSize: "0.75rem", fontWeight: 700, color: tokens.textSecondary, textTransform: "uppercase" }}>
                Target Mean Strength
              </h3>
              <span style={{ fontSize: "0.7rem", backgroundColor: tokens.primaryAccentLight, color: tokens.primaryAccent, padding: "1px 6px", borderRadius: "4px", fontWeight: 700 }}>
                {latestRun.recipe_snapshot.grade}
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
              <span style={{ fontSize: "1.4rem", fontWeight: 800, color: tokens.textPrimary }}>
                {latestRun.target_strength_snapshot.target_mean_strength_fck_prime_mpa} MPa
              </span>
              <span style={{ fontSize: "0.78rem", color: tokens.textMuted }}>
                Target Mean (f&apos;ck)
              </span>
            </div>
            <div style={{ fontSize: "0.72rem", color: tokens.textSecondary }}>
              fck: {latestRun.target_strength_snapshot.characteristic_strength_fck_mpa} MPa | σ: {latestRun.target_strength_snapshot.standard_deviation_mpa} MPa ({latestRun.target_strength_snapshot.standard_deviation_source === 'HISTORICAL_SQC_SAMPLE' ? 'Historical SQC Sample' : 'IS 10262:2019 Table 2'})
            </div>
          </div>

          {/* Model Lineage Card */}
          <div
            style={{
              backgroundColor: tokens.surfacePrimary,
              border: `1px solid ${tokens.border}`,
              borderRadius: tokens.radius,
              padding: "14px 16px",
              display: "flex",
              flexDirection: "column",
              gap: "6px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ margin: 0, fontSize: "0.75rem", fontWeight: 700, color: tokens.textSecondary, textTransform: "uppercase" }}>
                Inference Model Lineage
              </h3>
              <span style={{ fontSize: "0.7rem", backgroundColor: "rgba(124, 58, 237, 0.08)", color: "#7C3AED", padding: "1px 6px", borderRadius: "4px", fontFamily: tokens.fontMono, fontWeight: 700 }}>
                {latestRun.model_snapshot.model_version}
              </span>
            </div>
            <div style={{ fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
              {latestRun.model_snapshot.model_name}
            </div>
            <div style={{ fontSize: "0.72rem", color: tokens.warningAmber, fontWeight: 600 }}>
              {latestRun.model_snapshot.validation_status}
            </div>
          </div>

          {/* Engineering Constraints Card */}
          <div
            style={{
              backgroundColor: tokens.surfacePrimary,
              border: `1px solid ${tokens.border}`,
              borderRadius: tokens.radius,
              padding: "14px 16px",
              display: "flex",
              flexDirection: "column",
              gap: "6px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ margin: 0, fontSize: "0.75rem", fontWeight: 700, color: tokens.textSecondary, textTransform: "uppercase" }}>
                Engineering Constraints
              </h3>
              <span style={{ fontSize: "0.7rem", backgroundColor: tokens.successGreenLight, color: tokens.successGreen, padding: "1px 6px", borderRadius: "4px", fontWeight: 700 }}>
                IS 456 RCC — {latestRun.constraints_snapshot.exposure_class}
              </span>
            </div>
            <div style={{ fontSize: "0.75rem", color: tokens.textSecondary, display: "flex", flexDirection: "column", gap: "3px" }}>
              <div>
                <strong>IS 456 / IS 10262:</strong> Min Grade: ≥ M25 | Min Cement: ≥ 300 kg/m³ | Max W/B: ≤ 0.50
              </div>
              <div style={{ color: tokens.textMuted }}>
                <strong>Plant Policy:</strong> Fly Ash ≤ 35% | GGBS ≤ 50% | Admixture ≤ 2.0%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3. Pareto Frontier Chart & Candidates Workspace (Phase 5B) */}
      {evaluationResult && evaluationResult.candidates && evaluationResult.candidates.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Main Chart Component */}
          <div data-tour="optimization-pareto-chart">
            <ParetoFrontierChart
              candidates={evaluationResult.candidates as unknown as OptimizationCandidateDTO[]}
              baseline={evaluationResult.baseline_coordinates}
              targetMeanStrength={latestRun?.target_strength_snapshot.target_mean_strength_fck_prime_mpa || 38.25}
              fck={latestRun?.target_strength_snapshot.characteristic_strength_fck_mpa || 30.0}
              objective={evaluationResult.optimization_objective}
              selectedCandidateId={selectedCandidate?.id || null}
              onSelectCandidate={(cand) => setSelectedCandidate(cand)}
            />
          </div>

          {/* Candidate Inspection & Comparison Panel */}
          {selectedCandidate && (
            <div
              style={{
                backgroundColor: tokens.surfacePrimary,
                border: `1px solid ${tokens.border}`,
                borderRadius: tokens.radiusLarge,
                padding: "clamp(16px, 3vw, 20px)",
                display: "flex",
                flexDirection: "column",
                gap: "16px",
                boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
              }}
            >
              {/* Selected Candidate Header */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "12px",
                  borderBottom: `1px solid ${tokens.borderLight}`,
                  paddingBottom: "12px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div
                    style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: tokens.radius,
                      backgroundColor: selectedCandidate.is_feasible
                        ? selectedCandidate.is_non_dominated
                          ? tokens.successGreenLight
                          : tokens.primaryAccentLight
                        : tokens.dangerRedLight,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <MixerTruckIcon size={20} />
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 800, color: tokens.textPrimary }}>
                      Candidate Details: {selectedCandidate.candidate_identifier}
                    </h3>
                    <p style={{ margin: 0, fontSize: "0.75rem", color: tokens.textMuted }}>
                      Candidate Evaluation & Mix Proportions
                    </p>
                  </div>
                </div>

                {/* Status Badges */}
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      padding: "4px 8px",
                      borderRadius: "6px",
                      backgroundColor: selectedCandidate.is_feasible ? tokens.successGreenLight : tokens.dangerRedLight,
                      color: selectedCandidate.is_feasible ? tokens.successGreen : tokens.dangerRed,
                    }}
                  >
                    {selectedCandidate.is_feasible ? "FEASIBLE" : "INFEASIBLE"}
                  </span>
                  {selectedCandidate.is_feasible && selectedCandidate.is_non_dominated && (
                    <span
                      style={{
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        padding: "4px 8px",
                        borderRadius: "6px",
                        backgroundColor: "rgba(5, 150, 105, 0.12)",
                        color: "#059669",
                        border: "1px solid #059669",
                      }}
                    >
                      ★ PARETO FRONTIER OPTIMAL
                    </span>
                  )}
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      padding: "4px 8px",
                      borderRadius: "6px",
                      backgroundColor: tokens.surfaceSecondary,
                      color: tokens.textSecondary,
                      border: `1px solid ${tokens.border}`,
                    }}
                  >
                    {selectedCandidate.prediction_source_semantics}
                  </span>
                </div>
              </div>

              {/* KPI Summary Cards */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                  gap: "12px",
                }}
              >
                <div style={{ backgroundColor: tokens.surfaceSecondary, padding: "10px 14px", borderRadius: tokens.radius, border: `1px solid ${tokens.border}` }}>
                  <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontWeight: 600 }}>Predicted 28-Day Strength</div>
                  <div style={{ fontSize: "1.15rem", fontWeight: 800, color: tokens.textPrimary, marginTop: "2px" }}>
                    {selectedCandidate.predicted_strength_mpa.toFixed(1)} MPa
                  </div>
                  <div style={{ fontSize: "0.72rem", fontWeight: 700, color: selectedCandidate.strength_margin_mpa >= 0 ? tokens.successGreen : tokens.dangerRed, marginTop: "2px" }}>
                    {selectedCandidate.strength_margin_mpa >= 0 ? "+" : ""}{selectedCandidate.strength_margin_mpa.toFixed(2)} MPa Margin
                  </div>
                </div>

                <div style={{ backgroundColor: tokens.surfaceSecondary, padding: "10px 14px", borderRadius: tokens.radius, border: `1px solid ${tokens.border}` }}>
                  <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontWeight: 600 }}>Binder Content</div>
                  <div style={{ fontSize: "1.15rem", fontWeight: 800, color: tokens.textPrimary, marginTop: "2px" }}>
                    {selectedCandidate.binder_intensity_kg_m3.toFixed(1)} kg/m³
                  </div>
                  <div style={{ fontSize: "0.72rem", color: tokens.textSecondary, marginTop: "2px" }}>
                    W/B Ratio: {selectedCandidate.water_binder_ratio.toFixed(3)}
                  </div>
                </div>

                <div style={{ backgroundColor: tokens.surfaceSecondary, padding: "10px 14px", borderRadius: tokens.radius, border: `1px solid ${tokens.border}` }}>
                  <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontWeight: 600 }}>Absolute Yield</div>
                  <div style={{ fontSize: "1.15rem", fontWeight: 800, color: tokens.textPrimary, marginTop: "2px" }}>
                    {selectedCandidate.physical_volume_diagnostic.volume_balance_actual_m3.toFixed(3)} m³
                  </div>
                  <div style={{ fontSize: "0.72rem", color: tokens.successGreen, fontWeight: 700, marginTop: "2px" }}>
                    Δ {selectedCandidate.physical_volume_diagnostic.volume_balance_deviation_m3.toFixed(4)} m³ (Passed)
                  </div>
                </div>

                <div style={{ backgroundColor: tokens.surfaceSecondary, padding: "10px 14px", borderRadius: tokens.radius, border: `1px solid ${tokens.border}` }}>
                  <div style={{ fontSize: "0.72rem", color: tokens.textMuted, fontWeight: 600 }}>Cost per m³</div>
                  <div style={{ fontSize: "1.15rem", fontWeight: 800, color: tokens.textMuted, marginTop: "2px" }}>
                    {selectedCandidate.cost_per_m3 !== null ? `₹${selectedCandidate.cost_per_m3}` : "Not Configured"}
                  </div>
                  <div style={{ fontSize: "0.72rem", color: tokens.textMuted, marginTop: "2px" }}>
                    Cost Engine (Not Configured)
                  </div>
                </div>
              </div>

              {/* Constituent Proportions Table */}
              <div data-tour="optimization-candidate-table">
                <h4 style={{ margin: "0 0 8px 0", fontSize: "0.82rem", fontWeight: 700, color: tokens.textPrimary }}>
                  Batch Proportions (kg/m³ & Absolute Volume)
                </h4>
                <div style={{ overflowX: "auto", border: `1px solid ${tokens.border}`, borderRadius: tokens.radius }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.78rem" }}>
                    <thead>
                      <tr style={{ backgroundColor: tokens.surfaceSecondary, borderBottom: `1px solid ${tokens.border}`, textAlign: "left" }}>
                        <th style={{ padding: "8px 12px", color: tokens.textSecondary, fontWeight: 700 }}>Constituent Material</th>
                        <th style={{ padding: "8px 12px", color: tokens.textSecondary, fontWeight: 700 }}>Category</th>
                        <th style={{ padding: "8px 12px", color: tokens.textSecondary, fontWeight: 700, textAlign: "right" }}>Quantity (kg/m³)</th>
                        <th style={{ padding: "8px 12px", color: tokens.textSecondary, fontWeight: 700, textAlign: "right" }}>SG</th>
                        <th style={{ padding: "8px 12px", color: tokens.textSecondary, fontWeight: 700, textAlign: "right" }}>Volume (m³)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedCandidate.constituents.map((c, idx) => (
                        <tr key={idx} style={{ borderBottom: idx < selectedCandidate.constituents.length - 1 ? `1px solid ${tokens.borderLight}` : "none" }}>
                          <td style={{ padding: "8px 12px", fontWeight: 600, color: tokens.textPrimary }}>{c.material_name}</td>
                          <td style={{ padding: "8px 12px", color: tokens.textMuted, fontFamily: tokens.fontMono }}>{c.category_code}</td>
                          <td style={{ padding: "8px 12px", fontWeight: 700, textAlign: "right", color: tokens.textPrimary }}>{c.quantity_kg_m3.toFixed(1)}</td>
                          <td style={{ padding: "8px 12px", textAlign: "right", color: tokens.textSecondary }}>{c.specific_gravity.toFixed(2)}</td>
                          <td style={{ padding: "8px 12px", textAlign: "right", fontFamily: tokens.fontMono, color: tokens.textPrimary }}>{c.absolute_volume_m3.toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Engineering Constraint Diagnostics */}
              <div data-tour="optimization-diagnostics">
                <h4 style={{ margin: "0 0 8px 0", fontSize: "0.82rem", fontWeight: 700, color: tokens.textPrimary }}>
                  IS 456 & IS 10262 Constraint Evaluation Diagnostics
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "8px" }}>
                  {selectedCandidate.constraint_diagnostics.map((diag, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: "8px 12px",
                        borderRadius: tokens.radius,
                        backgroundColor: diag.status === "PASSED" ? tokens.surfaceSecondary : tokens.dangerRedLight,
                        border: `1px solid ${diag.status === "PASSED" ? tokens.border : "rgba(220, 38, 38, 0.3)"}`,
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <div>
                        <div style={{ fontSize: "0.75rem", fontWeight: 700, color: tokens.textPrimary }}>{diag.constraint_name}</div>
                        <div style={{ fontSize: "0.68rem", color: tokens.textMuted }}>{diag.standard_reference}</div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: "0.75rem", fontWeight: 800, color: diag.status === "PASSED" ? tokens.successGreen : tokens.dangerRed }}>
                          {diag.actual_value} {diag.unit}
                        </div>
                        <div style={{ fontSize: "0.68rem", color: tokens.textMuted }}>
                          Limit: {diag.comparison === "MINIMUM" ? "≥ " : "≤ "}{diag.limit_value} {diag.unit}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Phase 5C & 5D: Recipe Impact & Cost Comparison */}
              <div data-tour="optimization-impact-comparison" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <RecipeImpactComparison
                  runId={evaluationResult?.run_id || latestRun?.run_id || ""}
                  candidateId={selectedCandidate.id}
                  candidateIdentifier={selectedCandidate.candidate_identifier}
                />

                <CostImpactComparison
                  runId={evaluationResult?.run_id || latestRun?.run_id || ""}
                  candidateId={selectedCandidate.id}
                  candidateIdentifier={selectedCandidate.candidate_identifier}
                />
              </div>

              {/* Phase 5E: Recommendation Governance & Human Review Gate */}
              <div data-tour="optimization-governance-gate">
                <RecommendationGovernanceGate
                  runId={evaluationResult?.run_id || latestRun?.run_id || ""}
                  selectedCandidateId={selectedCandidate.id}
                  candidateIdentifier={selectedCandidate.candidate_identifier}
                />
              </div>
            </div>
          )}
        </div>
      ) : latestRun ? (
        <div
          style={{
            padding: "clamp(24px, 4vw, 32px)",
            border: `2px dashed ${tokens.border}`,
            borderRadius: tokens.radiusLarge,
            backgroundColor: tokens.surfaceSecondary,
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <div
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "50%",
              backgroundColor: tokens.primaryAccentLight,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: tokens.primaryAccent,
            }}
          >
            <Award size={22} />
          </div>
          <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: tokens.textPrimary }}>
            Optimization Run Context Created — Awaiting Candidate Evaluation
          </h3>
          <p style={{ margin: 0, fontSize: "0.82rem", color: tokens.textMuted, maxWidth: "520px", lineHeight: 1.4 }}>
            The immutable baseline for <strong style={{ color: tokens.textPrimary }}>{latestRun.recipe_code}</strong> has been snapshotted. Click below to execute the candidate generator and render the Pareto frontier.
          </p>
          <button
            onClick={() => evaluateRun(latestRun.run_id)}
            disabled={isEvaluating}
            style={{
              marginTop: "6px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "8px 18px",
              borderRadius: tokens.radius,
              backgroundColor: tokens.primaryAccent,
              color: "#FFFFFF",
              fontSize: "0.82rem",
              fontWeight: 700,
              border: "none",
              cursor: isEvaluating ? "not-allowed" : "pointer",
            }}
          >
            {isEvaluating ? <RefreshCw size={14} className="animate-spin" /> : <Zap size={14} />}
            {isEvaluating ? "Evaluating Candidate Solver..." : "Evaluate Candidate Mixes"}
          </button>
        </div>
      ) : (
        <div
          style={{
            padding: "clamp(24px, 5vw, 36px) 20px",
            border: `2px dashed ${tokens.border}`,
            borderRadius: tokens.radiusLarge,
            backgroundColor: tokens.surfaceSecondary,
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <div
            style={{
              width: "42px",
              height: "42px",
              borderRadius: "50%",
              backgroundColor: "#E2E8F0",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: tokens.textMuted,
              marginBottom: "4px",
            }}
          >
            <Sparkles size={20} />
          </div>
          <h3 style={{ margin: 0, fontSize: "0.92rem", fontWeight: 600, color: tokens.textPrimary }}>
            No Optimization Run Context Found
          </h3>
          <p style={{ margin: 0, fontSize: "0.82rem", color: tokens.textMuted, maxWidth: "460px", lineHeight: 1.4 }}>
            Select a target master mix design above and click <strong style={{ color: tokens.textPrimary }}>"Run AI Optimization"</strong> to generate a governed baseline run context snapshot.
          </p>
        </div>
      )}
    </div>
  );
};
