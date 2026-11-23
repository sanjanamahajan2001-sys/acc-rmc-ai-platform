import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { ModelPerformanceSummary } from '../components/dashboard/model_monitoring/ModelPerformanceSummary';
import { EvaluationModeStatus } from '../components/dashboard/model_monitoring/EvaluationModeStatus';
import { PredictionValidationChart } from '../components/dashboard/model_monitoring/PredictionValidationChart';
import { PredictionErrorTrend } from '../components/dashboard/model_monitoring/PredictionErrorTrend';
import { ModelFeatureImportance } from '../components/dashboard/model_monitoring/ModelFeatureImportance';
import { ModelInformationPanel } from '../components/dashboard/model_monitoring/ModelInformationPanel';
import { ModelMonitoringSection } from '../components/dashboard/model_monitoring/ModelMonitoringSection';
import * as reportingService from '../services/reportingService';

// Mock reportingService APIs
vi.mock('../services/reportingService', () => ({
  fetchPredictionSummary: vi.fn(),
  fetchActualVsPredicted: vi.fn(),
  fetchPredictionErrorTrend: vi.fn(),
  fetchModelFeatures: vi.fn(),
  fetchModelMetadata: vi.fn(),
  fetchModelBacktest: vi.fn(),
}));

describe('WS-DASH-4B: Model Performance Summary KPI Cards', () => {
  test('renders metric values accurately with 2 decimal places and units', () => {
    render(
      <ModelPerformanceSummary
        metrics={{
          mae_mpa: 1.45,
          rmse_mpa: 1.82,
          r2_score: 0.88,
          mean_residual_mpa: -0.12,
          residual_std_dev_mpa: 1.81,
          sample_count: 120,
        }}
      />
    );

    expect(screen.getByTestId('kpi-sample-count')).toHaveTextContent('120 batches');
    expect(screen.getByTestId('kpi-mae')).toHaveTextContent('1.45 MPa');
    expect(screen.getByTestId('kpi-rmse')).toHaveTextContent('1.82 MPa');
    expect(screen.getByTestId('kpi-r2')).toHaveTextContent('0.880');
    expect(screen.getByTestId('kpi-bias')).toHaveTextContent('-0.12 MPa');
    expect(screen.getByTestId('kpi-residual-std')).toHaveTextContent('1.81 MPa');
  });

  test('renders honest N/A — insufficient data for null metrics (e.g. Production Mode or small sample)', () => {
    render(
      <ModelPerformanceSummary
        metrics={{
          mae_mpa: null,
          rmse_mpa: null,
          r2_score: null,
          mean_residual_mpa: null,
          residual_std_dev_mpa: null,
          sample_count: 0,
        }}
      />
    );

    expect(screen.getByTestId('kpi-sample-count')).toHaveTextContent('0 batches');
    expect(screen.getByTestId('kpi-mae')).toHaveTextContent('N/A — insufficient data');
    expect(screen.getByTestId('kpi-rmse')).toHaveTextContent('N/A — insufficient data');
    expect(screen.getByTestId('kpi-r2')).toHaveTextContent('N/A — insufficient data');
    expect(screen.getByTestId('kpi-bias')).toHaveTextContent('N/A — insufficient data');
    expect(screen.getByTestId('kpi-residual-std')).toHaveTextContent('N/A — insufficient data');
  });
});

describe('WS-DASH-4B: Evaluation Mode Status & Controls', () => {
  test('renders Production Stored empty state notice clearly', () => {
    const onModeChange = vi.fn();
    render(
      <EvaluationModeStatus
        activeMode="PRODUCTION_STORED"
        onModeChange={onModeChange}
        productionScope={{
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
          warning: 'No production predictions currently stored in database.',
        } as any}
      />
    );

    expect(screen.getByText('Production Monitoring (Live)')).toBeInTheDocument();
    expect(screen.getByText(/No production prediction records are available yet/i)).toBeInTheDocument();
  });

  test('renders Retrospective Backtest notice with sample size disclaimer', () => {
    const onModeChange = vi.fn();
    render(
      <EvaluationModeStatus
        activeMode="RETROSPECTIVE_BACKTEST"
        onModeChange={onModeChange}
        backtestScope={{
          mode: 'RETROSPECTIVE_BACKTEST',
          active_model_id: 'baselineridge-ca125dcf',
          active_model_name: 'Production Baseline Ridge (28-day)',
          sample_count: 3,
          total_available_batches: 1898,
          tested_28d_batches: 1324,
          historical_observations: 1165,
          valid_backtest_pairs: 3,
          data_completeness_pct: 0.23,
          status: 'VALIDATED_BACKTEST',
          warning: '3 evaluation pairs — Insufficient sample size for reliable model validation.',
        } as any}
      />
    );

    expect(screen.getByText('Retrospective Backtest (Historical)')).toBeInTheDocument();
    expect(screen.getByText(/Insufficient sample size for reliable model performance assessment/i)).toBeInTheDocument();

    const prodBtn = screen.getByRole('tab', { name: /production monitoring/i });
    fireEvent.click(prodBtn);
    expect(onModeChange).toHaveBeenCalledWith('PRODUCTION_STORED');
  });
});

describe('WS-DASH-4B: Prediction Validation Scatter Chart', () => {
  test('renders scatter points and equality line reference', () => {
    const mockData = {
      scope: {
        mode: 'RETROSPECTIVE_BACKTEST' as const,
        active_model_id: 'baselineridge-ca125dcf',
        active_model_name: 'Production Baseline Ridge (28-day)',
        sample_count: 2,
        total_available_batches: 1898,
        tested_28d_batches: 1324,
        historical_observations: 1165,
        valid_backtest_pairs: 3,
        data_completeness_pct: 0.23,
        status: 'VALIDATED_BACKTEST',
        warning: 'Insufficient sample size',
      },
      items: [
        {
          prediction_id: 1,
          batch_id: 'B1',
          plant_id: 'PL01',
          grade: 'M-40',
          batch_timestamp: '2026-03-01T10:00:00Z',
          break_28d_date: '2026-03-29',
          actual_strength_mpa: 51.3,
          predicted_strength_mpa: 51.3,
          residual_error_mpa: 0.0,
          absolute_error_mpa: 0.0,
          squared_error_mpa2: 0.0,
          is_within_tolerance: true,
        },
        {
          prediction_id: 2,
          batch_id: 'B2',
          plant_id: 'PL01',
          grade: 'M-40',
          batch_timestamp: '2026-03-02T10:00:00Z',
          break_28d_date: '2026-03-30',
          actual_strength_mpa: 48.0,
          predicted_strength_mpa: 50.0,
          residual_error_mpa: 2.0,
          absolute_error_mpa: 2.0,
          squared_error_mpa2: 4.0,
          is_within_tolerance: true,
        },
      ],
      summary_metrics: {
        mae_mpa: 1.0,
        rmse_mpa: 1.41,
        r2_score: 0.5,
        mean_residual_mpa: 1.0,
        residual_std_dev_mpa: 1.41,
        sample_count: 2,
      },
      total_items: 2,
    };

    render(<PredictionValidationChart data={mockData as any} />);
    expect(screen.getByText('Actual vs. Predicted 28-Day Strength')).toBeInTheDocument();
    expect(screen.getByText(/Ideal \(y = x\)/i)).toBeInTheDocument();
  });

  test('renders empty state message when items array is empty', () => {
    const mockEmptyData = {
      scope: {
        mode: 'PRODUCTION_STORED' as const,
        active_model_id: 'baselineridge-ca125dcf',
        active_model_name: 'Production Baseline Ridge (28-day)',
        sample_count: 0,
        total_available_batches: 1898,
        tested_28d_batches: 1324,
        historical_observations: 1165,
        valid_backtest_pairs: 3,
        data_completeness_pct: 0,
        status: 'NO_STORED_PREDICTIONS_IN_RANGE',
        warning: 'No stored predictions',
      },
      items: [],
      summary_metrics: {
        mae_mpa: null,
        rmse_mpa: null,
        r2_score: null,
        mean_residual_mpa: null,
        residual_std_dev_mpa: null,
        sample_count: 0,
      },
      total_items: 0,
    };

    render(<PredictionValidationChart data={mockEmptyData as any} />);
    expect(screen.getByText('No validation pairs available for the selected filters.')).toBeInTheDocument();
  });
});

describe('WS-DASH-4B: Prediction Error Trend Chart', () => {
  test('renders operational threshold indicator ±3.0 MPa', () => {
    const mockTrendData = {
      scope: {
        mode: 'RETROSPECTIVE_BACKTEST' as const,
        active_model_id: 'baselineridge-ca125dcf',
        active_model_name: 'Production Baseline Ridge (28-day)',
        sample_count: 2,
        total_available_batches: 1898,
        tested_28d_batches: 1324,
        historical_observations: 1165,
        valid_backtest_pairs: 3,
        data_completeness_pct: 0.23,
        status: 'VALIDATED_BACKTEST',
        warning: 'Limited data',
      },
      items: [
        {
          index: 1,
          batch_id: 'B1',
          tested_date: '2026-03-01',
          actual_mpa: 51.3,
          predicted_mpa: 51.3,
          residual_mpa: 0.0,
          abs_error_mpa: 0.0,
          rolling_mae_mpa: 0.0,
          is_outlier: false,
        },
        {
          index: 2,
          batch_id: 'B2',
          tested_date: '2026-03-02',
          actual_mpa: 48.0,
          predicted_mpa: 50.0,
          residual_mpa: 2.0,
          abs_error_mpa: 2.0,
          rolling_mae_mpa: 1.0,
          is_outlier: false,
        },
      ],
      operational_monitoring_threshold_mpa: 3.0,
      rolling_window_size: 10,
      total_items: 2,
      threshold_description: 'Operational monitoring threshold',
    };

    render(<PredictionErrorTrend data={mockTrendData as any} />);
    expect(screen.getByText('Prediction Error & Residual Trend')).toBeInTheDocument();
    expect(screen.getByText(/Operational Monitoring Threshold/i)).toBeInTheDocument();
  });
});

describe('WS-DASH-4B: Model Feature Importance', () => {
  test('renders feature importance bars with domain labels and engineering units', () => {
    const mockFeatureData = {
      model_id: 'baselineridge-ca125dcf',
      model_version: 'baselineridge-ca125dcf',
      model_name: 'Production Baseline Ridge (28-day)',
      algorithm: 'Ridge',
      feature_importance_available: true,
      status_code: 200,
      message: 'Feature importance loaded',
      features: [
        { feature_name: 'cement_kg_m3', display_name: 'Cement Content', importance_weight: 0.35, unit: 'kg/m³', rank: 1, is_active: true },
        { feature_name: 'water_binder_ratio', display_name: 'Water-to-Binder Ratio (W/B)', importance_weight: 0.42, unit: 'ratio', rank: 2, is_active: true },
        { feature_name: 'curing_age_days', display_name: 'Curing Age', importance_weight: 0.28, unit: 'days', rank: 3, is_active: true },
      ],
    };

    render(<ModelFeatureImportance data={mockFeatureData as any} />);
    expect(screen.getByText('Model Feature Importance')).toBeInTheDocument();
    expect(screen.getByText('Cement Content')).toBeInTheDocument();
    expect(screen.getByText('Water-to-Binder Ratio (W/B)')).toBeInTheDocument();
    expect(screen.getByText('Curing Age')).toBeInTheDocument();
  });
});

describe('WS-DASH-4B: Model Information & Coverage Funnel Panel', () => {
  test('renders active model metadata and 5-stage population funnel correctly', () => {
    const mockRegistryData = {
      models: [
        {
          model_registry_id: 1,
          model_version: 'baselineridge-ca125dcf',
          model_name: 'Production Baseline Ridge (28-day)',
          algorithm: 'Ridge Regression',
          framework: 'scikit-learn',
          target_variable: 'actual_strength_28d_mpa',
          is_active: true,
          deployment_status: 'ACTIVE',
          training_timestamp: '2026-03-01T00:00:00Z',
          deployment_timestamp: '2026-03-01T00:00:00Z',
          feature_schema_version: 'v1.0.0',
          feature_count: 12,
          notes: 'IS 456 / IS 10262 calibrated baseline model',
        },
      ],
      total_models: 1,
    };

    const mockScope = {
      mode: 'RETROSPECTIVE_BACKTEST' as const,
      active_model_id: 'baselineridge-ca125dcf',
      active_model_name: 'Production Baseline Ridge (28-day)',
      sample_count: 3,
      total_available_batches: 1898,
      tested_28d_batches: 1324,
      historical_observations: 1165,
      valid_backtest_pairs: 3,
      data_completeness_pct: 0.23,
      status: 'VALIDATED_BACKTEST',
      warning: '3 evaluation pairs — Insufficient sample size for reliable model validation.',
    };

    render(<ModelInformationPanel registryData={mockRegistryData as any} scope={mockScope as any} />);
    expect(screen.getByText('Model Registry & Deployment Information')).toBeInTheDocument();
    expect(screen.getByText(/Ridge Regression/i)).toBeInTheDocument();
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    expect(screen.getByText(/Historical Population & Evaluation Coverage Funnel/i)).toBeInTheDocument();
    expect(screen.getByText(/12 Canonical Features/i)).toBeInTheDocument();
    expect(screen.getByText(/Authoritative Lineage Synced/i)).toBeInTheDocument();
  });
});

describe('WS-DASH-4B: ModelMonitoringSection End-to-End Container', () => {
  const mockSummary = {
    scope: {
      mode: 'PRODUCTION_STORED' as const,
      active_model_id: 'baselineridge-ca125dcf',
      active_model_name: 'Production Baseline Ridge (28-day)',
      sample_count: 0,
      total_available_batches: 1898,
      tested_28d_batches: 1324,
      historical_observations: 1165,
      valid_backtest_pairs: 3,
      data_completeness_pct: 0,
      status: 'NO_STORED_PREDICTIONS_IN_RANGE',
      warning: 'No production predictions currently stored in database.',
    },
    metrics: {
      mae_mpa: null,
      rmse_mpa: null,
      r2_score: null,
      mean_residual_mpa: null,
      residual_std_dev_mpa: null,
      sample_count: 0,
    },
    status: 'NO_STORED_PREDICTIONS_IN_RANGE',
  };

  const mockActualVsPredicted = {
    scope: mockSummary.scope,
    items: [],
    summary_metrics: mockSummary.metrics,
  };

  const mockTrend = {
    scope: mockSummary.scope,
    items: [],
    operational_monitoring_threshold_mpa: 3.0,
    rolling_window_size: 10,
  };

  const mockFeatures = {
    model_id: 'baselineridge-ca125dcf',
    model_name: 'Production Baseline Ridge (28-day)',
    algorithm: 'Ridge',
    feature_importance_available: true,
    features: [
      { feature_name: 'cement_kg_m3', display_name: 'Cement Content', importance_weight: 0.35, unit: 'kg/m³', rank: 1, is_active: true },
    ],
  };

  const mockMetadata = {
    models: [
      {
        model_version: 'baselineridge-ca125dcf',
        model_name: 'Production Baseline Ridge (28-day)',
        algorithm: 'Ridge Regression',
        framework: 'scikit-learn',
        target_variable: 'actual_strength_28d_mpa',
        is_active: true,
        deployment_status: 'ACTIVE',
        training_timestamp: '2026-03-01T00:00:00Z',
        feature_count: 12,
        notes: 'IS 456 calibrated baseline model',
      },
    ],
    total_models: 1,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (reportingService.fetchPredictionSummary as any).mockResolvedValue(mockSummary);
    (reportingService.fetchActualVsPredicted as any).mockResolvedValue(mockActualVsPredicted);
    (reportingService.fetchPredictionErrorTrend as any).mockResolvedValue(mockTrend);
    (reportingService.fetchModelFeatures as any).mockResolvedValue(mockFeatures);
    (reportingService.fetchModelMetadata as any).mockResolvedValue(mockMetadata);
    (reportingService.fetchModelBacktest as any).mockResolvedValue(mockSummary);
  });

  test('fetches data on mount and renders all subcomponents accurately', async () => {
    render(<ModelMonitoringSection filters={{}} />);

    await waitFor(() => {
      expect(screen.getByText('Strength Prediction Validation & Model Monitoring')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByTestId('kpi-sample-count')).toHaveTextContent('0 batches');
    });
  });
});
