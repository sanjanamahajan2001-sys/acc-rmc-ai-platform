import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RecommendationGovernanceGate } from '../components/dashboard/optimization/RecommendationGovernanceGate';
import {
  optimizationService,
  RunGovernanceResponseDTO,
  CandidateGovernanceItemDTO,
} from '../services/optimizationService';

vi.mock('../services/optimizationService', () => ({
  optimizationService: {
    getRunGovernance: vi.fn(),
    reviewCandidate: vi.fn(),
  },
}));

describe('RecommendationGovernanceGate Component (Phase 5E)', () => {
  const mockEligibleCandidate: CandidateGovernanceItemDTO = {
    candidate_id: 'cand-001-uuid',
    candidate_identifier: 'CAND-01',
    is_feasible: true,
    is_pareto_optimal: true,
    predicted_strength_mpa: 42.50,
    target_mean_strength_mpa: 38.25,
    characteristic_strength_fck_mpa: 30.0,
    strength_margin_mpa: 4.25,
    binder_intensity_kg_m3: 325.0,
    water_binder_ratio: 0.45,
    yield_m3: 1.000,
    cost_status: 'NOT_CONFIGURED',
    cost_per_m3: null,
    cost_delta_per_m3: null,
    cost_delta_percent: null,
    eligibility_status: 'ELIGIBLE_FOR_HUMAN_REVIEW',
    eligibility_reason_code: 'ELIGIBLE_FOR_HUMAN_REVIEW',
    eligibility_reason_description: 'Candidate satisfies all engineering constraints and lies on the Pareto-optimal frontier.',
    review_status: 'PENDING_REVIEW',
    reviewed_by_user_id: null,
    reviewed_by_username: null,
    reviewed_at: null,
    review_decision_reason: null,
    review_comments: null,
    model_lineage_description: 'ACC Multi-Task Gradient Boosted Regressor (Ver: 3.4.2)',
    allowed_actions: ['ACCEPT', 'REJECT', 'RESET'],
  };

  const mockInfeasibleCandidate: CandidateGovernanceItemDTO = {
    candidate_id: 'cand-002-uuid',
    candidate_identifier: 'CAND-INF',
    is_feasible: false,
    is_pareto_optimal: false,
    predicted_strength_mpa: 35.00,
    target_mean_strength_mpa: 38.25,
    characteristic_strength_fck_mpa: 30.0,
    strength_margin_mpa: -3.25,
    binder_intensity_kg_m3: 280.0,
    water_binder_ratio: 0.55,
    yield_m3: 0.985,
    cost_status: 'NOT_CONFIGURED',
    cost_per_m3: null,
    cost_delta_per_m3: null,
    cost_delta_percent: null,
    eligibility_status: 'NOT_ELIGIBLE_INFEASIBLE',
    eligibility_reason_code: 'INFEASIBLE_CANDIDATE',
    eligibility_reason_description: 'Candidate violates physical volume or IS standard engineering constraints. Quarantined for diagnostic inspection only.',
    review_status: 'PENDING_REVIEW',
    reviewed_by_user_id: null,
    reviewed_by_username: null,
    reviewed_at: null,
    review_decision_reason: null,
    review_comments: null,
    model_lineage_description: 'ACC Multi-Task Gradient Boosted Regressor (Ver: 3.4.2)',
    allowed_actions: [],
  };

  const mockRunGovernance: RunGovernanceResponseDTO = {
    run_id: 'run-uuid-1234',
    recipe_code: 'M-30-STD',
    grade: 'M30',
    plant_code: 'PLANT-KUDL-01',
    run_status: 'SUCCESS',
    total_candidates: 2,
    feasible_candidates_count: 1,
    pareto_optimal_count: 1,
    eligible_for_review_count: 1,
    reviewed_accepted_count: 0,
    reviewed_rejected_count: 0,
    has_feasible_candidates: true,
    governance_message: '1 candidate(s) are eligible for human engineering review. Production activation is outside the current phase.',
    cost_status: 'NOT_CONFIGURED',
    price_source_description: 'Pricing Source: Not Configured',
    user_can_review: true,
    user_role: 'QUALITY_HEAD',
    production_activation_status: 'PRODUCTION_ACTIVATION_OUTSIDE_CURRENT_PHASE',
    candidates: [mockEligibleCandidate, mockInfeasibleCandidate],
    evaluated_at: '2026-09-18T12:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders recommendation governance header, eligibility status, and disclaimers', async () => {
    vi.mocked(optimizationService.getRunGovernance).mockResolvedValue(mockRunGovernance);

    render(<RecommendationGovernanceGate runId="run-uuid-1234" selectedCandidateId="cand-001-uuid" />);

    await waitFor(() => {
      expect(screen.getByText('Recommendation Governance & Human Review Gate')).toBeInTheDocument();
    });

    expect(screen.getByText(/Role: QUALITY_HEAD \(Authorized Human Reviewer\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Production activation is outside the current phase/i)).toBeInTheDocument();
    expect(screen.getByText('FEASIBLE')).toBeInTheDocument();
    expect(screen.getByText('PARETO OPTIMAL')).toBeInTheDocument();
    expect(screen.getByText('HUMAN REVIEW: PENDING')).toBeInTheDocument();
    expect(screen.getByText('Accept Candidate')).toBeInTheDocument();
    expect(screen.getByText('Reject Candidate')).toBeInTheDocument();
  });

  it('quarantines infeasible candidate and blocks human approval actions', async () => {
    vi.mocked(optimizationService.getRunGovernance).mockResolvedValue(mockRunGovernance);

    render(<RecommendationGovernanceGate runId="run-uuid-1234" selectedCandidateId="cand-002-uuid" />);

    await waitFor(() => {
      expect(screen.getByText('CAND-INF')).toBeInTheDocument();
    });

    expect(screen.getByText('INFEASIBLE')).toBeInTheDocument();
    expect(screen.getAllByText(/Quarantined for diagnostic inspection only/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText('Accept Candidate')).not.toBeInTheDocument();
    expect(screen.queryByText('Reject Candidate')).not.toBeInTheDocument();
  });

  it('handles zero feasible candidates without generating fallback or fake recommendations', async () => {
    const mockZeroFeasible: RunGovernanceResponseDTO = {
      ...mockRunGovernance,
      total_candidates: 1,
      feasible_candidates_count: 0,
      pareto_optimal_count: 0,
      eligible_for_review_count: 0,
      has_feasible_candidates: false,
      governance_message: 'No feasible candidate is currently available for human review.',
      candidates: [mockInfeasibleCandidate],
    };
    vi.mocked(optimizationService.getRunGovernance).mockResolvedValue(mockZeroFeasible);

    render(<RecommendationGovernanceGate runId="run-uuid-1234" />);

    await waitFor(() => {
      expect(screen.getByText(/No Feasible Candidate Available:/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/No recommendation can be submitted for human review/i)).toBeInTheDocument();
  });

  it('records human review decision when authorized user submits acceptance modal', async () => {
    vi.mocked(optimizationService.getRunGovernance).mockResolvedValue(mockRunGovernance);
    vi.mocked(optimizationService.reviewCandidate).mockResolvedValue({
      ...mockEligibleCandidate,
      review_status: 'ACCEPTED',
      reviewed_by_username: 'quality_head_user',
      reviewed_at: '2026-09-18T12:05:00Z',
      review_decision_reason: 'TECHNICAL_VALIDATION_CONFIRMED',
    });

    render(<RecommendationGovernanceGate runId="run-uuid-1234" selectedCandidateId="cand-001-uuid" />);

    await waitFor(() => {
      expect(screen.getByText('Accept Candidate')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Accept Candidate'));

    expect(screen.getByText(/Confirm Acceptance of CAND-01/i)).toBeInTheDocument();

    const confirmBtn = screen.getByText('Confirm Accept');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(optimizationService.reviewCandidate).toHaveBeenCalledWith(
        'run-uuid-1234',
        'cand-001-uuid',
        expect.objectContaining({
          action: 'ACCEPT',
          reason_code: 'TECHNICAL_VALIDATION_CONFIRMED',
        })
      );
    });
  });
});
