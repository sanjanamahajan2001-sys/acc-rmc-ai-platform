import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { MixOptimizationSection } from '../components/dashboard/optimization/MixOptimizationSection';
import { optimizationService } from '../services/optimizationService';
import { masterDataService } from '../services/masterDataService';

vi.mock('../services/optimizationService');
vi.mock('../services/masterDataService');

describe('MixOptimizationSection Component', () => {
  const mockRecipes = [
    {
      id: 'recipe-uuid-1',
      recipe_code: 'M30_STD',
      recipe_name: 'M30 Standard Mix',
      grade: 'M30',
    },
    {
      id: 'recipe-uuid-2',
      recipe_code: 'M40_HIGH',
      recipe_name: 'M40 High Performance',
      grade: 'M40',
    },
  ];

  const mockRunResponse = {
    run_id: 'run-12345678-abcd',
    recipe_id: 'recipe-uuid-1',
    recipe_code: 'M30_STD',
    plant_code: 'PLANT-01',
    optimization_objective: 'MINIMIZE_COST' as const,
    run_status: 'CREATED',
    stage_message: 'Optimization Run Created — Awaiting Candidate Evaluation',
    recipe_snapshot: {
      recipe_id: 'recipe-uuid-1',
      recipe_code: 'M30_STD',
      recipe_name: 'M30 Standard Mix',
      grade: 'M30',
      target_strength_mpa: 30,
      constituents: [
        {
          material_id: 'mat-1',
          material_code: 'OPC_53',
          material_name: 'OPC 53 Cement',
          target_quantity_kg_m3: 380,
          engineering_unit: 'kg',
        },
      ],
    },
    model_snapshot: {
      model_name: 'Baseline Random Forest',
      model_version: 'rf-c517d534',
      framework: 'Scikit-Learn',
      algorithm: 'RandomForestRegressor',
      feature_schema_version: '1.0.0',
      deployment_status: 'ACTIVE',
      validation_status: 'ACTIVE — BASELINE MODEL (LIMITED VALIDATION)',
      prediction_source_semantics: 'ML_MODEL (Analytical Prediction — Limited Validation)',
    },
    target_strength_snapshot: {
      characteristic_strength_fck_mpa: 30,
      standard_deviation_mpa: 5.0,
      standard_deviation_source: 'IS456_ASSUMED_TABLE_8',
      target_mean_strength_fck_prime_mpa: 38.25,
      formula_reference: "f'ck = fck + 1.65 * sigma",
    },
    constraints_snapshot: {
      exposure_class: 'MODERATE',
      standard_edition: 'IS 456:2000 Table 5 & IS 10262:2019',
      configuration_version: '1.0.0',
      items: [
        {
          constraint_name: 'Minimum Cementitious Content',
          standard_reference: 'IS 456:2000 Table 5 (MODERATE)',
          limit_value: 300,
          unit: 'kg/m³',
          comparison: 'MINIMUM',
          status: 'ACTIVE',
        },
      ],
    },
    candidates_count: 0,
    created_at: new Date().toISOString(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(masterDataService.getRecipes).mockResolvedValue(mockRecipes as any);
    vi.mocked(optimizationService.getLatestRun).mockResolvedValue(null);
  });

  it('1. Renders optimization workspace header and model provenance badge', async () => {
    render(<MixOptimizationSection selectedPlant="PLANT-01" />);

    expect(screen.getByText(/AI Mix Optimization & Target Workspace/i)).toBeInTheDocument();
    expect(screen.getByText(/Active Candidate Solver & Pareto Frontier/i)).toBeInTheDocument();
    expect(screen.getByText(/ACTIVE — BASELINE MODEL/i)).toBeInTheDocument();
    expect(screen.getByText(/Analytical Prediction \(Limited Validation\)/i)).toBeInTheDocument();
  });

  it('2. Loads recipes into selector and shows empty state when no prior run exists', async () => {
    render(<MixOptimizationSection selectedPlant="PLANT-01" />);

    await waitFor(() => {
      expect(screen.getByText(/No Optimization Run Context Found/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/M30_STD \(M30\) — M30 Standard Mix/i)).toBeInTheDocument();
  });

  it('3. Explicitly triggers optimization run and renders immutable snapshot details and empty candidate state', async () => {
    vi.mocked(optimizationService.triggerRun).mockResolvedValue(mockRunResponse);

    render(<MixOptimizationSection selectedPlant="PLANT-01" />);

    await waitFor(() => {
      expect(screen.getByText(/M30_STD \(M30\) — M30 Standard Mix/i)).toBeInTheDocument();
    });

    const triggerBtn = screen.getByRole('button', { name: /Run AI Optimization/i });
    await act(async () => {
      fireEvent.click(triggerBtn);
    });

    await waitFor(() => {
      expect(optimizationService.triggerRun).toHaveBeenCalledTimes(1);
    });

    // Check rendered snapshot elements
    expect(screen.getByRole('heading', { name: /Target Mean Strength/i })).toBeInTheDocument();
    expect(screen.getByText(/38.25 MPa/i)).toBeInTheDocument();
    expect(screen.getByText(/rf-c517d534/i)).toBeInTheDocument();
    expect(screen.getByText(/Optimization Run Context Created — Awaiting Candidate Evaluation/i)).toBeInTheDocument();
  });
});
