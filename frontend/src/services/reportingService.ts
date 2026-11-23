import { apiClient, getAuthToken, resolveBaseUrl } from "./apiClient";

export interface ScopeMetadataDTO {
  plant_code?: string | null;
  recipe_code?: string | null;
  date_from?: string | null;
  date_to?: string | null;
  cache_token_version: number;
  generated_at: string;
}

export interface OperationalMetricsDTO {
  active_plants_count: number;
  total_ingested_batches: number;
  operational_batches_count: number;
  historical_qc_batches_count: number;
  forecast_design_batches_count: number;
  quality_compliance_rate_pct: number;
  total_cube_tests: number;
  total_volume_m3: number;
  material_consumptions_count: number;
  scope_metadata?: ScopeMetadataDTO | null;
}

export interface PlantOptionDTO {
  plant_code: string;
  plant_name: string;
  location?: string | null;
}

export interface RecipeOptionDTO {
  recipe_code: string;
  recipe_name: string;
  grade?: string | null;
  target_strength_mpa?: number | null;
}

export interface FilterOptionsDTO {
  plants: PlantOptionDTO[];
  recipes: RecipeOptionDTO[];
  available_date_range: {
    earliest_date?: string | null;
    latest_date?: string | null;
  };
}

export interface HistogramBinDTO {
  bin_start: number;
  bin_end: number;
  bin_label: string;
  count: number;
  is_below_fck: boolean;
}

export interface StrengthDistributionDTO {
  total_tested_batches: number;
  total_tested_specimens: number;
  mean_strength_mpa?: number | null;
  median_strength_mpa?: number | null;
  standard_deviation_mpa?: number | null;
  coefficient_of_variation_pct?: number | null;
  min_strength_mpa?: number | null;
  max_strength_mpa?: number | null;
  characteristic_strength_fck_mpa?: number | null;
  target_mean_strength_fck_prime_mpa?: number | null;
  strength_margin_mpa?: number | null;
  compliance_rate_pct: number;
  stability_grade: "EXCELLENT" | "MODERATE" | "HIGH_VARIATION" | "INSUFFICIENT_DATA" | string;
  histogram_bins: HistogramBinDTO[];
  scope_metadata: ScopeMetadataDTO;
}

export interface MixPerformanceItemDTO {
  recipe_code: string;
  recipe_name: string;
  grade: string;
  target_strength_fck: number;
  target_mean_strength_fck_prime: number;
  total_batches: number;
  tested_batches_28d: number;
  tested_specimens_28d: number;
  mean_strength_mpa?: number | null;
  standard_deviation_mpa?: number | null;
  coefficient_of_variation_pct?: number | null;
  strength_margin_mpa?: number | null;
  compliance_rate_pct: number;
  stability_status: string;
}

export interface MixPerformanceListDTO {
  items: MixPerformanceItemDTO[];
  total_recipes_evaluated: number;
  scope_metadata: ScopeMetadataDTO;
}

export interface StrengthTimelinePointDTO {
  batch_number: string;
  plant_code: string;
  recipe_code: string;
  grade: string;
  production_timestamp: string;
  result_7d_mpa?: number | null;
  result_28d_mpa?: number | null;
  target_fck_mpa: number;
  target_fck_prime_mpa: number;
  is_compliant_28d?: boolean | null;
}

export interface StrengthTimelineListDTO {
  timeline: StrengthTimelinePointDTO[];
  total_points: number;
  scope_metadata: ScopeMetadataDTO;
}

// =========================================================================
// PHASE 3: MATERIAL CONSUMPTION, BATCH VARIANCE & BINDER INTENSITY DTOs
// =========================================================================

export interface StandardReferenceDTO {
  standard: string;
  section: string;
  metric: string;
  tolerance_pct?: number | null;
  tolerance_scope: string;
}

export interface MaterialScopeMetadataDTO {
  plant_code?: string | null;
  recipe_code?: string | null;
  date_from?: string | null;
  date_to?: string | null;
  cache_token_version: number;
  generated_at: string;
}

export interface MaterialConsumptionItemDTO {
  material_code: string;
  material_name: string;
  category: string;
  broad_category: string;
  record_count: number;
  batch_count: number;
  planned_quantity_kg: number;
  actual_quantity_kg: number;
  variance_quantity_kg: number;
  variance_percentage: number;
  avg_consumption_per_batch_kg: number;
  consumption_kg_per_m3: number;
  engineering_unit: string;
}

export interface MaterialConsumptionSummaryDTO {
  items: MaterialConsumptionItemDTO[];
  total_batches: number;
  total_produced_batches: number;
  total_scheduled_batches: number;
  material_consumption_batch_count: number;
  total_volume_m3: number;
  total_planned_material_kg: number;
  total_actual_material_kg: number;
  total_variance_kg: number;
  overall_variance_percentage: number;
  total_binder_consumption_kg: number;
  total_water_consumption_kg: number;
  total_aggregate_consumption_kg: number;
  total_admixture_consumption_kg: number;
  scope_metadata: MaterialScopeMetadataDTO;
}

export interface MaterialVarianceDetailDTO {
  material_code: string;
  material_name: string;
  compliance_status: "CLASSIFIABLE" | "NOT_CLASSIFIABLE" | string;
  is4926_tolerance_pct?: number | null;
  standard_reference?: StandardReferenceDTO | null;
  record_count: number;
  compliant_count: number;
  non_compliant_count: number;
  compliance_rate_pct?: number | null;
  planned_quantity_kg: number;
  actual_quantity_kg: number;
  variance_quantity_kg: number;
  mean_variance_pct: number;
  mean_abs_variance_pct: number;
  max_abs_variance_pct: number;
}

export interface CategoryVarianceItemDTO {
  category_code: string;
  category_name: string;
  compliance_status: "CLASSIFIABLE" | "NOT_CLASSIFIABLE" | string;
  is4926_tolerance_pct?: number | null;
  standard_reference?: StandardReferenceDTO | null;
  record_count: number;
  compliant_count: number;
  non_compliant_count: number;
  compliance_rate_pct?: number | null;
  planned_total_kg: number;
  actual_total_kg: number;
  variance_total_kg: number;
  mean_variance_pct: number;
  mean_abs_variance_pct: number;
  max_abs_variance_pct: number;
  materials: MaterialVarianceDetailDTO[];
}

export interface WaterMoistureAnalysisDTO {
  planned_water_kg: number;
  actual_water_kg: number;
  raw_water_variance_kg: number;
  raw_water_variance_pct: number;
  moisture_probe_records_count: number;
  total_water_records_count: number;
  data_quality_status: "LIMITED" | "COMPLETE" | string;
  operational_note: string;
}

export interface OverallVarianceSummaryDTO {
  indicator_name: string;
  total_weighments: number;
  classifiable_weighments: number;
  compliant_weighments: number;
  non_compliant_weighments: number;
  annex_e_compliance_rate_pct: number;
  mean_abs_variance_pct: number;
  annex_e_weighment_batch_count: number;
  unclassified_record_count: number;
  unclassified_material_codes: string[];
  standard_applied: string;
}

export interface BatchVarianceAnalysisDTO {
  categories: CategoryVarianceItemDTO[];
  overall_summary: OverallVarianceSummaryDTO;
  water_moisture_analysis: WaterMoistureAnalysisDTO;
  scope_metadata: MaterialScopeMetadataDTO;
}

export interface RecipeBinderIntensityDTO {
  recipe_code: string;
  grade: string;
  target_strength_fck_mpa: number;
  total_batches: number;
  tested_batches_28d: number;
  tested_specimens_28d: number;
  cement_content_kg_m3?: number | null;
  total_binder_content_kg_m3?: number | null;
  water_content_kg_m3?: number | null;
  actual_wb_ratio?: number | null;
  planned_wb_ratio?: number | null;
  actual_wc_ratio?: number | null;
  mean_28d_strength_mpa?: number | null;
  min_28d_strength_mpa?: number | null;
  max_28d_strength_mpa?: number | null;
  binder_intensity_index_kg_m3_per_mpa?: number | null;
  cement_intensity_index_kg_m3_per_mpa?: number | null;
  is_statistically_reliable: boolean;
  sample_size_status: "RELIABLE" | "LIMITED" | "VERY_LOW" | "NO_TESTS" | string;
}

export interface FleetBinderEfficiencySummaryDTO {
  total_evaluated_recipes: number;
  total_production_batches: number;
  total_tested_batches_28d: number;
  tested_28d_batch_count: number;
  fleet_avg_cement_kg_m3?: number | null;
  fleet_avg_binder_kg_m3?: number | null;
  fleet_avg_actual_wb?: number | null;
  fleet_avg_actual_wc?: number | null;
  fleet_avg_28d_strength_mpa?: number | null;
  fleet_avg_binder_intensity?: number | null;
}

export interface BinderEfficiencyDTO {
  recipes: RecipeBinderIntensityDTO[];
  fleet_summary: FleetBinderEfficiencySummaryDTO;
  scope_metadata: MaterialScopeMetadataDTO;
}


// =========================================================================
// PHASE 4: MODEL MONITORING & STRENGTH PREDICTION VALIDATION DTOs
// =========================================================================

export interface ModelMetadataItemDTO {
  model_registry_id: string;
  model_name: string;
  model_version: string;
  framework: string;
  algorithm: string;
  feature_schema_version: string;
  training_dataset_version?: string | null;
  deployment_status: string;
  deployment_timestamp: string;
  is_active: boolean;
  artifact_location?: string | null;
  checksum?: string | null;
}

export interface ModelRegistryListDTO {
  models: ModelMetadataItemDTO[];
  total_models: number;
  active_model_version?: string | null;
}

export interface StatisticalMetricsDTO {
  sample_count: number;
  mae_mpa?: number | null;
  mse_mpa2?: number | null;
  rmse_mpa?: number | null;
  r2_score?: number | null;
  mean_residual_mpa?: number | null;
  residual_std_dev_mpa?: number | null;
  min_residual_mpa?: number | null;
  max_residual_mpa?: number | null;
  mean_actual_strength_mpa?: number | null;
  mean_predicted_strength_mpa?: number | null;
}

export interface PredictionSourceBreakdownDTO {
  total_evaluated: number;
  model_predictions_count: number;
  fallback_predictions_count: number;
  fallback_breakdown: Record<string, number>;
}

export interface ModelMonitoringScopeDTO {
  evaluation_type: "PRODUCTION_STORED" | "RETROSPECTIVE_BACKTEST" | string;
  plant_code?: string | null;
  recipe_code?: string | null;
  date_from?: string | null;
  date_to?: string | null;
  date_filter_applied_to: string;
  model_version?: string | null;
  status: string;
  disclaimer?: string | null;
  eligible_count: number;
  total_predictions_count?: number | null;
  model_predictions_count?: number | null;
  fallback_predictions_count?: number | null;
  excluded_records_count: number;
  cache_token_version: number;
  generated_at: string;
}

export interface PredictionSummaryDTO {
  scope: ModelMonitoringScopeDTO;
  metrics: StatisticalMetricsDTO;
  active_model?: ModelMetadataItemDTO | null;
  selected_model?: ModelMetadataItemDTO | null;
  disaggregated_summary?: PredictionSourceBreakdownDTO | null;
  fallback_metrics?: StatisticalMetricsDTO | null;
}

export interface ActualVsPredictedItemDTO {
  batch_id: string;
  batch_number: string;
  plant_code: string;
  recipe_code: string;
  grade?: string | null;
  production_timestamp: string;
  testing_date?: string | null;
  actual_strength_mpa: number;
  predicted_strength_mpa: number;
  residual_mpa: number;
  abs_error_mpa: number;
  model_version: string;
  prediction_source?: "ML_MODEL" | "HEURISTIC" | string;
  fallback_reason?: string | null;
}

export interface ActualVsPredictedResponseDTO {
  scope: ModelMonitoringScopeDTO;
  summary_metrics: StatisticalMetricsDTO;
  items: ActualVsPredictedItemDTO[];
  total_items: number;
}

export interface PredictionErrorTrendItemDTO {
  index: number;
  batch_id: string;
  batch_number: string;
  production_timestamp: string;
  actual_strength_mpa: number;
  predicted_strength_mpa: number;
  residual_mpa: number;
  abs_error_mpa: number;
  rolling_mae_mpa?: number | null;
}

export interface PredictionErrorTrendResponseDTO {
  scope: ModelMonitoringScopeDTO;
  items: PredictionErrorTrendItemDTO[];
  total_items: number;
  rolling_window_size: number;
  operational_monitoring_threshold_mpa: number;
  threshold_description: string;
}

export interface FeatureImportanceItemDTO {
  feature_name: string;
  display_name: string;
  importance_weight: number;
  raw_value?: number | null;
  unit: string;
}

export interface ModelFeatureImportanceResponseDTO {
  model_version: string;
  algorithm: string;
  feature_importance_available: boolean;
  status_code: string;
  message: string;
  features: FeatureImportanceItemDTO[];
}

export interface ModelMonitoringFilterParams extends FilterParams {
  model_version?: string;
  limit?: number;
  rolling_window?: number;
}

// =========================================================================
// FILTER PARAMS & API CALLERS
// =========================================================================

export interface FilterParams {
  plant_code?: string;
  recipe_code?: string;
  date_from?: string;
  date_to?: string;
}

const buildQueryString = (params?: FilterParams): string => {
  if (!params) return "";
  const queryParams = new URLSearchParams();
  if (params.plant_code) queryParams.append("plant_code", params.plant_code);
  if (params.recipe_code) queryParams.append("recipe_code", params.recipe_code);
  if (params.date_from) queryParams.append("date_from", params.date_from);
  if (params.date_to) queryParams.append("date_to", params.date_to);
  const qs = queryParams.toString();
  return qs ? `?${qs}` : "";
};

export const fetchOperationalMetrics = async (params?: FilterParams): Promise<OperationalMetricsDTO> => {
  return await apiClient.get<OperationalMetricsDTO>(`/reporting/operational-metrics${buildQueryString(params)}`);
};

export const fetchStrengthDistribution = async (params?: FilterParams): Promise<StrengthDistributionDTO> => {
  return await apiClient.get<StrengthDistributionDTO>(`/reporting/strength-distribution${buildQueryString(params)}`);
};

export const fetchMixPerformance = async (params?: FilterParams): Promise<MixPerformanceListDTO> => {
  return await apiClient.get<MixPerformanceListDTO>(`/reporting/mix-performance${buildQueryString(params)}`);
};

export const fetchStrengthTimeline = async (params?: FilterParams & { limit?: number }): Promise<StrengthTimelineListDTO> => {
  const qs = buildQueryString(params);
  const limitParam = params?.limit ? `${qs ? "&" : "?"}limit=${params.limit}` : "";
  return await apiClient.get<StrengthTimelineListDTO>(`/reporting/strength-timeline${qs}${limitParam}`);
};

export const fetchMaterialConsumption = async (params?: FilterParams): Promise<MaterialConsumptionSummaryDTO> => {
  return await apiClient.get<MaterialConsumptionSummaryDTO>(`/reporting/material-consumption${buildQueryString(params)}`);
};

export const fetchBatchVariance = async (params?: FilterParams): Promise<BatchVarianceAnalysisDTO> => {
  return await apiClient.get<BatchVarianceAnalysisDTO>(`/reporting/batch-variance${buildQueryString(params)}`);
};

export const fetchBinderEfficiency = async (params?: FilterParams): Promise<BinderEfficiencyDTO> => {
  return await apiClient.get<BinderEfficiencyDTO>(`/reporting/binder-efficiency${buildQueryString(params)}`);
};

export const fetchFilterOptions = async (): Promise<FilterOptionsDTO> => {
  return await apiClient.get<FilterOptionsDTO>("/reporting/filter-options");
};

export const requestSSETicket = async (): Promise<string> => {
  const res = await apiClient.post<{ ticket: string; expires_in_seconds: string }>(
    "/events/ticket"
  );
  return res.ticket;
};


export const fetchPredictionSummary = async (
  params?: ModelMonitoringFilterParams
): Promise<PredictionSummaryDTO> => {
  const qs = buildQueryString(params);
  const mvParam = params?.model_version ? `${qs ? "&" : "?"}model_version=${encodeURIComponent(params.model_version)}` : "";
  return await apiClient.get<PredictionSummaryDTO>(`/reporting/prediction-summary${qs}${mvParam}`);
};

export const fetchActualVsPredicted = async (
  params?: ModelMonitoringFilterParams
): Promise<ActualVsPredictedResponseDTO> => {
  const qs = buildQueryString(params);
  const queryParts: string[] = [];
  if (params?.model_version) queryParts.push(`model_version=${encodeURIComponent(params.model_version)}`);
  if (params?.limit) queryParts.push(`limit=${params.limit}`);
  const extra = queryParts.length > 0 ? `${qs ? "&" : "?"}${queryParts.join("&")}` : "";
  return await apiClient.get<ActualVsPredictedResponseDTO>(`/reporting/actual-vs-predicted${qs}${extra}`);
};

export const fetchPredictionErrorTrend = async (
  params?: ModelMonitoringFilterParams
): Promise<PredictionErrorTrendResponseDTO> => {
  const qs = buildQueryString(params);
  const queryParts: string[] = [];
  if (params?.model_version) queryParts.push(`model_version=${encodeURIComponent(params.model_version)}`);
  if (params?.limit) queryParts.push(`limit=${params.limit}`);
  if (params?.rolling_window) queryParts.push(`rolling_window=${params.rolling_window}`);
  const extra = queryParts.length > 0 ? `${qs ? "&" : "?"}${queryParts.join("&")}` : "";
  return await apiClient.get<PredictionErrorTrendResponseDTO>(`/reporting/prediction-error-trend${qs}${extra}`);
};

export const fetchModelFeatures = async (
  modelVersion?: string
): Promise<ModelFeatureImportanceResponseDTO> => {
  const query = modelVersion ? `?model_version=${encodeURIComponent(modelVersion)}` : "";
  return await apiClient.get<ModelFeatureImportanceResponseDTO>(`/reporting/model-features${query}`);
};

export const fetchModelMetadata = async (): Promise<ModelRegistryListDTO> => {
  return await apiClient.get<ModelRegistryListDTO>("/reporting/model-metadata");
};

export const fetchModelBacktest = async (
  params?: ModelMonitoringFilterParams
): Promise<ActualVsPredictedResponseDTO> => {
  const qs = buildQueryString(params);
  const queryParts: string[] = [];
  if (params?.model_version) queryParts.push(`model_version=${encodeURIComponent(params.model_version)}`);
  if (params?.limit) queryParts.push(`limit=${params.limit}`);
  const extra = queryParts.length > 0 ? `${qs ? "&" : "?"}${queryParts.join("&")}` : "";
  return await apiClient.get<ActualVsPredictedResponseDTO>(`/reporting/model-backtest${qs}${extra}`);
};


export interface ExecutiveDashboardSummaryDTO {
  quality_and_production: {
    grades_evaluated: number;
    total_batches_produced: number;
    total_volume_m3?: number;
    specimens_tested_28d: number;
    mean_strength_28d_mpa: number;
    quality_compliance_percent: number;
    strength_variability_sigma_mpa: number;
    strength_cov_percent: number;
    weighment_accuracy_percent: number;
  };
  strength_prediction: {
    platform_active_model: string;
    platform_model_version: string;
    model_used_for_optimization_run: string;
    validation_status: string;
    target_characteristic_fck_mpa: number;
    target_mean_strength_fck_prime_mpa: number;
    predicted_strength_mpa?: number;
    prediction_margin_mpa?: number;
    prediction_mean_abs_error_mae?: number;
  };
  mix_optimization: {
    has_optimization_run: boolean;
    optimization_run_id?: string;
    optimization_objective: string;
    total_candidates_evaluated: number;
    feasible_candidates_count: number;
    pareto_optimal_count: number;
    selected_candidate_identifier?: string;
    binder_intensity_kg_m3?: number;
    water_binder_ratio?: number;
    yield_m3?: number;
    recipe_impact_summary: string;
  };
  governance_and_commercial: {
    engineering_feasibility: string;
    review_status: string;
    human_reviewer_username?: string;
    human_reviewer_role?: string;
    review_timestamp?: string;
    review_reason_code?: string;
    pricing_configuration_status: string;
    pricing_source_description: string;
    cost_per_m3_inr?: number;
    cost_delta_per_m3_inr?: number;
    production_activation_status: string;
    production_activation_notice: string;
  };
}

export interface DashboardExportParams {
  plant_code?: string;
  recipe_code?: string;
  date_from?: string;
  date_to?: string;
  run_id?: string;
  candidate_id?: string;
}

export const fetchExecutiveDashboardSummary = async (
  params?: DashboardExportParams
): Promise<ExecutiveDashboardSummaryDTO> => {
  const qs = buildQueryString(params as any);
  return await apiClient.get<ExecutiveDashboardSummaryDTO>(`/reporting/executive-summary${qs}`);
};

export const exportDashboardJSON = async (
  params?: DashboardExportParams
): Promise<void> => {
  const qs = buildQueryString(params as any);
  const data = await apiClient.get<any>(`/reporting/export/json${qs}`);
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  const plantSuffix = params?.plant_code && params.plant_code.toUpperCase() !== 'ALL' ? `_${params.plant_code}` : '';
  const dateSuffix = new Date().toISOString().split('T')[0];
  a.download = `ACC_RMC_Dashboard${plantSuffix}_${dateSuffix}.json`;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    if (document.body.contains(a)) {
      document.body.removeChild(a);
    }
    window.URL.revokeObjectURL(url);
  }, 10000);
};

export const exportDashboardPDF = async (
  params?: DashboardExportParams
): Promise<void> => {
  const qs = buildQueryString(params as any);
  const token = getAuthToken();
  const baseUrl = resolveBaseUrl();
  const response = await fetch(`${baseUrl}/reporting/export/pdf${qs}`, {
    method: 'GET',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    throw new Error(`PDF export failed with status ${response.status}`);
  }

  const arrayBuffer = await response.arrayBuffer();
  const blob = new Blob([arrayBuffer], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  const plantSuffix = params?.plant_code && params.plant_code.toUpperCase() !== 'ALL' ? `_${params.plant_code}` : '';
  const dateSuffix = new Date().toISOString().split('T')[0];
  a.download = `ACC_RMC_Operations_Report${plantSuffix}_${dateSuffix}.pdf`;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    if (document.body.contains(a)) {
      document.body.removeChild(a);
    }
    window.URL.revokeObjectURL(url);
  }, 10000);
};
