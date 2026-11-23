import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Info,
  Scale,
  UserCheck,
  FileCheck,
  Building2,
  Clock,
  Layers,
  Sparkles,
  Lock,
} from 'lucide-react';
import {
  optimizationService,
  RunGovernanceResponseDTO,
  CandidateGovernanceItemDTO,
  CandidateReviewActionRequestDTO,
} from '../../../services/optimizationService';

interface RecommendationGovernanceGateProps {
  runId: string;
  selectedCandidateId?: string;
  candidateIdentifier?: string;
}

const tokens = {
  cardBg: '#ffffff',
  surfaceSecondary: '#f8fafc',
  surfaceHighlight: '#f1f5f9',
  border: '#e2e8f0',
  borderLight: '#edf2f7',
  textPrimary: '#0f172a',
  textSecondary: '#475569',
  textMuted: '#64748b',
  primaryAccent: '#0284c7',
  primaryAccentLight: '#e0f2fe',
  primaryAccentBorder: '#bae6fd',
  successGreen: '#16a34a',
  successGreenLight: '#dcfce7',
  successGreenBorder: '#bbf7d0',
  dangerRed: '#dc2626',
  dangerRedLight: '#fee2e2',
  dangerRedBorder: '#fecaca',
  warningAmber: '#d97706',
  warningAmberLight: '#fef3c7',
  warningAmberBorder: '#fde68a',
  purpleAccent: '#7c3aed',
  purpleAccentLight: '#f5f3ff',
  purpleAccentBorder: '#ddd6fe',
  fontMono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  radius: '8px',
};

const REVIEW_REASONS = [
  { code: 'TECHNICAL_VALIDATION_CONFIRMED', label: 'Technical Validation Confirmed (IS Standards Satisfied)' },
  { code: 'LAB_TRIAL_REQUIRED', label: 'Approved for Secondary QC Laboratory Trial Batch' },
  { code: 'SAFETY_MARGIN_ACCEPTABLE', label: 'Strength Safety Margin Acceptable for Plant Dispatch' },
  { code: 'PLANT_RAW_MATERIAL_CONSTRAINTS', label: 'Rejected: Local Silo / Raw Material Inventory Constraint' },
  { code: 'HIGH_BINDER_INTENSITY', label: 'Rejected: Excess Binder Content / Unfavorable Efficiency' },
  { code: 'OTHER', label: 'Other Engineering / Operational Rationale' },
];

export const RecommendationGovernanceGate: React.FC<RecommendationGovernanceGateProps> = ({
  runId,
  selectedCandidateId,
  candidateIdentifier,
}) => {
  const [governanceData, setGovernanceData] = useState<RunGovernanceResponseDTO | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Review Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [pendingAction, setPendingAction] = useState<'ACCEPT' | 'REJECT' | null>(null);
  const [selectedReason, setSelectedReason] = useState<string>(REVIEW_REASONS[0].code);
  const [reviewComments, setReviewComments] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const fetchGovernance = async () => {
    if (!runId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await optimizationService.getRunGovernance(runId);
      setGovernanceData(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load recommendation governance data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGovernance();
  }, [runId]);

  if (isLoading) {
    return (
      <div
        style={{
          marginTop: '20px',
          padding: '24px',
          border: `1px solid ${tokens.border}`,
          borderRadius: tokens.radius,
          backgroundColor: tokens.surfaceSecondary,
          textAlign: 'center',
          color: tokens.textSecondary,
          fontSize: '0.85rem',
        }}
      >
        <RotateCcw size={16} className="animate-spin" style={{ display: 'inline', marginRight: '8px', color: tokens.primaryAccent }} />
        Evaluating recommendation governance & human review gates...
      </div>
    );
  }

  if (error || !governanceData) {
    return (
      <div
        style={{
          marginTop: '20px',
          padding: '16px',
          border: `1px solid ${tokens.dangerRedBorder}`,
          borderRadius: tokens.radius,
          backgroundColor: tokens.dangerRedLight,
          color: tokens.dangerRed,
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <ShieldAlert size={18} />
        <span>{error || 'Unable to load recommendation governance.'}</span>
      </div>
    );
  }

  // Active candidate selection
  const activeCandidate = governanceData.candidates.find(
    (c) => c.candidate_id === selectedCandidateId || c.candidate_identifier === candidateIdentifier
  ) || governanceData.candidates[0] || null;

  const handleOpenReviewModal = (action: 'ACCEPT' | 'REJECT') => {
    setPendingAction(action);
    setSelectedReason(REVIEW_REASONS[0].code);
    setReviewComments('');
    setIsModalOpen(true);
  };

  const handleResetReview = async () => {
    if (!activeCandidate) return;
    setIsSubmitting(true);
    try {
      await optimizationService.reviewCandidate(runId, activeCandidate.candidate_id, {
        action: 'RESET',
        reason_code: 'RESET_BY_USER',
      });
      await fetchGovernance();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to reset review state.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmReview = async () => {
    if (!activeCandidate || !pendingAction) return;
    setIsSubmitting(true);
    try {
      await optimizationService.reviewCandidate(runId, activeCandidate.candidate_id, {
        action: pendingAction,
        reason_code: selectedReason,
        comments: reviewComments.trim() || undefined,
      });
      setIsModalOpen(false);
      await fetchGovernance();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to submit human review decision.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        marginTop: '20px',
        border: `1px solid ${tokens.border}`,
        borderRadius: tokens.radius,
        backgroundColor: tokens.cardBg,
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        overflow: 'hidden',
      }}
    >
      {/* Header Bar */}
      <div
        style={{
          padding: '14px 18px',
          backgroundColor: '#f8fafc',
          borderBottom: `1px solid ${tokens.border}`,
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              backgroundColor: tokens.purpleAccentLight,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: tokens.purpleAccent,
              flexShrink: 0,
            }}
          >
            <ShieldCheck size={18} />
          </div>
          <div>
            <div style={{ fontSize: '0.92rem', fontWeight: 700, color: tokens.textPrimary, display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span>Recommendation Governance & Human Review Gate</span>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontFamily: tokens.fontMono,
                  whiteSpace: 'nowrap',
                  backgroundColor: governanceData.user_can_review ? tokens.successGreenLight : tokens.surfaceHighlight,
                  color: governanceData.user_can_review ? tokens.successGreen : tokens.textSecondary,
                  border: `1px solid ${governanceData.user_can_review ? tokens.successGreenBorder : tokens.border}`,
                }}
              >
                Role: {governanceData.user_role} ({governanceData.user_can_review ? 'Authorized Human Reviewer' : 'Read-Only'})
              </span>
            </div>
            <div style={{ fontSize: '0.70rem', color: tokens.textMuted, marginTop: '2px' }}>
              Authorized roles: Quality Head, Quality Engineer, Plant Manager, Admin, Super Admin
            </div>
            <div style={{ fontSize: '0.72rem', color: tokens.textMuted, marginTop: '2px' }}>
              Target: <strong style={{ color: tokens.textSecondary }}>{governanceData.recipe_code} ({governanceData.grade})</strong> | Plant: <strong style={{ color: tokens.textSecondary }}>{governanceData.plant_code}</strong> | Status: <strong style={{ color: tokens.textSecondary }}>{governanceData.run_status}</strong>
            </div>
          </div>
        </div>

        {/* Governance State Counts */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <div style={{ fontSize: '0.72rem', color: tokens.textMuted }}>
            Eligible: <strong style={{ color: tokens.successGreen }}>{governanceData.eligible_for_review_count}</strong> / {governanceData.total_candidates}
          </div>
          {governanceData.reviewed_accepted_count > 0 && (
            <span style={{ fontSize: '0.68rem', padding: '1px 6px', borderRadius: '4px', backgroundColor: tokens.successGreenLight, color: tokens.successGreen, fontWeight: 700 }}>
              {governanceData.reviewed_accepted_count} Accepted
            </span>
          )}
          {governanceData.reviewed_rejected_count > 0 && (
            <span style={{ fontSize: '0.68rem', padding: '1px 6px', borderRadius: '4px', backgroundColor: tokens.dangerRedLight, color: tokens.dangerRed, fontWeight: 700 }}>
              {governanceData.reviewed_rejected_count} Rejected
            </span>
          )}
        </div>
      </div>

      {/* Governance Policy Notice Banner */}
      <div
        style={{
          padding: '10px 18px',
          backgroundColor: '#eff6ff',
          borderBottom: '1px solid #dbeafe',
          fontSize: '0.78rem',
          color: '#1e40af',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <Info size={16} style={{ flexShrink: 0 }} />
        <span>
          <strong>Governance Gate:</strong> {governanceData.governance_message}
        </span>
      </div>

      {/* Zero Feasible Candidates Notice (if applicable) */}
      {!governanceData.has_feasible_candidates && (
        <div
          style={{
            margin: '18px',
            padding: '16px',
            borderRadius: '6px',
            backgroundColor: tokens.warningAmberLight,
            border: `1px solid ${tokens.warningAmberBorder}`,
            color: tokens.warningAmber,
            fontSize: '0.82rem',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <AlertTriangle size={20} style={{ flexShrink: 0 }} />
          <div>
            <strong>No Feasible Candidate Available:</strong> No candidate alternative in this run satisfied all physical volume and IS standard engineering constraints. No recommendation can be submitted for human review.
          </div>
        </div>
      )}

      {/* Active Candidate Governance Detail Card */}
      {activeCandidate && (
        <div style={{ padding: '18px' }}>
          <div
            style={{
              borderRadius: '6px',
              border: `1px solid ${
                activeCandidate.review_status === 'ACCEPTED'
                  ? tokens.successGreenBorder
                  : activeCandidate.review_status === 'REJECTED'
                  ? tokens.dangerRedBorder
                  : !activeCandidate.is_feasible
                  ? tokens.dangerRedBorder
                  : tokens.border
              }`,
              backgroundColor: '#ffffff',
              overflow: 'hidden',
            }}
          >
            {/* Candidate Card Top Bar */}
            <div
              style={{
                padding: '12px 16px',
                backgroundColor: tokens.surfaceSecondary,
                borderBottom: `1px solid ${tokens.border}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.95rem', fontWeight: 800, color: tokens.textPrimary, fontFamily: tokens.fontMono }}>
                  {activeCandidate.candidate_identifier}
                </span>
                
                {/* Engineering Badges */}
                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: activeCandidate.is_feasible ? tokens.successGreenLight : tokens.dangerRedLight,
                    color: activeCandidate.is_feasible ? tokens.successGreen : tokens.dangerRed,
                    border: `1px solid ${activeCandidate.is_feasible ? tokens.successGreenBorder : tokens.dangerRedBorder}`,
                  }}
                >
                  {activeCandidate.is_feasible ? 'FEASIBLE' : 'INFEASIBLE'}
                </span>

                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: activeCandidate.is_pareto_optimal ? tokens.primaryAccentLight : tokens.surfaceHighlight,
                    color: activeCandidate.is_pareto_optimal ? tokens.primaryAccent : tokens.textSecondary,
                    border: `1px solid ${activeCandidate.is_pareto_optimal ? tokens.primaryAccentBorder : tokens.border}`,
                  }}
                >
                  {activeCandidate.is_pareto_optimal ? 'PARETO OPTIMAL' : 'NON-PARETO'}
                </span>

                {/* Review Status Badge */}
                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 800,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontFamily: tokens.fontMono,
                    backgroundColor:
                      activeCandidate.review_status === 'ACCEPTED'
                        ? tokens.successGreenLight
                        : activeCandidate.review_status === 'REJECTED'
                        ? tokens.dangerRedLight
                        : tokens.warningAmberLight,
                    color:
                      activeCandidate.review_status === 'ACCEPTED'
                        ? tokens.successGreen
                        : activeCandidate.review_status === 'REJECTED'
                        ? tokens.dangerRed
                        : tokens.warningAmber,
                    border: `1px solid ${
                      activeCandidate.review_status === 'ACCEPTED'
                        ? tokens.successGreenBorder
                        : activeCandidate.review_status === 'REJECTED'
                        ? tokens.dangerRedBorder
                        : tokens.warningAmberBorder
                    }`,
                  }}
                >
                  {activeCandidate.review_status === 'ACCEPTED'
                    ? 'HUMAN REVIEW: ACCEPTED'
                    : activeCandidate.review_status === 'REJECTED'
                    ? 'HUMAN REVIEW: REJECTED'
                    : 'HUMAN REVIEW: PENDING'}
                </span>
              </div>

              {/* Action Buttons for Authorized Users */}
              {activeCandidate.is_feasible && governanceData.user_can_review && (
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {activeCandidate.review_status !== 'ACCEPTED' && (
                    <button
                      onClick={() => handleOpenReviewModal('ACCEPT')}
                      disabled={isSubmitting}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '6px 14px',
                        borderRadius: '6px',
                        backgroundColor: tokens.successGreen,
                        color: '#ffffff',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        border: 'none',
                        cursor: 'pointer',
                      }}
                    >
                      <CheckCircle2 size={14} />
                      Accept Candidate
                    </button>
                  )}

                  {activeCandidate.review_status !== 'REJECTED' && (
                    <button
                      onClick={() => handleOpenReviewModal('REJECT')}
                      disabled={isSubmitting}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '6px 14px',
                        borderRadius: '6px',
                        backgroundColor: tokens.dangerRed,
                        color: '#ffffff',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        border: 'none',
                        cursor: 'pointer',
                      }}
                    >
                      <XCircle size={14} />
                      Reject Candidate
                    </button>
                  )}

                  {activeCandidate.review_status !== 'PENDING_REVIEW' && (
                    <button
                      onClick={handleResetReview}
                      disabled={isSubmitting}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        backgroundColor: tokens.surfaceHighlight,
                        color: tokens.textSecondary,
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        border: `1px solid ${tokens.border}`,
                        cursor: 'pointer',
                      }}
                    >
                      <RotateCcw size={13} />
                      Reset
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Candidate Content Body */}
            <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Engineering vs Governance Gating Explanation */}
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: '6px',
                  backgroundColor: !activeCandidate.is_feasible
                    ? tokens.dangerRedLight
                    : activeCandidate.is_pareto_optimal
                    ? tokens.purpleAccentLight
                    : tokens.surfaceSecondary,
                  border: `1px solid ${
                    !activeCandidate.is_feasible
                      ? tokens.dangerRedBorder
                      : activeCandidate.is_pareto_optimal
                      ? tokens.purpleAccentBorder
                      : tokens.border
                  }`,
                  fontSize: '0.78rem',
                  color: !activeCandidate.is_feasible
                    ? tokens.dangerRed
                    : activeCandidate.is_pareto_optimal
                    ? tokens.purpleAccent
                    : tokens.textSecondary,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px',
                }}
              >
                {!activeCandidate.is_feasible ? (
                  <ShieldAlert size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
                ) : (
                  <ShieldCheck size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
                )}
                <div>
                  <strong>Governance Assessment: </strong>
                  <span>{activeCandidate.eligibility_reason_description}</span>
                  {!activeCandidate.is_feasible && (
                    <div style={{ marginTop: '4px', fontWeight: 700 }}>
                      [INFEASIBLE] Quarantined for diagnostic inspection only. Human approval is strictly blocked.
                    </div>
                  )}
                </div>
              </div>

              {/* Engineering Facts Summary Grid */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: tokens.textMuted, textTransform: 'uppercase', marginBottom: '6px' }}>
                  Authoritative Persisted Metrics
                </div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
                    gap: '10px',
                  }}
                >
                  {/* Predicted Strength */}
                  <div style={{ padding: '10px', borderRadius: '6px', backgroundColor: tokens.surfaceSecondary, border: `1px solid ${tokens.border}` }}>
                    <div style={{ fontSize: '0.68rem', color: tokens.textMuted, fontWeight: 600, textTransform: 'uppercase' }}>
                      Predicted Strength (28d)
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: tokens.textPrimary, fontFamily: tokens.fontMono, marginTop: '2px' }}>
                      {activeCandidate.predicted_strength_mpa !== null ? `${activeCandidate.predicted_strength_mpa.toFixed(2)} MPa` : '—'}
                    </div>
                    <div style={{ fontSize: '0.68rem', color: (activeCandidate.strength_margin_mpa ?? 0) >= 0 ? tokens.successGreen : tokens.dangerRed, marginTop: '2px' }}>
                      Margin: {(activeCandidate.strength_margin_mpa ?? 0) >= 0 ? '+' : ''}
                      {activeCandidate.strength_margin_mpa?.toFixed(2) ?? '—'} MPa
                    </div>
                  </div>

                  {/* W/B Ratio */}
                  <div style={{ padding: '10px', borderRadius: '6px', backgroundColor: tokens.surfaceSecondary, border: `1px solid ${tokens.border}` }}>
                    <div style={{ fontSize: '0.68rem', color: tokens.textMuted, fontWeight: 600, textTransform: 'uppercase' }}>
                      Water / Binder Ratio
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: tokens.textPrimary, fontFamily: tokens.fontMono, marginTop: '2px' }}>
                      {activeCandidate.water_binder_ratio.toFixed(3)}
                    </div>
                    <div style={{ fontSize: '0.68rem', color: tokens.textMuted, marginTop: '2px' }}>
                      IS 456 Max Limit Validated
                    </div>
                  </div>

                  {/* Binder Content */}
                  <div style={{ padding: '10px', borderRadius: '6px', backgroundColor: tokens.surfaceSecondary, border: `1px solid ${tokens.border}` }}>
                    <div style={{ fontSize: '0.68rem', color: tokens.textMuted, fontWeight: 600, textTransform: 'uppercase' }}>
                      Binder Intensity
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: tokens.textPrimary, fontFamily: tokens.fontMono, marginTop: '2px' }}>
                      {activeCandidate.binder_intensity_kg_m3.toFixed(1)} kg/m³
                    </div>
                    <div style={{ fontSize: '0.68rem', color: tokens.textMuted, marginTop: '2px' }}>
                      Cementitious Content
                    </div>
                  </div>

                  {/* Commercial Feasibility Cost */}
                  <div style={{ padding: '10px', borderRadius: '6px', backgroundColor: tokens.surfaceSecondary, border: `1px solid ${tokens.border}` }}>
                    <div style={{ fontSize: '0.68rem', color: tokens.textMuted, fontWeight: 600, textTransform: 'uppercase' }}>
                      Material Cost / m³
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: tokens.textPrimary, fontFamily: tokens.fontMono, marginTop: '2px' }}>
                      {activeCandidate.cost_per_m3 !== null ? `₹ ${activeCandidate.cost_per_m3.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                    </div>
                    <div style={{ fontSize: '0.68rem', color: tokens.textMuted, marginTop: '2px' }}>
                      {activeCandidate.cost_status === 'NOT_CONFIGURED' ? 'Pricing Source: Not Configured' : activeCandidate.cost_status}
                    </div>
                  </div>
                </div>
              </div>

              {/* Review Decision Provenance (if reviewed) */}
              {activeCandidate.review_status !== 'PENDING_REVIEW' && (
                <div
                  style={{
                    padding: '12px 14px',
                    borderRadius: '6px',
                    backgroundColor: activeCandidate.review_status === 'ACCEPTED' ? tokens.successGreenLight : tokens.dangerRedLight,
                    border: `1px solid ${activeCandidate.review_status === 'ACCEPTED' ? tokens.successGreenBorder : tokens.dangerRedBorder}`,
                    fontSize: '0.8rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: activeCandidate.review_status === 'ACCEPTED' ? tokens.successGreen : tokens.dangerRed }}>
                    <UserCheck size={16} />
                    <span>
                      Human Review Decision: {activeCandidate.review_status} by {activeCandidate.reviewed_by_username || 'Authorized User'}
                    </span>
                    {activeCandidate.reviewed_at && (
                      <span style={{ fontSize: '0.72rem', fontWeight: 400, color: tokens.textMuted, marginLeft: 'auto' }}>
                        {new Date(activeCandidate.reviewed_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                  {activeCandidate.review_decision_reason && (
                    <div style={{ marginTop: '6px', color: tokens.textPrimary, fontSize: '0.75rem' }}>
                      <strong>Reason Code:</strong> {activeCandidate.review_decision_reason}
                    </div>
                  )}
                  {activeCandidate.review_comments && (
                    <div style={{ marginTop: '4px', color: tokens.textSecondary, fontSize: '0.75rem', fontStyle: 'italic' }}>
                      "{activeCandidate.review_comments}"
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {isModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '16px',
          }}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              padding: '24px',
              maxWidth: '480px',
              width: '100%',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            }}
          >
            <h3 style={{ margin: '0 0 12px 0', fontSize: '1.05rem', fontWeight: 700, color: tokens.textPrimary }}>
              Confirm {pendingAction === 'ACCEPT' ? 'Acceptance' : 'Rejection'} of {activeCandidate?.candidate_identifier}
            </h3>

            <p style={{ fontSize: '0.8rem', color: tokens.textSecondary, marginBottom: '16px', lineHeight: 1.4 }}>
              You are recording an authoritative human governance decision for candidate{' '}
              <strong>{activeCandidate?.candidate_identifier}</strong>. Select the engineering reason code below.
            </p>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: tokens.textPrimary, marginBottom: '6px' }}>
                Reason Code
              </label>
              <select
                value={selectedReason}
                onChange={(e) => setSelectedReason(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  border: `1px solid ${tokens.border}`,
                  fontSize: '0.8rem',
                  color: tokens.textPrimary,
                }}
              >
                {REVIEW_REASONS.map((r) => (
                  <option key={r.code} value={r.code}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: '18px' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: tokens.textPrimary, marginBottom: '6px' }}>
                Optional Engineering Comments
              </label>
              <textarea
                value={reviewComments}
                onChange={(e) => setReviewComments(e.target.value)}
                rows={3}
                placeholder="Enter technical notes, trial batch conditions, or specific constraints..."
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  border: `1px solid ${tokens.border}`,
                  fontSize: '0.8rem',
                  fontFamily: 'inherit',
                  resize: 'vertical',
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => setIsModalOpen(false)}
                disabled={isSubmitting}
                style={{
                  padding: '8px 16px',
                  borderRadius: '6px',
                  border: `1px solid ${tokens.border}`,
                  backgroundColor: tokens.surfaceSecondary,
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReview}
                disabled={isSubmitting}
                style={{
                  padding: '8px 18px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: pendingAction === 'ACCEPT' ? tokens.successGreen : tokens.dangerRed,
                  color: '#ffffff',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                {isSubmitting ? 'Recording Decision...' : `Confirm ${pendingAction === 'ACCEPT' ? 'Accept' : 'Reject'}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
