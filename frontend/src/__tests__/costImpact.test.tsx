import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { CostImpactComparison } from '../components/dashboard/optimization/CostImpactComparison';
import { optimizationService, CostImpactResponseDTO } from '../services/optimizationService';

vi.mock('../services/optimizationService');

describe('CostImpactComparison Component (Clean Enterprise UI)', () => {
  const mockCostDataConfigured: CostImpactResponseDTO = {
    run_id: 'run-uuid-1234',
    candidate_id: 'cand-uuid-5678',
    candidate_identifier: 'CAND-01',
    recipe_code: 'M-30-STD',
    grade: 'M30',
    plant_code: 'PLANT-01',
    is_feasible: true,
    price_source_description: 'Pricing Source: PROCUREMENT_ERP_FEED',
    pricing_snapshot_id: 'SNAP-2026-Q3-001',
    pricing_version: '2026-Q3-V1',
    effective_date: '2026-07-01T00:00:00Z',
    calculated_at: '2026-09-18T10:00:00Z',
    cost_summary: {
      cost_status: 'CONFIGURED',
      total_cost_available: true,
      currency: 'INR',
      master_cost_per_m3: 3850.50,
      candidate_cost_per_m3: 3620.25,
      cost_delta_per_m3: -230.25,
      cost_delta_percent: -5.98,
      unpriced_materials: [],
      missing_price_constituents: [],
      production_impact: {
        is_configured: true,
        volume_source: 'PLANT_CAPACITY_SCHEDULE',
        volume_period: 'MULTI_PERIOD',
        volume_basis: 'DISPATCH_SCHEDULE',
        daily_volume_m3: 250.0,
        monthly_volume_m3: 6500.0,
        annualized_volume_m3: 78000.0,
        daily_cost_delta: -57562.50,
        monthly_cost_delta: -1496625.00,
        annualized_cost_delta: -17959500.00,
        currency: 'INR',
      },
    },
    material_impacts: [
      {
        material_id: 'mat-cem-1',
        material_code: 'OPC-53',
        material_name: 'UltraTech OPC 53',
        category_code: 'CEMENT',
        master_quantity_kg_m3: 350.0,
        candidate_quantity_kg_m3: 320.0,
        quantity_delta_kg_m3: -30.0,
        unit_price_per_kg: 6.50,
        price_unit_display: '₹/kg',
        currency: 'INR',
        master_cost_per_m3: 2275.0,
        candidate_cost_per_m3: 2080.0,
        cost_delta_per_m3: -195.0,
        cost_delta_percent: -8.57,
        price_provenance: {
          snapshot_id: 'SNAP-2026-Q3-001',
          material_id: 'mat-cem-1',
          material_code: 'OPC-53',
          unit_price: 6.50,
          price_unit: '₹/kg',
          currency: 'INR',
          price_source: 'PROCUREMENT_ERP_FEED',
          price_version: '2026-Q3-V1',
          effective_from: '2026-07-01T00:00:00Z',
          effective_to: null,
          plant_code: 'PLANT-01',
          conversion_status: 'EXACT',
          is_available: true,
        },
        status_label: 'NORMAL',
      },
    ],
  };

  const mockCostDataUnconfigured: CostImpactResponseDTO = {
    run_id: 'run-uuid-1234',
    candidate_id: 'cand-uuid-5678',
    candidate_identifier: 'CAND-01',
    recipe_code: 'M-30-STD',
    grade: 'M30',
    plant_code: 'PLANT-01',
    is_feasible: true,
    price_source_description: 'Pricing Source: Not Configured',
    pricing_snapshot_id: null,
    pricing_version: null,
    effective_date: null,
    calculated_at: '2026-09-18T10:00:00Z',
    cost_summary: {
      cost_status: 'NOT_CONFIGURED',
      total_cost_available: false,
      currency: 'INR',
      master_cost_per_m3: null,
      candidate_cost_per_m3: null,
      cost_delta_per_m3: null,
      cost_delta_percent: null,
      unpriced_materials: ['UltraTech OPC 53', 'Fly Ash Grade 1'],
      missing_price_constituents: ['UltraTech OPC 53', 'Fly Ash Grade 1'],
      production_impact: {
        is_configured: false,
        volume_source: null,
        volume_period: null,
        volume_basis: null,
        daily_volume_m3: null,
        monthly_volume_m3: null,
        annualized_volume_m3: null,
        daily_cost_delta: null,
        monthly_cost_delta: null,
        annualized_cost_delta: null,
        currency: 'INR',
      },
    },
    material_impacts: [
      {
        material_id: 'mat-cem-1',
        material_code: 'OPC-53',
        material_name: 'UltraTech OPC 53',
        category_code: 'CEMENT',
        master_quantity_kg_m3: 350.0,
        candidate_quantity_kg_m3: 320.0,
        quantity_delta_kg_m3: -30.0,
        unit_price_per_kg: null,
        price_unit_display: '₹/kg',
        currency: 'INR',
        master_cost_per_m3: null,
        candidate_cost_per_m3: null,
        cost_delta_per_m3: null,
        cost_delta_percent: null,
        price_provenance: {
          material_id: 'mat-cem-1',
          material_code: 'OPC-53',
          unit_price: null,
          price_unit: '₹/kg',
          currency: 'INR',
          price_source: 'NOT_CONFIGURED',
          price_version: null,
          effective_from: null,
          effective_to: null,
          conversion_status: 'UNPRICED',
          is_available: false,
        },
        status_label: 'UNPRICED',
      },
    ],
  };

  const mockCostDataPartiallyConfigured: CostImpactResponseDTO = {
    run_id: 'run-uuid-1234',
    candidate_id: 'cand-uuid-5678',
    candidate_identifier: 'CAND-01',
    recipe_code: 'M-30-STD',
    grade: 'M30',
    plant_code: 'PLANT-01',
    is_feasible: true,
    price_source_description: 'Pricing Source: PROCUREMENT_ERP_FEED (Partial)',
    pricing_snapshot_id: 'SNAP-2026-Q3-001',
    pricing_version: '2026-Q3-V1',
    effective_date: '2026-07-01T00:00:00Z',
    calculated_at: '2026-09-18T10:00:00Z',
    cost_summary: {
      cost_status: 'PARTIALLY_CONFIGURED',
      total_cost_available: false,
      currency: 'INR',
      master_cost_per_m3: null,
      candidate_cost_per_m3: null,
      cost_delta_per_m3: null,
      cost_delta_percent: null,
      unpriced_materials: ['Fly Ash Grade 1'],
      missing_price_constituents: ['Fly Ash Grade 1'],
      production_impact: {
        is_configured: false,
        volume_source: null,
        daily_volume_m3: null,
        monthly_volume_m3: null,
        annualized_volume_m3: null,
        daily_cost_delta: null,
        monthly_cost_delta: null,
        annualized_cost_delta: null,
        currency: 'INR',
      },
    },
    material_impacts: [
      {
        material_id: 'mat-cem-1',
        material_code: 'OPC-53',
        material_name: 'UltraTech OPC 53',
        category_code: 'CEMENT',
        master_quantity_kg_m3: 350.0,
        candidate_quantity_kg_m3: 320.0,
        quantity_delta_kg_m3: -30.0,
        unit_price_per_kg: 6.50,
        price_unit_display: '₹/kg',
        currency: 'INR',
        master_cost_per_m3: 2275.0,
        candidate_cost_per_m3: 2080.0,
        cost_delta_per_m3: -195.0,
        cost_delta_percent: -8.57,
        price_provenance: {
          material_id: 'mat-cem-1',
          material_code: 'OPC-53',
          unit_price: 6.50,
          price_unit: '₹/kg',
          currency: 'INR',
          price_source: 'PROCUREMENT_ERP_FEED',
          price_version: '2026-Q3-V1',
          effective_from: null,
          effective_to: null,
          is_available: true,
        },
        status_label: 'NORMAL',
      },
      {
        material_id: 'mat-fa-1',
        material_code: 'FA-G1',
        material_name: 'Fly Ash Grade 1',
        category_code: 'FLY_ASH',
        master_quantity_kg_m3: 50.0,
        candidate_quantity_kg_m3: 80.0,
        quantity_delta_kg_m3: 30.0,
        unit_price_per_kg: null,
        price_unit_display: '₹/kg',
        currency: 'INR',
        master_cost_per_m3: null,
        candidate_cost_per_m3: null,
        cost_delta_per_m3: null,
        cost_delta_percent: null,
        price_provenance: {
          material_id: 'mat-fa-1',
          material_code: 'FA-G1',
          unit_price: null,
          price_unit: '₹/kg',
          currency: 'INR',
          price_source: 'NOT_CONFIGURED',
          price_version: null,
          effective_from: null,
          effective_to: null,
          is_available: false,
        },
        status_label: 'UNPRICED',
      },
    ],
  };

  const mockCostDataInfeasible: CostImpactResponseDTO = {
    ...mockCostDataConfigured,
    is_feasible: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders fully configured commercial feasibility metrics, provenance, and production volume impacts', async () => {
    vi.mocked(optimizationService.getCandidateCostImpact).mockResolvedValue(mockCostDataConfigured);

    render(
      <CostImpactComparison
        runId="run-uuid-1234"
        candidateId="cand-uuid-5678"
        candidateIdentifier="CAND-01"
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Cost & Commercial Feasibility Analysis/i)).toBeInTheDocument();
    });

    // Ensure no internal Phase D label in user-facing UI
    expect(screen.queryByText(/Phase 5D/i)).not.toBeInTheDocument();

    expect(screen.getByText('CONFIGURED')).toBeInTheDocument();
    expect(screen.getByText('₹ 3,850.50')).toBeInTheDocument();
    expect(screen.getByText('₹ 3,620.25')).toBeInTheDocument();
    expect(screen.getByText('- ₹ 230.25')).toBeInTheDocument();
    expect(screen.getByText(/-5.98% vs Master/i)).toBeInTheDocument();

    // Provenance details
    expect(screen.getByText(/PROCUREMENT_ERP_FEED/)).toBeInTheDocument();
    expect(screen.getByText(/ID: SNAP-2026-Q3-001/)).toBeInTheDocument();
    expect(screen.getByText(/• Ver: 2026-Q3-V1/)).toBeInTheDocument();

    // Production volume section
    expect(screen.getByText(/Production Volume Financial Impact/i)).toBeInTheDocument();
    expect(screen.getByText(/Daily Impact \(250 m³\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Monthly Impact \(6,500 m³\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Annualized Impact \(78,000 m³\)/i)).toBeInTheDocument();

    // Table itemized
    expect(screen.getByText('UltraTech OPC 53')).toBeInTheDocument();
    expect(screen.getByText('₹ 2275.00')).toBeInTheDocument();
    expect(screen.getByText('₹ 2080.00')).toBeInTheDocument();
  });

  it('renders safe unconfigured state with Pricing Source: Not Configured and no fake numbers', async () => {
    vi.mocked(optimizationService.getCandidateCostImpact).mockResolvedValue(mockCostDataUnconfigured);

    render(
      <CostImpactComparison
        runId="run-uuid-1234"
        candidateId="cand-uuid-5678"
        candidateIdentifier="CAND-01"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('NOT_CONFIGURED')).toBeInTheDocument();
    });

    expect(screen.getByText('Pricing Source: Not Configured')).toBeInTheDocument();
    expect(screen.getByText(/Cost Not Configured:/i)).toBeInTheDocument();
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText(/Production volume parameters \(daily, monthly, annual m³\) have not been configured/i)).toBeInTheDocument();
  });

  it('renders partially configured state with unpriced constituents list and suppresses totals', async () => {
    vi.mocked(optimizationService.getCandidateCostImpact).mockResolvedValue(mockCostDataPartiallyConfigured);

    render(
      <CostImpactComparison
        runId="run-uuid-1234"
        candidateId="cand-uuid-5678"
        candidateIdentifier="CAND-01"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('PARTIALLY_CONFIGURED')).toBeInTheDocument();
    });

    expect(screen.getByText(/Incomplete Pricing Snapshot:/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Fly Ash Grade 1/i).length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(3);
  });

  it('renders infeasible candidate badge and retains Cost Delta label (no fabricated savings)', async () => {
    vi.mocked(optimizationService.getCandidateCostImpact).mockResolvedValue(mockCostDataInfeasible);

    render(
      <CostImpactComparison
        runId="run-uuid-1234"
        candidateId="cand-uuid-5678"
        candidateIdentifier="CAND-01"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('INFEASIBLE — DIAGNOSTIC COMPARISON ONLY')).toBeInTheDocument();
    });

    expect(screen.getByText('Cost Delta / m³')).toBeInTheDocument();
    expect(screen.queryByText('Savings')).not.toBeInTheDocument();
  });
});
