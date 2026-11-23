import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ExecutiveDashboardSummary } from '../components/dashboard/ExecutiveDashboardSummary';
import { DashboardExportControl } from '../components/dashboard/DashboardExportControl';
import * as reportingService from '../services/reportingService';

describe('ExecutiveDashboardSummary Component', () => {
  const mockSummary: reportingService.ExecutiveDashboardSummaryDTO = {
    quality_and_production: {
      grades_evaluated: 358,
      total_batches_produced: 32,
      total_volume_m3: 180.0,
      specimens_tested_28d: 142,
      mean_strength_28d_mpa: 40.03,
      quality_compliance_percent: 93.9,
      strength_variability_sigma_mpa: 7.88,
      strength_cov_percent: 19.69,
      weighment_accuracy_percent: 87.43,
    },
    strength_prediction: {
      platform_active_model: 'randomforest-439de1ef',
      platform_model_version: 'randomforest-439de1ef',
      model_used_for_optimization_run: '—',
      validation_status: 'Limited Validation',
      target_characteristic_fck_mpa: 31.2,
      target_mean_strength_fck_prime_mpa: 44.2,
      predicted_strength_mpa: 42.5,
      prediction_margin_mpa: 2.47,
      prediction_mean_abs_error_mae: 3.1,
    },
    mix_optimization: {
      has_optimization_run: true,
      optimization_run_id: 'run-001',
      optimization_objective: 'Cost Minimization',
      total_candidates_evaluated: 120,
      feasible_candidates_count: 14,
      pareto_optimal_count: 5,
      selected_candidate_identifier: 'CAND-001',
      binder_intensity_kg_m3: 380,
      water_binder_ratio: 0.42,
      yield_m3: 1.0,
      recipe_impact_summary: '-15kg Cement, +20kg FlyAsh',
    },
    governance_and_commercial: {
      engineering_feasibility: 'FEASIBLE',
      review_status: 'ACCEPTED',
      human_reviewer_username: 'superadmin',
      human_reviewer_role: 'PLANT_MANAGER',
      review_timestamp: '2026-09-18T12:00:00Z',
      review_reason_code: 'COST_OPTIMAL',
      pricing_configuration_status: 'CONFIGURED',
      pricing_source_description: 'ERP Production Rates',
      cost_per_m3_inr: 3850.0,
      cost_delta_per_m3_inr: -120.0,
      production_activation_status: 'PRODUCTION_ACTIVATION_OUTSIDE_CURRENT_PHASE',
      production_activation_notice: 'Production activation is outside the current phase.',
    },
  };

  it('renders all 4 factual summary groups correctly', () => {
    render(<ExecutiveDashboardSummary summary={mockSummary} />);

    // Group headers
    expect(screen.getByText(/A\. Quality & Production/i)).toBeInTheDocument();
    expect(screen.getByText(/B\. Strength Prediction/i)).toBeInTheDocument();
    expect(screen.getByText(/C\. Mix Optimization/i)).toBeInTheDocument();
    expect(screen.getByText(/D\. Governance & Status/i)).toBeInTheDocument();

    // Group values
    expect(screen.getByText(/40.03 MPa/i)).toBeInTheDocument();
    expect(screen.getByText(/93.9%/i)).toBeInTheDocument();
    expect(screen.getByText(/randomforest-439de1ef/i)).toBeInTheDocument();
    expect(screen.getByText(/HUMAN REVIEW: ACCEPTED/i)).toBeInTheDocument();
    expect(screen.getByText(/Production activation is outside the current phase\./i)).toBeInTheDocument();
  });
});

describe('DashboardExportControl Component', () => {
  it('renders Export PDF and Export JSON buttons and handles click', async () => {
    const mockExportPdf = vi.spyOn(reportingService, 'exportDashboardPDF').mockResolvedValue(undefined);
    const mockExportJson = vi.spyOn(reportingService, 'exportDashboardJSON').mockResolvedValue(undefined);

    render(
      <DashboardExportControl
        plantCode="PLANT-NS70"
        recipeCode="M30-STANDARD"
      />
    );

    const pdfBtn = screen.getByTestId('export-pdf-button');
    const jsonBtn = screen.getByTestId('export-json-button');

    expect(pdfBtn).toBeInTheDocument();
    expect(jsonBtn).toBeInTheDocument();

    fireEvent.click(pdfBtn);
    expect(mockExportPdf).toHaveBeenCalledWith({
      plant_code: 'PLANT-NS70',
      recipe_code: 'M30-STANDARD',
      date_from: undefined,
      date_to: undefined,
      run_id: undefined,
      candidate_id: undefined,
    });

    fireEvent.click(jsonBtn);
    expect(mockExportJson).toHaveBeenCalledWith({
      plant_code: 'PLANT-NS70',
      recipe_code: 'M30-STANDARD',
      date_from: undefined,
      date_to: undefined,
      run_id: undefined,
      candidate_id: undefined,
    });
  });
});
