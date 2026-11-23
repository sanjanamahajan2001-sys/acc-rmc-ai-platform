import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { RecipeImpactComparison } from '../components/dashboard/optimization/RecipeImpactComparison';
import { optimizationService, RecipeImpactResponse } from '../services/optimizationService';

vi.mock('../services/optimizationService');

describe('RecipeImpactComparison Component (Clean Enterprise UI)', () => {
  const mockImpactData: RecipeImpactResponse = {
    run_id: 'run-uuid-1234',
    candidate_id: 'cand-uuid-5678',
    candidate_identifier: 'CAND-02',
    recipe_code: 'M-30-STD',
    plant_code: 'PLANT-01',
    grade: 'M30',
    exposure_class: 'MODERATE',
    optimization_objective: 'MINIMIZE_BINDER',
    constituents: [
      {
        material_id: 'mat-cem',
        material_code: 'CEM-OPC-53',
        material_name: 'OPC 53 Cement',
        category_code: 'CEMENT',
        current_quantity_kg_m3: 320.0,
        candidate_quantity_kg_m3: 260.0,
        absolute_delta_kg_m3: -60.0,
        percentage_delta: -18.75,
        current_specific_gravity: 3.15,
        candidate_specific_gravity: 3.15,
        current_volume_m3: 0.1016,
        candidate_volume_m3: 0.0825,
        volume_delta_m3: -0.0191,
        status_label: 'NORMAL',
      },
      {
        material_id: 'mat-fa',
        material_code: 'FA-CLASS-F',
        material_name: 'Fly Ash Class F',
        category_code: 'FLY_ASH',
        current_quantity_kg_m3: 60.0,
        candidate_quantity_kg_m3: 80.0,
        absolute_delta_kg_m3: 20.0,
        percentage_delta: 33.33,
        current_specific_gravity: 2.2,
        candidate_specific_gravity: 2.2,
        current_volume_m3: 0.0273,
        candidate_volume_m3: 0.0364,
        volume_delta_m3: 0.0091,
        status_label: 'NORMAL',
      },
      {
        material_id: 'mat-ggbs',
        material_code: 'GGBS-GRADE-1',
        material_name: 'Ground Granulated Slag',
        category_code: 'GGBS',
        current_quantity_kg_m3: 0.0,
        candidate_quantity_kg_m3: 40.0,
        absolute_delta_kg_m3: 40.0,
        percentage_delta: null,
        current_specific_gravity: 2.85,
        candidate_specific_gravity: 2.85,
        current_volume_m3: 0.0,
        candidate_volume_m3: 0.014,
        volume_delta_m3: 0.014,
        status_label: 'NEW_CONSTITUENT',
      },
      {
        material_id: 'mat-wtr',
        material_code: 'WATER-TAP',
        material_name: 'Batch Water',
        category_code: 'WATER',
        current_quantity_kg_m3: 160.0,
        candidate_quantity_kg_m3: 140.0,
        absolute_delta_kg_m3: -20.0,
        percentage_delta: -12.5,
        current_specific_gravity: 1.0,
        candidate_specific_gravity: 1.0,
        current_volume_m3: 0.16,
        candidate_volume_m3: 0.14,
        volume_delta_m3: -0.02,
        status_label: 'NORMAL',
      },
    ],
    impact_summary: {
      current_total_binder_kg_m3: 380.0,
      candidate_total_binder_kg_m3: 380.0,
      binder_delta_kg_m3: 0.0,
      binder_percentage_delta: 0.0,
      current_water_kg_m3: 160.0,
      candidate_water_kg_m3: 140.0,
      water_delta_kg_m3: -20.0,
      water_percentage_delta: -12.5,
      current_water_binder_ratio: 0.421,
      candidate_water_binder_ratio: 0.368,
      water_binder_ratio_delta: -0.053,
      current_yield_m3: 1.0,
      candidate_yield_m3: 1.0,
      yield_delta_m3: 0.0,
      aggregates_delta_kg_m3: 20.0,
      admixture_delta_kg_m3: 0.0,
    },
    candidate_evaluation: {
      predicted_strength_mpa: 42.5,
      target_mean_strength_mpa: 38.25,
      characteristic_strength_fck_mpa: 30.0,
      strength_margin_mpa: 4.25,
      strength_gate_status: 'PASSED_ROBUST',
      prediction_source: 'ML_MODEL',
      prediction_source_semantics: 'ML_MODEL (Analytical Prediction — Active Model)',
      model_name: 'acc_concrete_28d_strength',
      model_version: 'rf-c517d534',
      is_feasible: true,
      is_non_dominated: true,
      is_recommended: null,
    },
    evaluated_at: '2026-09-18T10:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('1. Renders loading state while fetching impact metrics', async () => {
    vi.mocked(optimizationService.getCandidateImpact).mockReturnValue(new Promise(() => {}));
    render(<RecipeImpactComparison runId="run-1" candidateId="cand-1" />);

    expect(screen.getByText(/Computing recipe impact & baseline deltas/i)).toBeInTheDocument();
  });

  it('2. Renders error alert when API call fails', async () => {
    vi.mocked(optimizationService.getCandidateImpact).mockRejectedValue(
      new Error('Candidate was not found.')
    );
    render(<RecipeImpactComparison runId="run-1" candidateId="cand-1" />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to Load Recipe Impact/i)).toBeInTheDocument();
      expect(screen.getByText(/Candidate was not found./i)).toBeInTheDocument();
    });
  });

  it('3. Renders full comparison table, clean summary cards, and does not contain internal Phase 5C language', async () => {
    vi.mocked(optimizationService.getCandidateImpact).mockResolvedValue(mockImpactData);
    render(<RecipeImpactComparison runId="run-uuid-1234" candidateId="cand-uuid-5678" />);

    await waitFor(() => {
      expect(screen.getByText(/Recipe Impact & Baseline Comparison/i)).toBeInTheDocument();
    });

    // Ensure NO "Phase 5C" in user-facing UI
    expect(screen.queryByText(/Phase 5C/i)).not.toBeInTheDocument();

    // Header & Badges
    expect(screen.getByText(/FEASIBLE/i)).toBeInTheDocument();
    expect(screen.getByText(/PARETO FRONTIER/i)).toBeInTheDocument();

    // Summary Cards
    expect(screen.getByText(/Binder Content/i)).toBeInTheDocument();
    expect(screen.getByText(/Water Content/i)).toBeInTheDocument();
    expect(screen.getByText(/Water\/Binder Ratio/i)).toBeInTheDocument();
    expect(screen.getByText(/42.5 MPa/i)).toBeInTheDocument();

    // Table rows & materials
    expect(screen.getByText(/OPC 53 Cement/i)).toBeInTheDocument();
    expect(screen.getByText(/Fly Ash Class F/i)).toBeInTheDocument();
    expect(screen.getByText(/Ground Granulated Slag/i)).toBeInTheDocument();

    // New constituent badge
    expect(screen.getByText(/New \(\+40.0 kg\)/i)).toBeInTheDocument();

    // Ensure valid evaluation time is rendered and NO "Invalid Date"
    expect(screen.queryByText(/Invalid Date/i)).not.toBeInTheDocument();
  });
});
