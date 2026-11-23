import React, { useEffect, useState } from 'react';
import { RupeeCoinIcon } from '../../icons';
import {
  optimizationService,
  CostImpactResponseDTO,
  MaterialCostImpactDTO,
} from '../../../services/optimizationService';
import {
  DollarSign,
  TrendingDown,
  TrendingUp,
  Minus,
  AlertCircle,
  Calendar,
  Layers,
  CheckCircle2,
  Info,
  RotateCw,
  Building2,
  FileSpreadsheet,
  AlertTriangle,
} from 'lucide-react';

interface CostImpactComparisonProps {
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
  warningAmberBorder: '#fde68a',
  fontMono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  radius: '8px',
};

export const CostImpactComparison: React.FC<CostImpactComparisonProps> = ({
  runId,
  candidateId,
  candidateIdentifier,
}) => {
  const [costData, setCostData] = useState<CostImpactResponseDTO | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    if (!runId || !candidateId) return;

    const fetchCostImpact = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await optimizationService.getCandidateCostImpact(runId, candidateId);
        if (isMounted) {
          setCostData(data);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err?.response?.data?.detail || err?.message || 'Failed to load commercial feasibility data.');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchCostImpact();

    return () => {
      isMounted = false;
    };
  }, [runId, candidateId]);

  if (isLoading) {
    return (
      <div
        style={{
          padding: '24px',
          border: `1px solid ${tokens.border}`,
          borderRadius: tokens.radius,
          backgroundColor: tokens.surfaceSecondary,
          textAlign: 'center',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '10px',
          color: tokens.textSecondary,
          fontSize: '0.85rem',
        }}
      >
        <RotateCw size={16} className="animate-spin" style={{ color: tokens.primaryAccent }} />
        Calculating commercial feasibility and cost impact...
      </div>
    );
  }

  if (error || !costData) {
    return (
      <div
        style={{
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
        <AlertCircle size={18} />
        <span>{error || 'Unable to display cost impact analysis.'}</span>
      </div>
    );
  }

  const { cost_summary, material_impacts, price_source_description, pricing_snapshot_id, pricing_version, effective_date, is_feasible } = costData;
  const isConfigured = cost_summary.cost_status === 'CONFIGURED';
  const isPartial = cost_summary.cost_status === 'PARTIALLY_CONFIGURED';
  const isUnconfigured = cost_summary.cost_status === 'NOT_CONFIGURED';

  const deltaPerM3 = cost_summary.cost_delta_per_m3;
  const deltaPct = cost_summary.cost_delta_percent;
  const isNegativeDelta = deltaPerM3 !== null && deltaPerM3 < 0;
  const isPositiveDelta = deltaPerM3 !== null && deltaPerM3 > 0;

  const formatCurrencyDelta = (val: number | null) => {
    if (val === null) return '—';
    const prefix = val < 0 ? '- ' : val > 0 ? '+ ' : '';
    return `${prefix}₹ ${Math.abs(val).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              backgroundColor: tokens.primaryAccentLight,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <RupeeCoinIcon size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.92rem', fontWeight: 700, color: tokens.textPrimary, display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              Cost & Commercial Feasibility Analysis
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontFamily: tokens.fontMono,
                  backgroundColor: isConfigured
                    ? tokens.successGreenLight
                    : isPartial
                    ? tokens.warningAmberLight
                    : tokens.surfaceHighlight,
                  color: isConfigured
                    ? tokens.successGreen
                    : isPartial
                    ? tokens.warningAmber
                    : tokens.textSecondary,
                  border: `1px solid ${
                    isConfigured
                      ? tokens.successGreenBorder
                      : isPartial
                      ? tokens.warningAmberBorder
                      : tokens.border
                  }`,
                }}
              >
                {cost_summary.cost_status}
              </span>
              {is_feasible === false && (
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: tokens.dangerRedLight,
                    color: tokens.dangerRed,
                    border: `1px solid ${tokens.dangerRedBorder}`,
                  }}
                >
                  INFEASIBLE — DIAGNOSTIC COMPARISON ONLY
                </span>
              )}
            </div>
            <div style={{ fontSize: '0.72rem', color: tokens.textMuted }}>
              Target: <span style={{ fontWeight: 600, color: tokens.textSecondary }}>{costData.recipe_code} ({costData.grade})</span> | Candidate: <span style={{ fontWeight: 600, color: tokens.textSecondary }}>{candidateIdentifier || costData.candidate_identifier}</span> | Plant: <span style={{ fontWeight: 600, color: tokens.textSecondary }}>{costData.plant_code}</span>
            </div>
          </div>
        </div>

        {/* Provenance Badge & Metadata */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: tokens.textMuted }}>
            <FileSpreadsheet size={14} style={{ color: isConfigured ? tokens.primaryAccent : tokens.textMuted }} />
            <span>
              {isUnconfigured ? (
                <strong style={{ color: tokens.textMuted }}>Pricing Source: Not Configured</strong>
              ) : (
                <span>
                  Source: <strong style={{ color: tokens.textSecondary }}>{price_source_description.replace('Pricing Source: ', '')}</strong>
                </span>
              )}
            </span>
          </div>
          {isConfigured && (pricing_snapshot_id || pricing_version || effective_date) && (
            <div style={{ display: 'flex', gap: '6px', fontSize: '0.65rem', color: tokens.textMuted, fontFamily: tokens.fontMono }}>
              {pricing_snapshot_id && <span>ID: {pricing_snapshot_id}</span>}
              {pricing_version && <span>• Ver: {pricing_version}</span>}
              {effective_date && <span>• Eff: {new Date(effective_date).toLocaleDateString()}</span>}
            </div>
          )}
        </div>
      </div>

      {/* Warning/Info Banner if Not Fully Configured */}
      {!isConfigured && (
        <div
          style={{
            padding: '12px 18px',
            backgroundColor: isPartial ? tokens.warningAmberLight : tokens.surfaceSecondary,
            borderBottom: `1px solid ${isPartial ? tokens.warningAmberBorder : tokens.border}`,
            fontSize: '0.8rem',
            color: isPartial ? tokens.warningAmber : tokens.textSecondary,
            display: 'flex',
            alignItems: 'flex-start',
            gap: '8px',
          }}
        >
          <Info size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            {isUnconfigured && (
              <span>
                <strong>Cost Not Configured:</strong> No authoritative procurement pricing snapshot is bound to this run. Material unit prices are not assumed or fabricated.
              </span>
            )}
            {isPartial && (
              <span>
                <strong>Incomplete Pricing Snapshot:</strong> Authoritative unit pricing or conversion is missing for constituent(s):{' '}
                <strong>{(cost_summary.unpriced_materials || cost_summary.missing_price_constituents || []).join(', ')}</strong>. Total recipe-level commercial metrics are suppressed to prevent inaccurate commercial decisions.
              </span>
            )}
          </div>
        </div>
      )}

      {/* Main Metric Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px',
          padding: '16px 18px',
          backgroundColor: '#ffffff',
          borderBottom: `1px solid ${tokens.border}`,
        }}
      >
        {/* Master Recipe Cost */}
        <div
          style={{
            padding: '12px',
            borderRadius: '6px',
            backgroundColor: tokens.surfaceSecondary,
            border: `1px solid ${tokens.border}`,
          }}
        >
          <div style={{ fontSize: '0.72rem', fontWeight: 600, color: tokens.textMuted, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Master Recipe Cost / m³
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: tokens.textPrimary, marginTop: '4px', fontFamily: tokens.fontMono }}>
            {cost_summary.master_cost_per_m3 !== null ? `₹ ${cost_summary.master_cost_per_m3.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
          </div>
          <div style={{ fontSize: '0.7rem', color: tokens.textMuted, marginTop: '2px' }}>
            {cost_summary.master_cost_per_m3 !== null ? 'Authoritative baseline snapshot' : 'Available when authoritative pricing is configured'}
          </div>
        </div>

        {/* Candidate Mix Cost */}
        <div
          style={{
            padding: '12px',
            borderRadius: '6px',
            backgroundColor: tokens.surfaceSecondary,
            border: `1px solid ${tokens.border}`,
          }}
        >
          <div style={{ fontSize: '0.72rem', fontWeight: 600, color: tokens.textMuted, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Candidate Mix Cost / m³
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: tokens.textPrimary, marginTop: '4px', fontFamily: tokens.fontMono }}>
            {cost_summary.candidate_cost_per_m3 !== null ? `₹ ${cost_summary.candidate_cost_per_m3.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
          </div>
          <div style={{ fontSize: '0.7rem', color: tokens.textMuted, marginTop: '2px' }}>
            {cost_summary.candidate_cost_per_m3 !== null ? 'Evaluated alternative' : 'Available when authoritative pricing is configured'}
          </div>
        </div>

        {/* Total Cost Delta / m³ (Strictly labeled Cost Delta, not Savings) */}
        <div
          style={{
            padding: '12px',
            borderRadius: '6px',
            backgroundColor: isNegativeDelta
              ? tokens.successGreenLight
              : isPositiveDelta
              ? tokens.dangerRedLight
              : tokens.surfaceSecondary,
            border: `1px solid ${
              isNegativeDelta
                ? tokens.successGreenBorder
                : isPositiveDelta
                ? tokens.dangerRedBorder
                : tokens.border
            }`,
          }}
        >
          <div style={{ fontSize: '0.72rem', fontWeight: 600, color: isNegativeDelta ? tokens.successGreen : isPositiveDelta ? tokens.dangerRed : tokens.textMuted, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Cost Delta / m³
          </div>
          <div
            style={{
              fontSize: '1.25rem',
              fontWeight: 800,
              color: isNegativeDelta ? tokens.successGreen : isPositiveDelta ? tokens.dangerRed : tokens.textPrimary,
              marginTop: '4px',
              fontFamily: tokens.fontMono,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            {isNegativeDelta && <TrendingDown size={18} />}
            {isPositiveDelta && <TrendingUp size={18} />}
            {formatCurrencyDelta(deltaPerM3)}
          </div>
          <div style={{ fontSize: '0.7rem', color: isNegativeDelta ? tokens.successGreen : isPositiveDelta ? tokens.dangerRed : tokens.textMuted, marginTop: '2px' }}>
            {deltaPct !== null ? `${deltaPct > 0 ? '+' : ''}${deltaPct}% vs Master` : 'Calculated when fully priced'}
          </div>
        </div>
      </div>

      {/* Production Volume Impact Panel */}
      <div
        style={{
          padding: '16px 18px',
          backgroundColor: '#fafafa',
          borderBottom: `1px solid ${tokens.border}`,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', fontWeight: 700, color: tokens.textPrimary }}>
            <Building2 size={16} style={{ color: tokens.primaryAccent }} />
            Production Volume Financial Impact
          </div>
          {cost_summary.production_impact.is_configured ? (
            <div style={{ fontSize: '0.72rem', color: tokens.textMuted }}>
              Basis: <span style={{ fontWeight: 600, color: tokens.textSecondary }}>{cost_summary.production_impact.volume_source}</span>
            </div>
          ) : (
            <span style={{ fontSize: '0.72rem', color: tokens.textMuted, fontStyle: 'italic' }}>
              Volume schedule unconfigured
            </span>
          )}
        </div>

        {cost_summary.production_impact.is_configured ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
            {/* Daily */}
            {cost_summary.production_impact.daily_volume_m3 !== null && (
              <div style={{ padding: '10px 14px', backgroundColor: '#ffffff', borderRadius: '6px', border: `1px solid ${tokens.border}` }}>
                <div style={{ fontSize: '0.7rem', color: tokens.textMuted, textTransform: 'uppercase' }}>
                  Daily Impact ({cost_summary.production_impact.daily_volume_m3?.toLocaleString()} m³)
                </div>
                <div
                  style={{
                    fontSize: '1.05rem',
                    fontWeight: 800,
                    fontFamily: tokens.fontMono,
                    marginTop: '4px',
                    color: (cost_summary.production_impact.daily_cost_delta ?? 0) < 0 ? tokens.successGreen : tokens.dangerRed,
                  }}
                >
                  {formatCurrencyDelta(cost_summary.production_impact.daily_cost_delta ?? null)}
                </div>
              </div>
            )}

            {/* Monthly */}
            {cost_summary.production_impact.monthly_volume_m3 !== null && (
              <div style={{ padding: '10px 14px', backgroundColor: '#ffffff', borderRadius: '6px', border: `1px solid ${tokens.border}` }}>
                <div style={{ fontSize: '0.7rem', color: tokens.textMuted, textTransform: 'uppercase' }}>
                  Monthly Impact ({cost_summary.production_impact.monthly_volume_m3?.toLocaleString()} m³)
                </div>
                <div
                  style={{
                    fontSize: '1.05rem',
                    fontWeight: 800,
                    fontFamily: tokens.fontMono,
                    marginTop: '4px',
                    color: (cost_summary.production_impact.monthly_cost_delta ?? 0) < 0 ? tokens.successGreen : tokens.dangerRed,
                  }}
                >
                  {formatCurrencyDelta(cost_summary.production_impact.monthly_cost_delta ?? null)}
                </div>
              </div>
            )}

            {/* Annualized */}
            {cost_summary.production_impact.annualized_volume_m3 !== null && (
              <div style={{ padding: '10px 14px', backgroundColor: '#ffffff', borderRadius: '6px', border: `1px solid ${tokens.border}` }}>
                <div style={{ fontSize: '0.7rem', color: tokens.textMuted, textTransform: 'uppercase' }}>
                  Annualized Impact ({cost_summary.production_impact.annualized_volume_m3?.toLocaleString()} m³)
                </div>
                <div
                  style={{
                    fontSize: '1.05rem',
                    fontWeight: 800,
                    fontFamily: tokens.fontMono,
                    marginTop: '4px',
                    color: (cost_summary.production_impact.annualized_cost_delta ?? 0) < 0 ? tokens.successGreen : tokens.dangerRed,
                  }}
                >
                  {formatCurrencyDelta(cost_summary.production_impact.annualized_cost_delta ?? null)}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ fontSize: '0.75rem', color: tokens.textMuted, padding: '8px 0' }}>
            Production volume parameters (daily, monthly, annual m³) have not been configured for commercial scaling. Only unit per-m³ metrics are evaluated.
          </div>
        )}
      </div>

      {/* Itemized Material Cost Breakdown Table */}
      <div style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
        <table style={{ width: '100%', minWidth: '760px', borderCollapse: 'collapse', fontSize: '0.78rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ backgroundColor: '#f1f5f9', borderBottom: `1px solid ${tokens.border}`, color: tokens.textSecondary }}>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Constituent Material</th>
              <th style={{ padding: '10px 12px', fontWeight: 700, textAlign: 'right' }}>Master Qty (kg/m³)</th>
              <th style={{ padding: '10px 12px', fontWeight: 700, textAlign: 'right' }}>Candidate Qty (kg/m³)</th>
              <th style={{ padding: '10px 12px', fontWeight: 700, textAlign: 'right' }}>Qty Δ (kg/m³)</th>
              <th style={{ padding: '10px 12px', fontWeight: 700, textAlign: 'right' }}>Unit Price</th>
              <th style={{ padding: '10px 12px', fontWeight: 700, textAlign: 'right' }}>Master Cost (₹/m³)</th>
              <th style={{ padding: '10px 12px', fontWeight: 700, textAlign: 'right' }}>Cand Cost (₹/m³)</th>
              <th style={{ padding: '10px 14px', fontWeight: 700, textAlign: 'right' }}>Cost Δ (₹/m³)</th>
            </tr>
          </thead>
          <tbody>
            {material_impacts.map((mat: MaterialCostImpactDTO, idx: number) => {
              const itemSaving = mat.cost_delta_per_m3 !== null && mat.cost_delta_per_m3 < 0;
              const itemCostIncrease = mat.cost_delta_per_m3 !== null && mat.cost_delta_per_m3 > 0;

              return (
                <tr
                  key={mat.material_code || idx}
                  style={{
                    borderBottom: `1px solid ${tokens.borderLight}`,
                    backgroundColor: idx % 2 === 0 ? '#ffffff' : '#fafafa',
                  }}
                >
                  {/* Material Name & Category */}
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ fontWeight: 600, color: tokens.textPrimary }}>{mat.material_name}</div>
                    <div style={{ fontSize: '0.68rem', color: tokens.textMuted, display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <span style={{ fontFamily: tokens.fontMono }}>{mat.material_code}</span>
                      <span>•</span>
                      <span style={{ textTransform: 'capitalize' }}>{mat.category_code.toLowerCase().replace(/_/g, ' ')}</span>
                      {mat.status_label === 'UNPRICED' && (
                        <span style={{ color: tokens.warningAmber, fontWeight: 700, fontSize: '0.65rem' }}>[UNPRICED]</span>
                      )}
                      {mat.status_label === 'PRICE_CONVERSION_UNAVAILABLE' && (
                        <span style={{ color: tokens.dangerRed, fontWeight: 700, fontSize: '0.65rem' }}>[PRICE CONVERSION UNAVAILABLE]</span>
                      )}
                      {mat.status_label === 'UNSUPPORTED_UNIT' && (
                        <span style={{ color: tokens.dangerRed, fontWeight: 700, fontSize: '0.65rem' }}>[UNSUPPORTED UNIT]</span>
                      )}
                      {mat.status_label === 'NEW_CONSTITUENT' && (
                        <span style={{ color: tokens.primaryAccent, fontWeight: 700, fontSize: '0.65rem' }}>[NEW]</span>
                      )}
                      {mat.status_label === 'REMOVED_CONSTITUENT' && (
                        <span style={{ color: tokens.textMuted, fontWeight: 700, fontSize: '0.65rem' }}>[REMOVED]</span>
                      )}
                    </div>
                  </td>

                  {/* Master Qty */}
                  <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: tokens.fontMono }}>
                    {mat.master_quantity_kg_m3.toFixed(1)}
                  </td>

                  {/* Candidate Qty */}
                  <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: tokens.fontMono, fontWeight: 600 }}>
                    {mat.candidate_quantity_kg_m3.toFixed(1)}
                  </td>

                  {/* Qty Delta */}
                  <td
                    style={{
                      padding: '10px 12px',
                      textAlign: 'right',
                      fontFamily: tokens.fontMono,
                      color: mat.quantity_delta_kg_m3 < 0 ? tokens.successGreen : mat.quantity_delta_kg_m3 > 0 ? tokens.primaryAccent : tokens.textMuted,
                    }}
                  >
                    {mat.quantity_delta_kg_m3 > 0 ? '+' : ''}
                    {mat.quantity_delta_kg_m3.toFixed(1)}
                  </td>

                  {/* Unit Price */}
                  <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: tokens.fontMono }}>
                    {mat.price_provenance.unit_price !== null && mat.price_provenance.is_available ? (
                      <div>
                        <div>₹ {mat.price_provenance.unit_price}</div>
                        <div style={{ fontSize: '0.65rem', color: tokens.textMuted }}>{mat.price_provenance.price_unit}</div>
                      </div>
                    ) : (
                      <span style={{ color: tokens.warningAmber, fontSize: '0.72rem' }}>—</span>
                    )}
                  </td>

                  {/* Master Cost */}
                  <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: tokens.fontMono }}>
                    {mat.master_cost_per_m3 !== null ? `₹ ${mat.master_cost_per_m3.toFixed(2)}` : '—'}
                  </td>

                  {/* Candidate Cost */}
                  <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: tokens.fontMono, fontWeight: 600 }}>
                    {mat.candidate_cost_per_m3 !== null ? `₹ ${mat.candidate_cost_per_m3.toFixed(2)}` : '—'}
                  </td>

                  {/* Cost Delta */}
                  <td
                    style={{
                      padding: '10px 14px',
                      textAlign: 'right',
                      fontFamily: tokens.fontMono,
                      fontWeight: 700,
                      color: itemSaving ? tokens.successGreen : itemCostIncrease ? tokens.dangerRed : tokens.textMuted,
                    }}
                  >
                    {mat.cost_delta_per_m3 !== null ? (
                      <div>
                        <div>
                          {mat.cost_delta_per_m3 > 0 ? '+' : '- '}₹ {Math.abs(mat.cost_delta_per_m3).toFixed(2)}
                        </div>
                        {mat.cost_delta_percent !== null && (
                          <div style={{ fontSize: '0.68rem' }}>
                            {mat.cost_delta_percent > 0 ? '+' : ''}{mat.cost_delta_percent.toFixed(1)}%
                          </div>
                        )}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
