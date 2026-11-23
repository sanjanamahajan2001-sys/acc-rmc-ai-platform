import { apiClient } from './apiClient';

export interface RecipeConstituentSnapshot {
  material_id: string;
  material_code: string;
  material_name: string;
  category_code?: string;
  target_quantity_kg_m3: number;
  engineering_unit: string;
  default_density_kg_m3?: number;
}

export interface RecipeSnapshot {
  recipe_id: string;
  recipe_code: string;
  recipe_name: string;
  mix_design_code?: string;
  grade: string;
  target_strength_mpa: number;
  water_cement_ratio?: number;
  slump_target_mm?: number;
  nominal_max_aggregate_size_mm?: number;
  exposure_class?: string;
  constituents: RecipeConstituentSnapshot[];
}

export interface ModelSnapshot {
  model_registry_id?: string;
  model_name: string;
  model_version: string;
  framework: string;
  algorithm: string;
  feature_schema_version: string;
  checksum?: string;
  deployment_status: string;
  validation_status: string;
  prediction_source_semantics: string;
}

export interface TargetStrengthSnapshot {
  characteristic_strength_fck_mpa: number;
  standard_deviation_mpa: number;
  standard_deviation_source: string;
  target_mean_strength_fck_prime_mpa: number;
  formula_reference: string;
}

export interface ConstraintItem {
  constraint_name: string;
  standard_reference: string;
  limit_value: number;
  unit: string;
  comparison: string;
  status: string;
}

export interface ConstraintsSnapshot {
  exposure_class: string;
  standard_edition: string;
  configuration_version: string;
  items: ConstraintItem[];
}

export interface OptimizationRunResponse {
  run_id: string;
  recipe_id: string;
  recipe_code: string;
  plant_code: string;
  optimization_objective: 'MINIMIZE_COST' | 'MINIMIZE_BINDER' | 'BALANCED';
  run_status: string;
  stage_message: string;
  recipe_snapshot: RecipeSnapshot;
  model_snapshot: ModelSnapshot;
  target_strength_snapshot: TargetStrengthSnapshot;
  constraints_snapshot: ConstraintsSnapshot;
  pricing_snapshot?: Record<string, any>;
  candidates_count: number;
  created_at: string;
  triggered_by_user_id?: string;
}

export interface OptimizationTriggerRequest {
  recipe_id: string;
  plant_code: string;
  optimization_objective?: 'MINIMIZE_COST' | 'MINIMIZE_BINDER' | 'BALANCED';
  target_strength_margin_mpa?: number;
  parameter_overrides?: Record<string, any>;
}

export interface CandidateConstituent {
  material_code: string;
  material_name: string;
  category_code: string;
  quantity_kg_m3: number;
  specific_gravity: number;
  absolute_volume_m3: number;
}

export interface ConstraintDiagnosticItem {
  constraint_name: string;
  standard_reference: string;
  limit_value: number;
  actual_value: number;
  unit: string;
  comparison: string;
  status: string;
  margin: number;
}

export interface PhysicalVolumeDiagnostic {
  volume_balance_actual_m3: number;
  volume_balance_target_m3: number;
  volume_balance_deviation_m3: number;
  volume_tolerance_limit_m3: number;
  air_volume_m3: number;
  validation_status: string;
}

export interface OptimizationCandidate {
  id: string;
  candidate_identifier: string;
  predicted_strength_mpa: number;
  target_mean_strength_mpa: number;
  characteristic_strength_fck_mpa: number;
  strength_margin_mpa: number;
  strength_gate_status: string;
  prediction_source: string;
  prediction_source_semantics: string;
  model_name: string;
  model_version: string;
  binder_intensity_kg_m3: number;
  cost_per_m3: number | null;
  water_binder_ratio: number;
  water_cement_ratio: number;
  is_feasible: boolean;
  is_non_dominated: boolean;
  is_recommended: boolean | null;
  physical_volume_diagnostic: PhysicalVolumeDiagnostic;
  constraint_diagnostics: ConstraintDiagnosticItem[];
  constituents: CandidateConstituent[];
}

export interface BaselineCoordinates {
  recipe_code: string;
  grade: string;
  characteristic_strength_fck_mpa: number;
  target_mean_strength_fck_prime_mpa: number;
  predicted_strength_mpa: number;
  binder_intensity_kg_m3: number;
  cost_per_m3: number | null;
  water_binder_ratio: number;
}

export interface CandidateEvaluationResponse {
  run_id: string;
  recipe_code: string;
  plant_code: string;
  optimization_objective: string;
  run_status: string;
  stage_message: string;
  total_candidates: number;
  feasible_candidates_count: number;
  pareto_candidates_count: number;
  cost_configured: boolean;
  objective_configured: boolean;
  baseline_coordinates: BaselineCoordinates;
  candidates: OptimizationCandidate[];
  evaluation_duration_ms: number;
  evaluated_at: string;
}

// Phase 5C Contracts
export interface ConstituentImpactItem {
  material_id: string | null;
  material_code: string;
  material_name: string;
  category_code: string;
  current_quantity_kg_m3: number;
  candidate_quantity_kg_m3: number;
  absolute_delta_kg_m3: number;
  percentage_delta: number | null;
  current_specific_gravity: number;
  candidate_specific_gravity: number;
  current_volume_m3: number;
  candidate_volume_m3: number;
  volume_delta_m3: number;
  status_label: 'NORMAL' | 'NEW_CONSTITUENT' | 'REMOVED_CONSTITUENT' | 'NO_QUANTITY';
}

export interface RecipeImpactSummary {
  current_total_binder_kg_m3: number;
  candidate_total_binder_kg_m3: number;
  binder_delta_kg_m3: number;
  binder_percentage_delta: number | null;
  current_water_kg_m3: number;
  candidate_water_kg_m3: number;
  water_delta_kg_m3: number;
  water_percentage_delta: number | null;
  current_water_binder_ratio: number;
  candidate_water_binder_ratio: number;
  water_binder_ratio_delta: number;
  current_yield_m3: number;
  candidate_yield_m3: number;
  yield_delta_m3: number;
  aggregates_delta_kg_m3: number;
  admixture_delta_kg_m3: number;
}

export interface CandidateEvaluationSummary {
  predicted_strength_mpa: number;
  target_mean_strength_mpa: number;
  characteristic_strength_fck_mpa: number;
  strength_margin_mpa: number;
  strength_gate_status: string;
  prediction_source: string;
  prediction_source_semantics: string;
  model_name: string;
  model_version: string;
  is_feasible: boolean;
  is_non_dominated: boolean;
  is_recommended: boolean | null;
}

export interface RecipeImpactResponse {
  run_id: string;
  candidate_id: string;
  candidate_identifier: string;
  recipe_code: string;
  plant_code: string;
  grade: string;
  exposure_class: string;
  optimization_objective: string;
  constituents: ConstituentImpactItem[];
  impact_summary: RecipeImpactSummary;
  candidate_evaluation: CandidateEvaluationSummary;
  evaluated_at: string;
}

// Phase 5D Contracts
export interface CostPriceProvenanceDTO {
  snapshot_id?: string | null;
  material_id: string | null;
  material_code: string;
  unit_price: number | null;
  price_unit: string;
  currency: string;
  price_source: string;
  price_version: string | null;
  effective_from: string | null;
  effective_to: string | null;
  plant_code?: string | null;
  conversion_status?: string;
  is_available: boolean;
}

export interface MaterialCostImpactDTO {
  material_id: string | null;
  material_code: string;
  material_name: string;
  category_code: string;
  master_quantity_kg_m3: number;
  candidate_quantity_kg_m3: number;
  quantity_delta_kg_m3: number;
  unit_price_per_kg: number | null;
  price_unit_display: string;
  currency: string;
  master_cost_per_m3: number | null;
  candidate_cost_per_m3: number | null;
  cost_delta_per_m3: number | null;
  cost_delta_percent: number | null;
  price_provenance: CostPriceProvenanceDTO;
  status_label: string;
}

export interface ProductionVolumeImpactDTO {
  is_configured: boolean;
  volume_source?: string | null;
  volume_period?: string | null;
  volume_basis?: string | null;
  daily_volume_m3: number | null;
  monthly_volume_m3: number | null;
  annualized_volume_m3: number | null;
  daily_cost_delta: number | null;
  monthly_cost_delta: number | null;
  annualized_cost_delta: number | null;
  currency: string;
}

export interface RecipeCostSummaryDTO {
  cost_status: 'CONFIGURED' | 'NOT_CONFIGURED' | 'PARTIALLY_CONFIGURED';
  total_cost_available?: boolean;
  currency: string;
  master_cost_per_m3: number | null;
  candidate_cost_per_m3: number | null;
  cost_delta_per_m3: number | null;
  cost_delta_percent: number | null;
  unpriced_materials?: string[];
  missing_price_constituents: string[];
  production_impact: ProductionVolumeImpactDTO;
}

export interface CostImpactResponseDTO {
  run_id: string;
  candidate_id: string;
  candidate_identifier: string;
  recipe_code: string;
  grade: string;
  plant_code: string;
  is_feasible?: boolean;
  cost_summary: RecipeCostSummaryDTO;
  material_impacts: MaterialCostImpactDTO[];
  price_source_description: string;
  pricing_snapshot_id?: string | null;
  pricing_version?: string | null;
  effective_date?: string | null;
  calculated_at: string;
}


// Phase 5E Contracts
export interface CandidateGovernanceItemDTO {
  candidate_id: string;
  candidate_identifier: string;
  is_feasible: boolean;
  is_pareto_optimal: boolean;
  predicted_strength_mpa: number | null;
  target_mean_strength_mpa: number | null;
  characteristic_strength_fck_mpa: number | null;
  strength_margin_mpa: number | null;
  binder_intensity_kg_m3: number;
  water_binder_ratio: number;
  yield_m3: number | null;
  cost_status: "CONFIGURED" | "PARTIALLY_CONFIGURED" | "NOT_CONFIGURED";
  cost_per_m3: number | null;
  cost_delta_per_m3: number | null;
  cost_delta_percent: number | null;
  eligibility_status: "ELIGIBLE_FOR_HUMAN_REVIEW" | "NOT_ELIGIBLE_INFEASIBLE" | "NOT_ELIGIBLE_NON_PARETO" | "NOT_ELIGIBLE_NO_FEASIBLE";
  eligibility_reason_code: string;
  eligibility_reason_description: string;
  review_status: "PENDING_REVIEW" | "ACCEPTED" | "REJECTED";
  reviewed_by_user_id?: string | null;
  reviewed_by_username?: string | null;
  reviewed_at?: string | null;
  review_decision_reason?: string | null;
  review_comments?: string | null;
  model_lineage_description: string;
  allowed_actions: string[];
}

export interface RunGovernanceResponseDTO {
  run_id: string;
  recipe_code: string;
  grade: string;
  plant_code: string;
  run_status: string;
  total_candidates: number;
  feasible_candidates_count: number;
  pareto_optimal_count: number;
  eligible_for_review_count: number;
  reviewed_accepted_count: number;
  reviewed_rejected_count: number;
  has_feasible_candidates: boolean;
  governance_message: string;
  cost_status: "CONFIGURED" | "PARTIALLY_CONFIGURED" | "NOT_CONFIGURED";
  price_source_description: string;
  user_can_review: boolean;
  user_role: string;
  production_activation_status: string;
  candidates: CandidateGovernanceItemDTO[];
  evaluated_at: string;
}

export interface CandidateReviewActionRequestDTO {
  action: "ACCEPT" | "REJECT" | "RESET";
  reason_code: string;
  comments?: string | null;
}

export const optimizationService = {
  /**
   * Fetch the most recent optimization run without recomputing
   */
  async getLatestRun(recipeCode?: string, plantCode?: string): Promise<OptimizationRunResponse | null> {
    const params: Record<string, string> = {};
    if (recipeCode) params.recipe_code = recipeCode;
    if (plantCode) params.plant_code = plantCode;

    return await apiClient.get<OptimizationRunResponse | null>('/optimization/runs/latest', params);
  },

  /**
   * Explicitly trigger an AI mix optimization run snapshot
   */
  async triggerRun(payload: OptimizationTriggerRequest): Promise<OptimizationRunResponse> {
    return await apiClient.post<OptimizationRunResponse>('/optimization/runs/trigger', payload);
  },

  /**
   * Evaluate candidate mix alternatives with physical validation & Pareto classification (Phase 5B)
   */
  async evaluateRun(runId: string): Promise<CandidateEvaluationResponse> {
    return await apiClient.post<CandidateEvaluationResponse>(`/optimization/runs/${runId}/evaluate`, {});
  },

  /**
   * Fetch persisted candidates for a given optimization run
   */
  async getCandidates(runId: string): Promise<OptimizationCandidate[]> {
    return await apiClient.get<OptimizationCandidate[]>(`/optimization/runs/${runId}/candidates`);
  },

  /**
   * Fetch recipe impact comparison between Phase 5A baseline and Phase 5B candidate (Phase 5C)
   */
  async getCandidateImpact(runId: string, candidateId: string): Promise<RecipeImpactResponse> {
    return await apiClient.get<RecipeImpactResponse>(`/optimization/runs/${runId}/candidates/${candidateId}/impact`);
  },

  /**
   * Fetch cost and commercial feasibility comparison (Phase 5D)
   */
  async getCandidateCostImpact(runId: string, candidateId: string): Promise<CostImpactResponseDTO> {
    return await apiClient.get<CostImpactResponseDTO>(`/optimization/runs/${runId}/candidates/${candidateId}/cost-impact`);
  },
  /**
   * Fetch recommendation governance and human review lifecycle (Phase 5E)
   */
  async getRunGovernance(runId: string): Promise<RunGovernanceResponseDTO> {
    return await apiClient.get<RunGovernanceResponseDTO>(`/optimization/runs/${runId}/governance`);
  },

  /**
   * Submit an authoritative human review decision on an optimization candidate (Phase 5E)
   */
  async reviewCandidate(
    runId: string,
    candidateId: string,
    payload: CandidateReviewActionRequestDTO
  ): Promise<CandidateGovernanceItemDTO> {
    return await apiClient.post<CandidateGovernanceItemDTO>(
      `/optimization/runs/${runId}/candidates/${candidateId}/review`,
      payload
    );
  },
};
