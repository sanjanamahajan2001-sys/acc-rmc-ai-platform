import React, { useEffect, useState } from 'react';
import { MixerTruckIcon } from '../../icons';
import {
  optimizationService,
  RecipeImpactResponse,
  ConstituentImpactItem,
} from '../../../services/optimizationService';
import {
  ArrowDownRight,
  ArrowUpRight,
  Minus,
  CheckCircle2,
  TrendingDown,
  Layers,
  Droplets,
  Activity,
  Award,
  AlertTriangle,
  RotateCw,
  Info,
} from 'lucide-react';

interface RecipeImpactComparisonProps {
  runId: string;
  candidateId: string;
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
  successGreen: '#16a34a',
  successGreenLight: '#dcfce7',
  successGreenBorder: '#bbf7d0',
  dangerRed: '#dc2626',
  dangerRedLight: '#fee2e2',
  dangerRedBorder: '#fecaca',
  warningAmber: '#d97706',
  warningAmberLight: '#fef3c7',
  fontMono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  radius: '8px',
};

export const RecipeImpactComparison: React.FC<RecipeImpactComparisonProps> = ({
  runId,
  candidateId,
  candidateIdentifier,
}) => {
  const [impact, setImpact] = useState<RecipeImpactResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadImpact = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await optimizationService.getCandidateImpact(runId, candidateId);
        if (isMounted) {
          setImpact(data);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(
            err.response?.data?.detail ||
            err.message ||
            'Failed to load recipe impact comparison metrics.'
          );
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    if (runId && candidateId) {
      loadImpact();
    }
    return () => {
      isMounted = false;
    };
  }, [runId, candidateId]);

  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '28px 16px',
          backgroundColor: tokens.surfaceSecondary,
          borderRadius: tokens.radius,
          border: `1px solid ${tokens.border}`,
          gap: '10px',
        }}
      >
        <RotateCw size={22} className="animate-spin" style={{ color: tokens.primaryAccent }} />
        <span style={{ fontSize: '0.85rem', color: tokens.textSecondary, fontWeight: 600 }}>
          Computing recipe impact & baseline deltas...
        </span>
      </div>
    );
  }

  if (error || !impact) {
    return (
      <div
        style={{
          padding: '16px 20px',
          backgroundColor: tokens.dangerRedLight,
          border: `1px solid ${tokens.dangerRedBorder}`,
          borderRadius: tokens.radius,
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px',
          color: tokens.dangerRed,
        }}
      >
        <AlertTriangle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>Failed to Load Recipe Impact</div>
          <div style={{ fontSize: '0.8rem', marginTop: '4px', opacity: 0.9 }}>{error}</div>
        </div>
      </div>
    );
  }

  const { constituents, impact_summary: summary, candidate_evaluation: evalMetrics } = impact;

  const formatTimestamp = (ts?: string | null) => {
    if (!ts) return 'Evaluation time unavailable';
    try {
      const d = new Date(ts);
      if (isNaN(d.getTime())) return 'Evaluation time unavailable';
      return d.toLocaleString();
    } catch {
      return 'Evaluation time unavailable';
    }
  };

  const renderDeltaBadge = (delta: number, pct: number | null, status: string, isInverseGood = false) => {
    if (status === 'NEW_CONSTITUENT') {
      return (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '0.72rem',
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: '4px',
            backgroundColor: tokens.primaryAccentLight,
            color: tokens.primaryAccent,
          }}
        >
          <ArrowUpRight size={12} /> New (+{delta.toFixed(1)} kg)
        </span>
      );
    }

    if (status === 'REMOVED_CONSTITUENT') {
      return (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '0.72rem',
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: '4px',
            backgroundColor: tokens.warningAmberLight,
            color: tokens.warningAmber,
          }}
        >
          <ArrowDownRight size={12} /> Removed (-100%)
        </span>
      );
    }

    if (delta === 0) {
      return (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '2px',
            fontSize: '0.72rem',
            fontWeight: 600,
            padding: '2px 6px',
            borderRadius: '4px',
            backgroundColor: tokens.surfaceHighlight,
            color: tokens.textMuted,
          }}
        >
          <Minus size={12} /> 0.0%
        </span>
      );
    }

    const isPositive = delta > 0;
    const isGood = isInverseGood ? !isPositive : isPositive;
    const bg = isGood ? tokens.successGreenLight : tokens.dangerRedLight;
    const col = isGood ? tokens.successGreen : tokens.dangerRed;

    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '2px',
          fontSize: '0.72rem',
          fontWeight: 700,
          padding: '2px 6px',
          borderRadius: '4px',
          backgroundColor: bg,
          color: col,
        }}
      >
        {isPositive ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
        {isPositive ? '+' : ''}{delta.toFixed(1)} kg ({pct !== null ? `${isPositive ? '+' : ''}${pct.toFixed(1)}%` : '—'})
      </span>
    );
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        marginTop: '16px',
        padding: '18px',
        backgroundColor: tokens.cardBg,
        borderRadius: tokens.radius,
        border: `1px solid ${tokens.border}`,
      }}
    >
      {/* Header Banner */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '10px',
          paddingBottom: '14px',
          borderBottom: `1px solid ${tokens.borderLight}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '6px',
              backgroundColor: tokens.primaryAccentLight,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <MixerTruckIcon size={20} />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 800, color: tokens.textPrimary }}>
              Recipe Impact & Baseline Comparison
            </h3>
            <p style={{ margin: 0, fontSize: '0.75rem', color: tokens.textMuted }}>
              Master Recipe: <strong>{impact.recipe_code}</strong> ({impact.grade}) vs Candidate: <strong>{impact.candidate_identifier}</strong>
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '0.72rem',
              fontWeight: 700,
              padding: '3px 8px',
              borderRadius: '6px',
              backgroundColor: evalMetrics.is_feasible ? tokens.successGreenLight : tokens.dangerRedLight,
              color: evalMetrics.is_feasible ? tokens.successGreen : tokens.dangerRed,
              border: `1px solid ${evalMetrics.is_feasible ? tokens.successGreenBorder : tokens.dangerRedBorder}`,
            }}
          >
            {evalMetrics.is_feasible ? 'FEASIBLE' : 'INFEASIBLE — DIAGNOSTIC COMPARISON ONLY'}
          </span>
          {evalMetrics.is_feasible && evalMetrics.is_non_dominated && (
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '6px',
                backgroundColor: tokens.primaryAccentLight,
                color: tokens.primaryAccent,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <Award size={13} /> PARETO FRONTIER
            </span>
          )}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
          gap: '10px',
        }}
      >
        {/* Binder Content */}
        <div
          style={{
            backgroundColor: tokens.surfaceSecondary,
            padding: '12px 14px',
            borderRadius: tokens.radius,
            border: `1px solid ${tokens.border}`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.72rem', color: tokens.textMuted, fontWeight: 700 }}>
              Binder Content
            </span>
            <TrendingDown size={14} style={{ color: tokens.primaryAccent }} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '4px' }}>
            <span style={{ fontSize: '1.15rem', fontWeight: 800, color: tokens.textPrimary }}>
              {summary.candidate_total_binder_kg_m3.toFixed(1)}
            </span>
            <span style={{ fontSize: '0.75rem', color: tokens.textMuted }}>
              kg/m³ {summary.current_total_binder_kg_m3 > 0 ? `(Master: ${summary.current_total_binder_kg_m3.toFixed(1)})` : '(Master: Unavailable)'}
            </span>
          </div>
          <div style={{ marginTop: '6px' }}>
            {renderDeltaBadge(summary.binder_delta_kg_m3, summary.binder_percentage_delta, 'NORMAL', true)}
          </div>
        </div>

        {/* Water Content */}
        <div
          style={{
            backgroundColor: tokens.surfaceSecondary,
            padding: '12px 14px',
            borderRadius: tokens.radius,
            border: `1px solid ${tokens.border}`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.72rem', color: tokens.textMuted, fontWeight: 700 }}>
              Water Content
            </span>
            <Droplets size={14} style={{ color: tokens.primaryAccent }} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '4px' }}>
            <span style={{ fontSize: '1.15rem', fontWeight: 800, color: tokens.textPrimary }}>
              {summary.candidate_water_kg_m3.toFixed(1)}
            </span>
            <span style={{ fontSize: '0.75rem', color: tokens.textMuted }}>
              kg/m³ {summary.current_water_kg_m3 > 0 ? `(Master: ${summary.current_water_kg_m3.toFixed(1)})` : '(Master: Unavailable)'}
            </span>
          </div>
          <div style={{ marginTop: '6px' }}>
            {renderDeltaBadge(summary.water_delta_kg_m3, summary.water_percentage_delta, 'NORMAL', true)}
          </div>
        </div>

        {/* Water/Binder Ratio */}
        <div
          style={{
            backgroundColor: tokens.surfaceSecondary,
            padding: '12px 14px',
            borderRadius: tokens.radius,
            border: `1px solid ${tokens.border}`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.72rem', color: tokens.textMuted, fontWeight: 700 }}>
              Water/Binder Ratio
            </span>
            <Activity size={14} style={{ color: tokens.primaryAccent }} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '4px' }}>
            <span style={{ fontSize: '1.15rem', fontWeight: 800, color: tokens.textPrimary }}>
              {summary.candidate_water_binder_ratio.toFixed(3)}
            </span>
            <span style={{ fontSize: '0.75rem', color: tokens.textMuted }}>
              {summary.current_water_binder_ratio > 0 ? `(Master: ${summary.current_water_binder_ratio.toFixed(3)})` : '(Master: Unavailable)'}
            </span>
          </div>
          <div
            style={{
              fontSize: '0.72rem',
              fontWeight: 700,
              color: summary.water_binder_ratio_delta <= 0 ? tokens.successGreen : tokens.warningAmber,
              marginTop: '6px',
            }}
          >
            Δ {summary.water_binder_ratio_delta >= 0 ? '+' : ''}
            {summary.water_binder_ratio_delta.toFixed(3)} W/B
          </div>
        </div>

        {/* Predicted 28-Day Strength */}
        <div
          style={{
            backgroundColor: tokens.surfaceSecondary,
            padding: '12px 14px',
            borderRadius: tokens.radius,
            border: `1px solid ${tokens.border}`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.72rem', color: tokens.textMuted, fontWeight: 700 }}>
              Predicted 28-Day Strength
            </span>
            <CheckCircle2 size={14} style={{ color: evalMetrics.strength_margin_mpa >= 0 ? tokens.successGreen : tokens.dangerRed }} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '4px' }}>
            <span style={{ fontSize: '1.15rem', fontWeight: 800, color: tokens.textPrimary }}>
              {evalMetrics.predicted_strength_mpa.toFixed(1)} MPa
            </span>
            <span style={{ fontSize: '0.75rem', color: tokens.textMuted }}>
              (Target: {evalMetrics.target_mean_strength_mpa.toFixed(1)} MPa)
            </span>
          </div>
          <div
            style={{
              fontSize: '0.72rem',
              fontWeight: 700,
              color: evalMetrics.strength_margin_mpa >= 0 ? tokens.successGreen : tokens.dangerRed,
              marginTop: '6px',
            }}
          >
            Margin: {evalMetrics.strength_margin_mpa >= 0 ? '+' : ''}
            {evalMetrics.strength_margin_mpa.toFixed(2)} MPa
          </div>
        </div>
      </div>

      {/* Constituent Table */}
      <div style={{ overflowX: 'auto', borderRadius: tokens.radius, border: `1px solid ${tokens.border}` }}>
        <table style={{ width: '100%', minWidth: '680px', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ backgroundColor: tokens.surfaceSecondary, borderBottom: `1px solid ${tokens.border}` }}>
              <th style={{ padding: '8px 12px', color: tokens.textSecondary, fontWeight: 700 }}>Material</th>
              <th style={{ padding: '8px 12px', color: tokens.textSecondary, fontWeight: 700 }}>Category</th>
              <th style={{ padding: '8px 12px', color: tokens.textSecondary, fontWeight: 700, textAlign: 'right' }}>Master (kg/m³)</th>
              <th style={{ padding: '8px 12px', color: tokens.textSecondary, fontWeight: 700, textAlign: 'right' }}>Candidate (kg/m³)</th>
              <th style={{ padding: '8px 12px', color: tokens.textSecondary, fontWeight: 700, textAlign: 'right' }}>Δ kg/m³</th>
              <th style={{ padding: '8px 12px', color: tokens.textSecondary, fontWeight: 700, textAlign: 'right' }}>Δ %</th>
              <th style={{ padding: '8px 12px', color: tokens.textSecondary, fontWeight: 700, textAlign: 'right' }}>SG</th>
              <th style={{ padding: '8px 12px', color: tokens.textSecondary, fontWeight: 700, textAlign: 'right' }}>Candidate Vol (m³)</th>
            </tr>
          </thead>
          <tbody>
            {constituents.map((item: ConstituentImpactItem, idx: number) => {
              const isBinder = ['CEMENT', 'FLY_ASH', 'GGBS'].includes(item.category_code);
              return (
                <tr
                  key={idx}
                  style={{
                    borderBottom: idx < constituents.length - 1 ? `1px solid ${tokens.borderLight}` : 'none',
                    backgroundColor: idx % 2 === 1 ? tokens.surfaceSecondary : '#ffffff',
                  }}
                >
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: tokens.textPrimary }}>
                    {item.material_name}
                    <span style={{ display: 'block', fontSize: '0.68rem', color: tokens.textMuted, fontFamily: tokens.fontMono }}>
                      {item.material_code}
                    </span>
                  </td>
                  <td style={{ padding: '8px 12px', color: tokens.textMuted, fontFamily: tokens.fontMono }}>
                    {item.category_code}
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'right', fontFamily: tokens.fontMono, color: tokens.textSecondary }}>
                    {item.current_quantity_kg_m3 > 0 ? item.current_quantity_kg_m3.toFixed(1) : '—'}
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'right', fontFamily: tokens.fontMono, fontWeight: 700, color: tokens.textPrimary }}>
                    {item.candidate_quantity_kg_m3 > 0 ? item.candidate_quantity_kg_m3.toFixed(1) : '—'}
                  </td>
                  <td
                    style={{
                      padding: '8px 12px',
                      textAlign: 'right',
                      fontFamily: tokens.fontMono,
                      fontWeight: 700,
                      color:
                        item.absolute_delta_kg_m3 === 0
                          ? tokens.textMuted
                          : isBinder
                          ? item.absolute_delta_kg_m3 < 0
                            ? tokens.successGreen
                            : tokens.dangerRed
                          : item.absolute_delta_kg_m3 > 0
                          ? tokens.primaryAccent
                          : tokens.textSecondary,
                    }}
                  >
                    {item.absolute_delta_kg_m3 > 0 ? `+${item.absolute_delta_kg_m3.toFixed(1)}` : item.absolute_delta_kg_m3.toFixed(1)}
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    {renderDeltaBadge(item.absolute_delta_kg_m3, item.percentage_delta, item.status_label, isBinder)}
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'right', color: tokens.textMuted, fontFamily: tokens.fontMono }}>
                    {item.candidate_specific_gravity.toFixed(2)}
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'right', fontFamily: tokens.fontMono, color: tokens.textPrimary }}>
                    {item.candidate_volume_m3.toFixed(4)}
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr style={{ backgroundColor: tokens.surfaceHighlight, fontWeight: 700, borderTop: `2px solid ${tokens.border}` }}>
              <td colSpan={2} style={{ padding: '8px 12px', color: tokens.textPrimary }}>
                Batch Yield (incl. 1.0% Entrapped Air)
              </td>
              <td style={{ padding: '8px 12px', textAlign: 'right', fontFamily: tokens.fontMono }}>
                {summary.current_yield_m3.toFixed(3)} m³
              </td>
              <td style={{ padding: '8px 12px', textAlign: 'right', fontFamily: tokens.fontMono, color: tokens.primaryAccent }}>
                {summary.candidate_yield_m3.toFixed(3)} m³
              </td>
              <td
                colSpan={4}
                style={{
                  padding: '8px 12px',
                  textAlign: 'right',
                  color: tokens.successGreen,
                  fontSize: '0.74rem',
                }}
              >
                Δ Volume: {summary.yield_delta_m3 >= 0 ? '+' : ''}{summary.yield_delta_m3.toFixed(4)} m³ (1.000 ± 0.005 m³ Compliant)
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Footer */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '8px',
          padding: '8px 12px',
          backgroundColor: tokens.surfaceSecondary,
          borderRadius: tokens.radius,
          border: `1px solid ${tokens.border}`,
          fontSize: '0.72rem',
          color: tokens.textMuted,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Info size={13} style={{ color: tokens.primaryAccent }} />
          <span>
            Lineage: <strong>{evalMetrics.prediction_source_semantics}</strong>
          </span>
        </div>
        <div>
          Evaluation Time: <strong>{formatTimestamp(impact.evaluated_at)}</strong>
        </div>
      </div>
    </div>
  );
};

export default RecipeImpactComparison;
