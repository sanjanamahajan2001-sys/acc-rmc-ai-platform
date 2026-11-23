import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  X,
} from "lucide-react";
import { StrengthCylinderIcon, BatchPlantIcon } from "../components/icons";
import { AppShell } from "../components/AppShell";
import { enterpriseLightTokens as tokens } from "../components/manual-entry/enterpriseLightTokens";
import * as reportingService from "../services/reportingService";
import {
  OperationalMetricsDTO,
  FilterOptionsDTO,
  StrengthDistributionDTO,
  MixPerformanceListDTO,
  StrengthTimelineListDTO,
  MaterialConsumptionSummaryDTO,
  BatchVarianceAnalysisDTO,
  BinderEfficiencyDTO,
  PredictionSummaryDTO,
  ActualVsPredictedResponseDTO,
  PredictionErrorTrendResponseDTO,
  ModelFeatureImportanceResponseDTO,
  ModelRegistryListDTO,
} from "../services/reportingService";
import { ModelMonitoringSection } from "../components/dashboard/model_monitoring/ModelMonitoringSection";
import { MixOptimizationSection } from "../components/dashboard/optimization/MixOptimizationSection";
import { useDashboardEventStream } from "../hooks/useDashboardEventStream";
import { LiveSyncIndicator } from "../components/dashboard/LiveSyncIndicator";
import { DashboardFilterBar } from "../components/dashboard/DashboardFilterBar";
import { ExecutiveDashboardSummaryDTO } from "../services/reportingService";
import { ExecutiveDashboardSummary } from "../components/dashboard/ExecutiveDashboardSummary";
import { DashboardExportControl } from "../components/dashboard/DashboardExportControl";
import { ExecutiveKPICards } from "../components/dashboard/ExecutiveKPICards";
import { StatisticalSummaryCards } from "../components/dashboard/sqc/StatisticalSummaryCards";
import { StrengthDistributionChart } from "../components/dashboard/sqc/StrengthDistributionChart";
import { MixPerformanceMatrix } from "../components/dashboard/sqc/MixPerformanceMatrix";
import { StrengthTrendTimeline } from "../components/dashboard/sqc/StrengthTrendTimeline";
import { MaterialSummaryCards } from "../components/dashboard/materials/MaterialSummaryCards";
import { MaterialConsumptionMatrix } from "../components/dashboard/materials/MaterialConsumptionMatrix";
import { BatchWeighingVarianceChart } from "../components/dashboard/materials/BatchWeighingVarianceChart";
import { WaterCementRatioChart } from "../components/dashboard/materials/WaterCementRatioChart";
import { BinderIntensityMatrix } from "../components/dashboard/materials/BinderIntensityMatrix";
import { apiClient } from "../services/apiClient";

export const OperationsDashboardPage: React.FC = () => {
  const navigate = useNavigate();

  // Filters State
  const [selectedPlant, setSelectedPlant] = useState<string>("");
  const [selectedRecipe, setSelectedRecipe] = useState<string>("");
  const [activeOptimizationRunId, setActiveOptimizationRunId] = useState<string | null>(null);
  const [activeCandidateId, setActiveCandidateId] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  // Data State - Phase 1 & 2
  const [filterOptions, setFilterOptions] = useState<FilterOptionsDTO | null>(null);
    const [executiveSummary, setExecutiveSummary] = useState<ExecutiveDashboardSummaryDTO | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState<boolean>(false);
  const [metrics, setMetrics] = useState<OperationalMetricsDTO | null>(null);
  const [distribution, setDistribution] = useState<StrengthDistributionDTO | null>(null);
  const [mixPerformance, setMixPerformance] = useState<MixPerformanceListDTO | null>(null);
  const [timeline, setTimeline] = useState<StrengthTimelineListDTO | null>(null);

  // Data State - Phase 3 (Materials, Variance & Efficiency)
  const [materialConsumption, setMaterialConsumption] = useState<MaterialConsumptionSummaryDTO | null>(null);
  const [batchVariance, setBatchVariance] = useState<BatchVarianceAnalysisDTO | null>(null);
  const [binderEfficiency, setBinderEfficiency] = useState<BinderEfficiencyDTO | null>(null);

  // Data State - Phase 4 (Strength Prediction & Model Monitoring)
  const [predictionSummary, setPredictionSummary] = useState<PredictionSummaryDTO | null>(null);
  const [actualVsPredicted, setActualVsPredicted] = useState<ActualVsPredictedResponseDTO | null>(null);
  const [predictionErrorTrend, setPredictionErrorTrend] = useState<PredictionErrorTrendResponseDTO | null>(null);
  const [featureImportance, setFeatureImportance] = useState<ModelFeatureImportanceResponseDTO | null>(null);
  const [modelRegistry, setModelRegistry] = useState<ModelRegistryListDTO | null>(null);
  const [backtestData, setBacktestData] = useState<ActualVsPredictedResponseDTO | null>(null);

  // Loading & Error States
  const [isLoadingMetrics, setIsLoadingMetrics] = useState<boolean>(true);
  const [isLoadingSQC, setIsLoadingSQC] = useState<boolean>(true);
  const [isLoadingMaterials, setIsLoadingMaterials] = useState<boolean>(true);
  const [isLoadingModelMonitoring, setIsLoadingModelMonitoring] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Ingestion Reset Modal State
  const [isResetModalOpen, setIsResetModalOpen] = useState(false);
  const [resetConfirmed, setResetConfirmed] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);
  const [resetReport, setResetReport] = useState<any | null>(null);

  // Load Filter Options Once
  useEffect(() => {
    reportingService
      .fetchFilterOptions()
      .then((data: FilterOptionsDTO) => setFilterOptions(data))
      .catch((err: any) => console.error("Failed to load filter options", err));
  }, []);

  // Fetch Authoritative Dashboard Metrics, SQC, and Material Consumption Data
  const loadDashboardData = useCallback(async () => {
    try {
            setIsLoadingSummary(true);
      try {
        const sumRes = await reportingService.fetchExecutiveDashboardSummary({
          plant_code: selectedPlant || undefined,
          recipe_code: selectedRecipe || undefined,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
          run_id: activeOptimizationRunId || undefined,
          candidate_id: activeCandidateId || undefined,
        });
        setExecutiveSummary(sumRes);
      } catch (sumErr) {
        console.warn("Could not fetch executive summary:", sumErr);
      } finally {
        setIsLoadingSummary(false);
      }
      setIsLoadingMetrics(true);
      setIsLoadingSQC(true);
      setIsLoadingMaterials(true);
      setIsLoadingModelMonitoring(true);
      setError(null);

      const params = {
        plant_code: selectedPlant || undefined,
        recipe_code: selectedRecipe || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      };

      const [
        metricsRes,
        distRes,
        mixRes,
        timeRes,
        matRes,
        varRes,
        effRes,
        predSummRes,
        actPredRes,
        errTrendRes,
        featImpRes,
        registryRes,
        backtestRes,
      ] = await Promise.all([
        reportingService.fetchOperationalMetrics(params),
        reportingService.fetchStrengthDistribution(params),
        reportingService.fetchMixPerformance(params),
        reportingService.fetchStrengthTimeline({ ...params, limit: 50 }),
        reportingService.fetchMaterialConsumption(params),
        reportingService.fetchBatchVariance(params),
        reportingService.fetchBinderEfficiency(params),
        reportingService.fetchPredictionSummary(params),
        reportingService.fetchActualVsPredicted({ ...params, limit: 500 }),
        reportingService.fetchPredictionErrorTrend({ ...params, limit: 500, rolling_window: 10 }),
        reportingService.fetchModelFeatures(),
        reportingService.fetchModelMetadata(),
        reportingService.fetchModelBacktest({ ...params, limit: 500 }),
      ]);

      setMetrics(metricsRes);
      setDistribution(distRes);
      setMixPerformance(mixRes);
      setTimeline(timeRes);
      setMaterialConsumption(matRes);
      setBatchVariance(varRes);
      setBinderEfficiency(effRes);
      setPredictionSummary(predSummRes);
      setActualVsPredicted(actPredRes);
      setPredictionErrorTrend(errTrendRes);
      setFeatureImportance(featImpRes);
      setModelRegistry(registryRes);
      setBacktestData(backtestRes);
    } catch (err: any) {
      console.error("Dashboard data load error:", err);
      setError(err?.response?.data?.detail || "Failed to load authoritative dashboard metrics.");
    } finally {
      setIsLoadingMetrics(false);
      setIsLoadingSQC(false);
      setIsLoadingMaterials(false);
      setIsLoadingModelMonitoring(false);
    }
  }, [selectedPlant, selectedRecipe, dateFrom, dateTo]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Refresh executive summary reactively whenever active optimization run or candidate changes
  useEffect(() => {
    const refreshSummary = async () => {
      try {
        const sumRes = await reportingService.fetchExecutiveDashboardSummary({
          plant_code: selectedPlant || undefined,
          recipe_code: selectedRecipe || undefined,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
          run_id: activeOptimizationRunId || undefined,
          candidate_id: activeCandidateId || undefined,
        });
        setExecutiveSummary(sumRes);
      } catch (sumErr) {
        console.warn("Failed to reactively update executive summary:", sumErr);
      }
    };
    refreshSummary();
  }, [activeOptimizationRunId, activeCandidateId, selectedPlant, selectedRecipe, dateFrom, dateTo]);

  const handleEventInvalidate = useCallback(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Real-time Event-Driven Invalidation Hook
  const { syncStatus } = useDashboardEventStream(handleEventInvalidate);

  const handleResetFilters = () => {
    setSelectedPlant("");
    setSelectedRecipe("");
    setDateFrom("");
    setDateTo("");
  };

  const handleExecuteReset = async () => {
    setIsResetting(true);
    setResetError(null);
    try {
      const resp = await apiClient.post<any>("/ingestion/reset", {
        confirm: true,
        confirm_danger: true,
        reason: "User requested safe ingestion reset from Operations Dashboard",
      });
      setResetReport(resp);
      await loadDashboardData();
    } catch (err: any) {
      setResetError(err.response?.data?.detail || "Failed to reset database ingestion data");
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <AppShell>
      <div className="dashboard-page-container">
        {/* Top Header */}
        <div className="dashboard-header-bar">
          <div>
            <h1
              style={{
                margin: "0 0 4px 0",
                fontSize: "1.45rem",
                fontWeight: 700,
                color: tokens.textPrimary,
                letterSpacing: "-0.01em",
              }}
            >
              Operations & Quality Control Center
            </h1>
            <p
              style={{
                margin: 0,
                fontSize: "0.82rem",
                color: tokens.textMuted,
              }}
            >
              Authoritative real-time production telemetry, mix quality compliance & batch execution metrics
            </p>
          </div>

          <div className="dashboard-header-actions" data-tour="dashboard-export-controls">
            <DashboardExportControl
              plantCode={selectedPlant}
              recipeCode={selectedRecipe}
              dateFrom={dateFrom}
              dateTo={dateTo}
              runId={activeOptimizationRunId || undefined}
              candidateId={activeCandidateId || undefined}
            />
            <LiveSyncIndicator status={syncStatus} />
            <button
              type="button"
              onClick={() => setIsResetModalOpen(true)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 14px",
                backgroundColor: tokens.surfacePrimary,
                color: tokens.statusErrorText,
                border: `1px solid ${tokens.statusErrorBorder}`,
                borderRadius: "6px",
                fontSize: "0.78rem",
                fontWeight: 600,
                cursor: "pointer",
                boxShadow: "0 1px 2px 0 rgba(0,0,0,0.02)",
              }}
            >
              <RotateCcw size={14} />
              <span>Reset Ingestion Data</span>
            </button>
          </div>
        </div>

        {/* Filter Bar */}
        <div data-tour="dashboard-filters">
        <DashboardFilterBar
          filterOptions={filterOptions}
          selectedPlant={selectedPlant}
          selectedRecipe={selectedRecipe}
          dateFrom={dateFrom}
          dateTo={dateTo}
          onPlantChange={setSelectedPlant}
          onRecipeChange={setSelectedRecipe}
          onDateFromChange={setDateFrom}
          onDateToChange={setDateTo}
          onResetFilters={handleResetFilters}
          isLoading={isLoadingMetrics || isLoadingSQC || isLoadingMaterials || isLoadingModelMonitoring}
        />
        </div>

        {/* Error Alert */}
        {error && (
          <div
            style={{
              padding: "12px 16px",
              backgroundColor: tokens.statusErrorBg,
              border: `1px solid ${tokens.statusErrorBorder}`,
              borderRadius: "8px",
              color: tokens.statusErrorText,
              fontSize: "0.82rem",
              marginBottom: "20px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Executive Dashboard Summary (4 Factual Groups) */}
        <div data-tour="dashboard-summary-cards">
        <ExecutiveDashboardSummary
          summary={executiveSummary}
          loading={isLoadingSummary}
        />
        </div>

        {/* Phase 1: Executive KPI Cards */}
        <div data-tour="dashboard-kpis">
        <ExecutiveKPICards
          metrics={metrics || undefined}
          isLoading={isLoadingMetrics}
          isError={Boolean(error)}
        />
        </div>

        {/* Phase 2: Statistical Quality Control Section */}
        <div data-tour="dashboard-sqc-section" style={{ marginBottom: "32px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "14px",
              paddingBottom: "8px",
              borderBottom: `1px solid ${tokens.borderLight}`,
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <StrengthCylinderIcon size={20} />
              <h2
                style={{
                  margin: 0,
                  fontSize: "1.05rem",
                  fontWeight: 700,
                  color: tokens.textPrimary,
                  letterSpacing: "-0.01em",
                }}
              >
                Statistical Quality Control (28-Day Strength)
              </h2>
            </div>
            <span style={{ fontSize: "0.72rem", color: tokens.textMuted }}>
              IS 456 / IS 10262 Certified Quality Standard
            </span>
          </div>

          {/* Statistical Summary Cards */}
          <StatisticalSummaryCards data={distribution} isLoading={isLoadingSQC} />

          {/* Two-Column Chart & Timeline Layout */}
          <div className="dashboard-sqc-charts-grid">
            <StrengthDistributionChart data={distribution} isLoading={isLoadingSQC} />
            <StrengthTrendTimeline data={timeline} isLoading={isLoadingSQC} />
          </div>

          {/* Mix Performance Table (Paginated) */}
          <MixPerformanceMatrix data={mixPerformance} isLoading={isLoadingSQC} />
        </div>

        {/* Phase 3: Material Consumption & Batching Control Section */}
        <div data-tour="dashboard-materials-section" style={{ marginBottom: "32px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "14px",
              paddingBottom: "8px",
              borderBottom: `1px solid ${tokens.borderLight}`,
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <BatchPlantIcon size={20} />
              <h2
                style={{
                  margin: 0,
                  fontSize: "1.05rem",
                  fontWeight: 700,
                  color: tokens.textPrimary,
                  letterSpacing: "-0.01em",
                }}
              >
                Material Consumption & Batching Control
              </h2>
            </div>
            <span style={{ fontSize: "0.72rem", color: tokens.textMuted }}>
              IS 4926:2003 Annex E Weighing Accuracy, Material Intensity & W/B Efficiency
            </span>
          </div>

          {/* Material Summary Cards */}
          <MaterialSummaryCards data={materialConsumption} isLoading={isLoadingMaterials} />

          {/* Dual Column: Annex E Weighing Variance & Water / W/B Monitoring */}
          <div className="dashboard-materials-dual-grid">
            <BatchWeighingVarianceChart data={batchVariance} isLoading={isLoadingMaterials} />
            <WaterCementRatioChart
              varianceData={batchVariance}
              efficiencyData={binderEfficiency}
              isLoading={isLoadingMaterials}
            />
          </div>

          {/* Material Consumption & Specific Density Matrix */}
          <MaterialConsumptionMatrix data={materialConsumption} isLoading={isLoadingMaterials} />

          {/* Binder Intensity & Material Efficiency Matrix */}
          <BinderIntensityMatrix data={binderEfficiency} isLoading={isLoadingMaterials} />
        </div>

        {/* Phase 4: Strength Prediction Validation & Model Monitoring Section */}
        <div data-tour="dashboard-model-monitoring">
        <ModelMonitoringSection
          predictionSummary={predictionSummary}
          actualVsPredicted={actualVsPredicted}
          predictionErrorTrend={predictionErrorTrend}
          featureImportance={featureImportance}
          modelRegistry={modelRegistry}
          backtestData={backtestData}
          isLoading={isLoadingModelMonitoring}
        />
        </div>

        {/* Phase 5A: AI Mix Optimization Workspace */}
        <div data-tour="dashboard-optimization-workspace">
        <MixOptimizationSection
          selectedPlant={selectedPlant}
          onActiveRunChange={setActiveOptimizationRunId}
          onActiveCandidateChange={setActiveCandidateId}
        />
        </div>

        {/* Reset Confirmation Modal */}
        {isResetModalOpen && (
          <div
            style={{
              position: "fixed",
              inset: 0,
              backgroundColor: "rgba(15, 23, 42, 0.45)",
              backdropFilter: "blur(4px)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 50,
              padding: "16px",
            }}
          >
            <div
              style={{
                backgroundColor: "#FFFFFF",
                borderRadius: "12px",
                border: `1px solid ${tokens.border}`,
                boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)",
                maxWidth: "480px",
                width: "100%",
                padding: "24px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div
                    style={{
                      padding: "8px",
                      backgroundColor: tokens.statusErrorBg,
                      borderRadius: "8px",
                      color: tokens.statusErrorText,
                    }}
                  >
                    <AlertTriangle size={20} />
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: tokens.textPrimary }}>
                      Reset Ingestion Data
                    </h3>
                    <p style={{ margin: 0, fontSize: "0.78rem", color: tokens.textSecondary }}>
                      Safe non-destructive administrative test cleanup
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setIsResetModalOpen(false);
                    setResetReport(null);
                    setResetError(null);
                    setResetConfirmed(false);
                  }}
                  style={{ background: "none", border: "none", cursor: "pointer", color: tokens.textMuted }}
                >
                  <X size={18} />
                </button>
              </div>

              {resetReport ? (
                <div style={{ marginBottom: "20px" }}>
                  <div
                    style={{
                      padding: "14px",
                      backgroundColor: tokens.statusSuccessBg,
                      border: `1px solid ${tokens.statusSuccessBorder}`,
                      borderRadius: "8px",
                      marginBottom: "16px",
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "10px",
                    }}
                  >
                    <CheckCircle2 size={18} color={tokens.statusSuccessText} style={{ marginTop: "2px" }} />
                    <div style={{ fontSize: "0.82rem", color: tokens.statusSuccessText }}>
                      <div style={{ fontWeight: 600 }}>Reset Completed Successfully</div>
                      <div>{(resetReport?.rows_deleted_per_table?.prd_batches ?? resetReport?.detail?.deleted_batches_count) || 0} batches cleared.</div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setIsResetModalOpen(false);
                      setResetReport(null);
                      setResetConfirmed(false);
                    }}
                    style={{
                      width: "100%",
                      padding: "10px",
                      backgroundColor: tokens.primaryAccent,
                      color: "#FFFFFF",
                      border: "none",
                      borderRadius: "6px",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Close & Return to Dashboard
                  </button>
                </div>
              ) : (
                <div>
                  <p style={{ fontSize: "0.82rem", color: tokens.textSecondary, lineHeight: 1.5, marginBottom: "16px" }}>
                    This action will purge uploaded batches, cube test results, and raw staging data. Master plant and mix recipe definitions are strictly preserved.
                  </p>

                  <label
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      fontSize: "0.8rem",
                      color: tokens.textPrimary,
                      marginBottom: "20px",
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={resetConfirmed}
                      onChange={(e) => setResetConfirmed(e.target.checked)}
                    />
                    <span>I understand this purges staging and test ingestion data.</span>
                  </label>

                  {resetError && (
                    <div
                      style={{
                        padding: "10px 12px",
                        backgroundColor: tokens.statusErrorBg,
                        border: `1px solid ${tokens.statusErrorBorder}`,
                        borderRadius: "6px",
                        color: tokens.statusErrorText,
                        fontSize: "0.78rem",
                        marginBottom: "16px",
                      }}
                    >
                      {resetError}
                    </div>
                  )}

                  <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                    <button
                      type="button"
                      onClick={() => setIsResetModalOpen(false)}
                      disabled={isResetting}
                      style={{
                        padding: "8px 14px",
                        backgroundColor: tokens.surfacePrimary,
                        border: `1px solid ${tokens.border}`,
                        borderRadius: "6px",
                        fontSize: "0.8rem",
                        color: tokens.textSecondary,
                        cursor: "pointer",
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleExecuteReset}
                      disabled={!resetConfirmed || isResetting}
                      style={{
                        padding: "8px 16px",
                        backgroundColor: resetConfirmed ? tokens.statusErrorText : tokens.border,
                        color: "#FFFFFF",
                        border: "none",
                        borderRadius: "6px",
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        cursor: resetConfirmed && !isResetting ? "pointer" : "not-allowed",
                      }}
                    >
                      {isResetting ? "Resetting Data..." : "Confirm & Execute Reset"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
};
