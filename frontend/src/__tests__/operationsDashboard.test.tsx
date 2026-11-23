class MockEventSource {
  onopen: any = null;
  onerror: any = null;
  addEventListener: any = vi.fn();
  removeEventListener: any = vi.fn();
  close: any = vi.fn();
}
// @ts-ignore
global.EventSource = MockEventSource;
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { OperationsDashboardPage } from '../pages/OperationsDashboardPage';
import { LiveSyncIndicator } from '../components/dashboard/LiveSyncIndicator';
import { BrowserRouter } from 'react-router-dom';
import * as reportingService from '../services/reportingService';

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 'usr-1', username: 'admin', roles: ['SUPER_ADMIN'] },
    hasRole: () => true,
  }),
}));

vi.mock('../components/AppShell', () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => <div data-testid="app-shell">{children}</div>,
}));

vi.mock('../services/reportingService', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/reportingService')>();
  return {
    ...actual,
    fetchFilterOptions: vi.fn(),
    fetchOperationalMetrics: vi.fn(),
    fetchStrengthDistribution: vi.fn(),
    fetchMixPerformance: vi.fn(),
    fetchStrengthTimeline: vi.fn(),
    fetchMaterialConsumption: vi.fn(),
    fetchBatchVariance: vi.fn(),
    fetchBinderEfficiency: vi.fn(),
    fetchPredictionSummary: vi.fn(),
    fetchActualVsPredicted: vi.fn(),
    fetchPredictionErrorTrend: vi.fn(),
    fetchModelFeatures: vi.fn(),
    fetchModelMetadata: vi.fn(),
    fetchModelBacktest: vi.fn(),
    requestSSETicket: vi.fn(),
  };
});

describe('OperationsDashboardPage & LiveSyncIndicator Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(reportingService.fetchPredictionSummary).mockResolvedValue({
      scope: {
        mode: 'PRODUCTION_STORED',
        active_model_id: 'baselineridge-ca125dcf',
        active_model_name: 'Production Baseline Ridge (28-day)',
        sample_count: 0,
        total_available_batches: 1898,
        tested_28d_batches: 1324,
        historical_observations: 1165,
        valid_backtest_pairs: 3,
        data_completeness_pct: 0,
        status: 'NO_STORED_PREDICTIONS_IN_RANGE',
      },
      metrics: { mae_mpa: null, rmse_mpa: null, r2_score: null, mean_residual_mpa: null, residual_std_dev_mpa: null, sample_count: 0 },
      status: 'NO_STORED_PREDICTIONS_IN_RANGE',
    } as any);
    vi.mocked(reportingService.fetchActualVsPredicted).mockResolvedValue({
      scope: { mode: 'PRODUCTION_STORED', active_model_id: 'baselineridge-ca125dcf', active_model_name: 'Production Baseline Ridge (28-day)', sample_count: 0, total_available_batches: 1898, tested_28d_batches: 1324, historical_observations: 1165, valid_backtest_pairs: 3, data_completeness_pct: 0, status: 'NO_STORED_PREDICTIONS_IN_RANGE' },
      items: [],
      summary_metrics: { mae_mpa: null, rmse_mpa: null, r2_score: null, mean_residual_mpa: null, residual_std_dev_mpa: null, sample_count: 0 },
    } as any);
    vi.mocked(reportingService.fetchPredictionErrorTrend).mockResolvedValue({
      scope: { mode: 'PRODUCTION_STORED', active_model_id: 'baselineridge-ca125dcf', active_model_name: 'Production Baseline Ridge (28-day)', sample_count: 0, total_available_batches: 1898, tested_28d_batches: 1324, historical_observations: 1165, valid_backtest_pairs: 3, data_completeness_pct: 0, status: 'NO_STORED_PREDICTIONS_IN_RANGE' },
      items: [],
      operational_monitoring_threshold_mpa: 3.0,
      rolling_window_size: 10,
    } as any);
    vi.mocked(reportingService.fetchModelFeatures).mockResolvedValue({
      model_id: 'baselineridge-ca125dcf',
      model_name: 'Production Baseline Ridge (28-day)',
      algorithm: 'Ridge',
      feature_importance_available: true,
      features: [],
    } as any);
    vi.mocked(reportingService.fetchModelMetadata).mockResolvedValue({
      models: [],
      total_models: 0,
    } as any);
    vi.mocked(reportingService.fetchModelBacktest).mockResolvedValue({
      scope: { mode: 'RETROSPECTIVE_BACKTEST', active_model_id: 'baselineridge-ca125dcf', active_model_name: 'Production Baseline Ridge (28-day)', sample_count: 3, total_available_batches: 1898, tested_28d_batches: 1324, historical_observations: 1165, valid_backtest_pairs: 3, data_completeness_pct: 0.23, status: 'VALIDATED_BACKTEST' },
      metrics: { mae_mpa: 0.0, rmse_mpa: 0.0, r2_score: null, mean_residual_mpa: 0.0, residual_std_dev_mpa: 0.0, sample_count: 3 },
      status: 'VALIDATED_BACKTEST',
    } as any);
  });

  it('1. LiveSyncIndicator renders accurate status labels and colors', () => {
    const { rerender } = render(<LiveSyncIndicator status="LIVE" />);
    expect(screen.getByText('Live (Event-Driven)')).toBeInTheDocument();

    rerender(<LiveSyncIndicator status="SYNCING" />);
    expect(screen.getByText('Syncing Update...')).toBeInTheDocument();

    rerender(<LiveSyncIndicator status="RECONNECTING" />);
    expect(screen.getByText('Reconnecting...')).toBeInTheDocument();

    rerender(<LiveSyncIndicator status="OFFLINE" />);
    expect(screen.getByText('Offline (Reconciling)')).toBeInTheDocument();
  });

  it('2. OperationsDashboardPage loads authoritative KPI metrics, SQC data and filter options', async () => {
    vi.mocked(reportingService.fetchFilterOptions).mockResolvedValue({
      recipes: [
        { recipe_code: 'M-30', recipe_name: 'M-30 Standard', grade: 'M-30', target_strength_mpa: 30.0 }
      ],
      plants: [
        { plant_code: 'PLANT-MUMBAI-01', plant_name: 'Mumbai Central Batching Plant' },
        { plant_code: 'PLANT-DELHI-02', plant_name: 'Delhi South Terminal' },
      ],
      available_date_range: { earliest_date: '2026-01-01', latest_date: '2026-09-17' },
    });

    vi.mocked(reportingService.fetchOperationalMetrics).mockResolvedValue({
      active_plants_count: 5,
      total_ingested_batches: 1327,
      operational_batches_count: 1327,
      historical_qc_batches_count: 0,
      forecast_design_batches_count: 0,
      quality_compliance_rate_pct: 98.4,
      total_cube_tests: 1302,
      total_volume_m3: 14820.5,
      material_consumptions_count: 4809,
    });

    vi.mocked(reportingService.fetchStrengthDistribution).mockResolvedValue({
      total_tested_batches: 1327,
      total_tested_specimens: 1302,
      mean_strength_mpa: 42.5,
      median_strength_mpa: 42.0,
      standard_deviation_mpa: 3.4,
      coefficient_of_variation_pct: 8.0,
      min_strength_mpa: 35.0,
      max_strength_mpa: 52.0,
      characteristic_strength_fck_mpa: 40.0,
      target_mean_strength_fck_prime_mpa: 48.25,
      strength_margin_mpa: 2.5,
      compliance_rate_pct: 98.4,
      stability_grade: 'EXCELLENT',
      histogram_bins: [
        { bin_start: 35.0, bin_end: 37.5, bin_label: '35.0–37.5', count: 12, is_below_fck: true },
        { bin_start: 40.0, bin_end: 42.5, bin_label: '40.0–42.5', count: 500, is_below_fck: false },
      ],
      scope_metadata: {
        plant_code: null,
        recipe_code: null,
        date_from: null,
        date_to: null,
        cache_token_version: 1,
        generated_at: '2026-09-17T11:00:00Z',
      },
    });

    vi.mocked(reportingService.fetchMixPerformance).mockResolvedValue({
      items: [
        {
          recipe_code: 'M-30',
          recipe_name: 'M-30 Standard Mix',
          grade: 'M-30',
          target_strength_fck: 30.0,
          target_mean_strength_fck_prime: 38.25,
          total_batches: 752,
          tested_batches_28d: 515,
          tested_specimens_28d: 540,
          mean_strength_mpa: 40.54,
          standard_deviation_mpa: 3.2,
          coefficient_of_variation_pct: 7.89,
          strength_margin_mpa: 10.54,
          compliance_rate_pct: 98.8,
          stability_status: 'EXCELLENT',
        },
      ],
      total_recipes_evaluated: 1,
      scope_metadata: {
        plant_code: null,
        recipe_code: null,
        date_from: null,
        date_to: null,
        cache_token_version: 1,
        generated_at: '2026-09-17T11:00:00Z',
      },
    });

    vi.mocked(reportingService.fetchStrengthTimeline).mockResolvedValue({
      timeline: [
        {
          batch_number: 'BATCH-001',
          plant_code: 'PLANT-01',
          recipe_code: 'M-30',
          grade: 'M-30',
          production_timestamp: '2026-09-17 10:00',
          result_7d_mpa: 28.5,
          result_28d_mpa: 41.2,
          target_fck_mpa: 30.0,
          target_fck_prime_mpa: 38.25,
          is_compliant_28d: true,
        },
      ],
      total_points: 1,
      scope_metadata: {
        plant_code: null,
        recipe_code: null,
        date_from: null,
        date_to: null,
        cache_token_version: 1,
        generated_at: '2026-09-17T11:00:00Z',
      },
    });

    vi.mocked(reportingService.fetchMaterialConsumption).mockResolvedValue({
      total_batches: 1327,
      total_produced_batches: 1327,
      total_scheduled_batches: 0,
      material_consumption_batch_count: 1327,
      total_volume_m3: 14820.5,
      total_planned_material_kg: 35000000.0,
      total_actual_material_kg: 35100000.0,
      total_variance_kg: 100000.0,
      overall_variance_percentage: 0.28,
      total_binder_consumption_kg: 5000000.0,
      total_water_consumption_kg: 2500000.0,
      total_aggregate_consumption_kg: 27500000.0,
      total_admixture_consumption_kg: 100000.0,
      items: [],
      scope_metadata: {
        plant_code: null,
        recipe_code: null,
        date_from: null,
        date_to: null,
        cache_token_version: 1,
        generated_at: '2026-09-17T11:00:00Z',
      },
    });

    vi.mocked(reportingService.fetchBatchVariance).mockResolvedValue({
      categories: [],
      overall_summary: {
        indicator_name: 'IS 4926:2003 Annex E Weighment Tolerance Indicator',
        total_weighments: 4809,
        classifiable_weighments: 4809,
        compliant_weighments: 4500,
        non_compliant_weighments: 309,
        annex_e_compliance_rate_pct: 93.57,
        mean_abs_variance_pct: 1.2,
        annex_e_weighment_batch_count: 1327,
        unclassified_record_count: 0,
        unclassified_material_codes: [],
        standard_applied: 'IS 4926:2003 Annex E / Clause E-1',
      },
      water_moisture_analysis: {
        planned_water_kg: 2450000.0,
        actual_water_kg: 2500000.0,
        raw_water_variance_kg: 50000.0,
        raw_water_variance_pct: 2.04,
        moisture_probe_records_count: 0,
        total_water_records_count: 1327,
        data_quality_status: 'LIMITED',
        operational_note: 'Raw water variance reflects scale delivery.',
      },
      scope_metadata: {
        plant_code: null,
        recipe_code: null,
        date_from: null,
        date_to: null,
        cache_token_version: 1,
        generated_at: '2026-09-17T11:00:00Z',
      },
    });

    vi.mocked(reportingService.fetchBinderEfficiency).mockResolvedValue({
      recipes: [],
      fleet_summary: {
        total_evaluated_recipes: 1,
        total_production_batches: 1327,
        total_tested_batches_28d: 1327,
        tested_28d_batch_count: 1327,
        fleet_avg_cement_kg_m3: 310.0,
        fleet_avg_binder_kg_m3: 400.0,
        fleet_avg_actual_wb: 0.39,
        fleet_avg_actual_wc: 0.52,
        fleet_avg_28d_strength_mpa: 42.5,
        fleet_avg_binder_intensity: 9.89,
      },
      scope_metadata: {
        plant_code: null,
        recipe_code: null,
        date_from: null,
        date_to: null,
        cache_token_version: 1,
        generated_at: '2026-09-17T11:00:00Z',
      },
    });

    vi.mocked(reportingService.requestSSETicket).mockResolvedValue('test-ticket-123');

    const { container } = render(
      <BrowserRouter>
        <OperationsDashboardPage />
      </BrowserRouter>
    );

    // Initial heading
    expect(screen.getByText('Operations & Quality Control Center')).toBeInTheDocument();

    await waitFor(() => {
      const heading = screen.getByText('Statistical Quality Control (28-Day Strength)');
      expect(heading).toBeInTheDocument();
    });

    // Check what text is in container
    console.log('CONTAINER TEXT CONTENT:', container.textContent);
    expect(container.textContent).toContain('14,820.5');
    expect(container.textContent).toContain('1,327');
    expect(container.textContent).toContain('98.4%');

    // Verify Plant Dropdown Populated
    expect(screen.getByText(/Mumbai Central Batching Plant/)).toBeInTheDocument();
    expect(screen.getByText(/Delhi South Terminal/)).toBeInTheDocument();
  });
});
