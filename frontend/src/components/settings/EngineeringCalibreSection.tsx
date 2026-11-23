import React, { useState, useEffect } from 'react';
import {
  EngineeringCalibreSettingsDTO,
  fetchEngineeringSettings,
  updateEngineeringSettings,
  resetEngineeringSettings,
} from '../../services/settingsService';
import { enterpriseLightTokens as tokens } from '../manual-entry/enterpriseLightTokens';
import {
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Scale,
  ShieldAlert,
  Save,
  BookOpen,
  FlaskConical,
} from 'lucide-react';

export const EngineeringCalibreSection: React.FC = () => {
  const [settings, setSettings] = useState<EngineeringCalibreSettingsDTO | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [hasChanges, setHasChanges] = useState<boolean>(false);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setFeedbackMsg(null);
      const res = await fetchEngineeringSettings();
      setSettings(res);
      setHasChanges(false);
    } catch (err: any) {
      setFeedbackMsg({
        type: 'error',
        text: err?.response?.data?.detail || 'Failed to load engineering calculation settings.',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleStandardChange = (stdCode: string) => {
    if (!settings) return;
    const selectedStd = settings.available_standards.find((s) => s.code === stdCode);
    if (!selectedStd) return;

    setSettings({
      ...settings,
      standard_code: selectedStd.code,
      standard_name: selectedStd.name,
      target_strength_formula: selectedStd.formula,
      confidence_multiplier_z: selectedStd.default_z,
    });
    setHasChanges(true);
  };

  const handleZMultiplierChange = (zVal: number) => {
    if (!settings) return;
    setSettings({
      ...settings,
      confidence_multiplier_z: zVal,
    });
    setHasChanges(true);
  };

  const handleAirVolumeChange = (airPct: number) => {
    if (!settings) return;
    const fraction = airPct / 100.0;
    setSettings({
      ...settings,
      air_volume_percent: airPct,
      air_volume_fraction: fraction,
    });
    setHasChanges(true);
  };

  const handleExposureChange = (
    tier: string,
    field: 'min_cement_kg_m3' | 'max_wb_ratio' | 'min_grade',
    value: any
  ) => {
    if (!settings) return;
    const updated = { ...settings.exposure_constraints_json };
    if (!updated[tier]) {
      updated[tier] = { min_cement_kg_m3: 300, max_wb_ratio: 0.5, min_grade: 'M25' };
    }
    updated[tier] = {
      ...updated[tier],
      [field]: field === 'min_grade' ? String(value) : Number(value),
    };
    setSettings({
      ...settings,
      exposure_constraints_json: updated,
    });
    setHasChanges(true);
  };

  const handleScmChange = (
    scmKey: string,
    field: 'min_percent' | 'max_percent' | 'default_percent',
    val: number
  ) => {
    if (!settings) return;
    const updated = { ...settings.scm_substitution_bounds_json };
    if (!updated[scmKey]) {
      updated[scmKey] = { min_percent: 0, max_percent: 30, default_percent: 20 };
    }
    updated[scmKey] = {
      ...updated[scmKey],
      [field]: Number(val),
    };
    setSettings({
      ...settings,
      scm_substitution_bounds_json: updated,
    });
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (!settings) return;
    try {
      setSaving(true);
      setFeedbackMsg(null);
      const res = await updateEngineeringSettings(settings);
      setSettings(res);
      setHasChanges(false);
      setFeedbackMsg({
        type: 'success',
        text: 'Engineering calculation calibre settings successfully persisted to database.',
      });
      setTimeout(() => setFeedbackMsg(null), 5000);
    } catch (err: any) {
      setFeedbackMsg({
        type: 'error',
        text: err?.response?.data?.detail || 'Failed to save engineering settings.',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Reset all calculation settings to official IS 456 / IS 10262 factory defaults?')) {
      return;
    }
    try {
      setSaving(true);
      setFeedbackMsg(null);
      const res = await resetEngineeringSettings();
      setSettings(res);
      setHasChanges(false);
      setFeedbackMsg({
        type: 'success',
        text: 'Calculation settings restored to official IS 456 / IS 10262 factory standards.',
      });
      setTimeout(() => setFeedbackMsg(null), 5000);
    } catch (err: any) {
      setFeedbackMsg({
        type: 'error',
        text: err?.response?.data?.detail || 'Failed to reset engineering settings.',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: tokens.textSecondary }}>
        <div style={{ fontSize: '2rem', marginBottom: '12px' }}>⚙️</div>
        <p style={{ fontWeight: 600, margin: 0, color: tokens.textPrimary }}>
          Loading Engineering Calculation Calibre Metadata...
        </p>
      </div>
    );
  }

  if (!settings) return null;

  const cardStyle: React.CSSProperties = {
    backgroundColor: tokens.surfacePrimary,
    border: `1px solid ${tokens.border}`,
    borderRadius: '10px',
    padding: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
    boxSizing: 'border-box',
    width: '100%',
    minWidth: 0,
  };

  const sectionHeaderStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontSize: '0.95rem',
    fontWeight: 700,
    color: tokens.textPrimary,
    marginBottom: '16px',
    borderBottom: `1px solid ${tokens.borderLight}`,
    paddingBottom: '10px',
  };

  const labelStyle: React.CSSProperties = {
    fontSize: '0.78rem',
    fontWeight: 600,
    color: tokens.textSecondary,
    marginBottom: '6px',
    display: 'block',
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '8px 12px',
    fontSize: '0.85rem',
    borderRadius: '6px',
    border: `1px solid ${tokens.border}`,
    backgroundColor: tokens.surfacePrimary,
    color: tokens.textPrimary,
    boxSizing: 'border-box',
    outline: 'none',
  };

  const getConfidenceLabel = (z: number) => {
    if (z >= 2.30) return '99.0% Statistical Compliance (Strict High-Reliability)';
    if (z >= 1.60 && z <= 1.70) return '95.0% Standard Compliance (IS 456 / IS 10262 Official)';
    if (z >= 1.25 && z <= 1.35) return '90.0% Compliance (Economical / ACI Margin)';
    if (z <= 1.10) return '85.0% Compliance (Low Margin)';
    return `${(50 + z * 27.5).toFixed(1)}% Estimated Compliance Margin`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%', minWidth: 0, boxSizing: 'border-box' }}>
      {/* Feedback Banner */}
      {feedbackMsg && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            fontSize: '0.85rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            backgroundColor: feedbackMsg.type === 'success' ? 'rgba(5, 150, 105, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            border: `1px solid ${feedbackMsg.type === 'success' ? 'rgba(5, 150, 105, 0.25)' : 'rgba(239, 68, 68, 0.25)'}`,
            color: feedbackMsg.type === 'success' ? '#047857' : '#b91c1c',
          }}
        >
          {feedbackMsg.type === 'success' ? <CheckCircle2 size={18} style={{ flexShrink: 0 }} /> : <AlertTriangle size={18} style={{ flexShrink: 0 }} />}
          <span>{feedbackMsg.text}</span>
        </div>
      )}

      {/* Top Banner Action Bar */}
      <div className="settings-calibre-action-bar">
        <div style={{ minWidth: 0, flex: '1 1 280px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '1rem', fontWeight: 800, color: tokens.textPrimary }}>
              Core Engineering Calculation & Solver Calibre
            </span>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                color: tokens.primaryAccent,
                padding: '2px 8px',
                borderRadius: '12px',
                whiteSpace: 'nowrap',
              }}
            >
              LIVE POSTGRESQL PERSISTENCE
            </span>
          </div>
          <div style={{ fontSize: '0.78rem', color: tokens.textMuted, marginTop: '4px' }}>
            Last modified by <strong style={{ color: tokens.textSecondary }}>{settings.updated_by_username || 'Admin'}</strong> at{' '}
            {settings.updated_at ? new Date(settings.updated_at).toLocaleString() : 'System Boot'}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={handleReset}
            disabled={saving}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              fontSize: '0.82rem',
              fontWeight: 600,
              borderRadius: '6px',
              border: `1px solid ${tokens.border}`,
              backgroundColor: tokens.surfacePrimary,
              color: tokens.textSecondary,
              cursor: saving ? 'not-allowed' : 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            <RotateCcw size={15} style={{ flexShrink: 0 }} />
            <span>Reset to IS Defaults</span>
          </button>

          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !hasChanges}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 18px',
              fontSize: '0.82rem',
              fontWeight: 700,
              borderRadius: '6px',
              border: 'none',
              backgroundColor: hasChanges ? tokens.primaryAccent : '#94A3B8',
              color: '#FFFFFF',
              cursor: hasChanges && !saving ? 'pointer' : 'not-allowed',
              boxShadow: hasChanges ? '0 2px 4px rgba(37, 99, 235, 0.25)' : 'none',
              whiteSpace: 'nowrap',
            }}
          >
            <Save size={15} style={{ flexShrink: 0 }} />
            <span>{saving ? 'Saving...' : hasChanges ? 'Save Engineering Settings' : 'Settings Up to Date'}</span>
          </button>
        </div>
      </div>

      {/* Grid: Standard & Statistical Calibre + Physical Properties */}
      <div className="settings-calibre-dual-grid">
        {/* Section 1: Design Standard & Target Strength Calibre */}
        <div data-tour="settings-calibre-standard" style={cardStyle}>
          <div style={sectionHeaderStyle}>
            <BookOpen size={18} style={{ color: tokens.primaryAccent, flexShrink: 0 }} />
            <span>1. Design Standard & Statistical Calibre (Z-Factor)</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Standard Selection */}
            <div>
              <label style={labelStyle}>Governing Concrete Code Standard</label>
              <select
                value={settings.standard_code}
                onChange={(e) => handleStandardChange(e.target.value)}
                style={inputStyle}
              >
                {settings.available_standards.map((std) => (
                  <option key={std.code} value={std.code}>
                    {std.name} — {std.jurisdiction}
                  </option>
                ))}
              </select>
              <div style={{ fontSize: '0.72rem', color: tokens.textMuted, marginTop: '4px' }}>
                {settings.available_standards.find((s) => s.code === settings.standard_code)?.description}
              </div>
            </div>

            {/* Target Strength Equation Display */}
            <div
              style={{
                backgroundColor: '#F1F5F9',
                border: `1px solid ${tokens.borderLight}`,
                borderRadius: '8px',
                padding: '12px 14px',
                overflowX: 'auto',
                WebkitOverflowScrolling: 'touch',
                minWidth: 0,
              }}
            >
              <div style={{ fontSize: '0.7rem', color: tokens.textMuted, fontWeight: 700, textTransform: 'uppercase' }}>
                Target Mean Strength Formula (f'ck)
              </div>
              <div
                style={{
                  fontFamily: 'monospace',
                  fontSize: '0.92rem',
                  fontWeight: 700,
                  color: tokens.primaryAccent,
                  marginTop: '4px',
                  wordBreak: 'break-word',
                }}
              >
                {settings.standard_code === 'ACI_318_ACI_211'
                  ? `f'cr = f'c + ${settings.confidence_multiplier_z.toFixed(2)} × s`
                  : `f'ck = fck + ${settings.confidence_multiplier_z.toFixed(2)} × σ`}
              </div>
              <div style={{ fontSize: '0.72rem', color: tokens.textSecondary, marginTop: '4px' }}>
                Active Multiplier: <strong>Z = {settings.confidence_multiplier_z.toFixed(2)}</strong> →{' '}
                {getConfidenceLabel(settings.confidence_multiplier_z)}
              </div>
            </div>

            {/* Z-Factor Slider & Preset Buttons */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', flexWrap: 'wrap', gap: '4px' }}>
                <label style={{ ...labelStyle, margin: 0 }}>Statistical Safety Factor (Z-Score)</label>
                <span style={{ fontSize: '0.85rem', fontWeight: 800, color: tokens.primaryAccent }}>
                  Z = {settings.confidence_multiplier_z.toFixed(2)}
                </span>
              </div>

              <input
                type="range"
                min="1.00"
                max="2.50"
                step="0.01"
                value={settings.confidence_multiplier_z}
                onChange={(e) => handleZMultiplierChange(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: tokens.primaryAccent, cursor: 'pointer' }}
              />

              <div style={{ display: 'flex', gap: '6px', marginTop: '8px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() => handleZMultiplierChange(1.28)}
                  style={{
                    fontSize: '0.72rem',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    border: `1px solid ${settings.confidence_multiplier_z === 1.28 ? tokens.primaryAccent : tokens.border}`,
                    backgroundColor: settings.confidence_multiplier_z === 1.28 ? 'rgba(37,99,235,0.08)' : tokens.surfacePrimary,
                    color: settings.confidence_multiplier_z === 1.28 ? tokens.primaryAccent : tokens.textSecondary,
                    cursor: 'pointer',
                    fontWeight: 600,
                  }}
                >
                  90% Margin (Z=1.28)
                </button>
                <button
                  type="button"
                  onClick={() => handleZMultiplierChange(1.65)}
                  style={{
                    fontSize: '0.72rem',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    border: `1px solid ${settings.confidence_multiplier_z === 1.65 ? tokens.primaryAccent : tokens.border}`,
                    backgroundColor: settings.confidence_multiplier_z === 1.65 ? 'rgba(37,99,235,0.08)' : tokens.surfacePrimary,
                    color: settings.confidence_multiplier_z === 1.65 ? tokens.primaryAccent : tokens.textSecondary,
                    cursor: 'pointer',
                    fontWeight: 700,
                  }}
                >
                  95% Standard (Z=1.65 - IS Default)
                </button>
                <button
                  type="button"
                  onClick={() => handleZMultiplierChange(2.33)}
                  style={{
                    fontSize: '0.72rem',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    border: `1px solid ${settings.confidence_multiplier_z === 2.33 ? tokens.primaryAccent : tokens.border}`,
                    backgroundColor: settings.confidence_multiplier_z === 2.33 ? 'rgba(37,99,235,0.08)' : tokens.surfacePrimary,
                    color: settings.confidence_multiplier_z === 2.33 ? tokens.primaryAccent : tokens.textSecondary,
                    cursor: 'pointer',
                    fontWeight: 600,
                  }}
                >
                  99% High Reliability (Z=2.33)
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Physical & Volumetric Absolute Volume Yield */}
        <div style={cardStyle}>
          <div style={sectionHeaderStyle}>
            <Scale size={18} style={{ color: tokens.primaryAccent, flexShrink: 0 }} />
            <span>2. Physical Absolute Volume & Yield Parameters</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Air Volume Fraction */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', flexWrap: 'wrap', gap: '4px' }}>
                <label style={{ ...labelStyle, margin: 0 }}>Entrapped Air Volume Fraction (%)</label>
                <span style={{ fontSize: '0.85rem', fontWeight: 800, color: tokens.primaryAccent }}>
                  {settings.air_volume_percent.toFixed(1)}% ({settings.air_volume_fraction.toFixed(3)} m³/m³)
                </span>
              </div>

              <input
                type="range"
                min="0.2"
                max="4.0"
                step="0.1"
                value={settings.air_volume_percent}
                onChange={(e) => handleAirVolumeChange(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: tokens.primaryAccent, cursor: 'pointer' }}
              />
              <div style={{ fontSize: '0.72rem', color: tokens.textMuted, marginTop: '4px' }}>
                Standard: 1.0% entrapped air per IS 10262 Table 3 for 20mm Nominal Maximum Size Aggregate (NMSA).
              </div>
            </div>

            {/* Absolute Volume Equation Summary */}
            <div
              style={{
                backgroundColor: '#F8FAFC',
                border: `1px solid ${tokens.borderLight}`,
                borderRadius: '8px',
                padding: '12px 14px',
                overflowX: 'auto',
                WebkitOverflowScrolling: 'touch',
                minWidth: 0,
              }}
            >
              <div style={{ fontSize: '0.7rem', color: tokens.textMuted, fontWeight: 700, textTransform: 'uppercase' }}>
                IS 10262 Absolute Volume Yield Equation
              </div>
              <div
                style={{
                  fontFamily: 'monospace',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: tokens.textPrimary,
                  marginTop: '6px',
                  lineHeight: 1.5,
                  wordBreak: 'break-word',
                }}
              >
                V_concrete = ∑ [ Mass_i / (1000 × SG_i) ] + {settings.air_volume_fraction.toFixed(3)} = 1.000 m³
              </div>
            </div>

            {/* Specific Gravities Reference Grid */}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: tokens.textSecondary, marginBottom: '8px' }}>
                Reference Specific Gravities (SG)
              </div>
              <div className="settings-sg-grid">
                {Object.entries(settings.specific_gravities_json || {}).map(([mat, sg]) => (
                  <div
                    key={mat}
                    style={{
                      backgroundColor: '#F1F5F9',
                      padding: '6px 4px',
                      borderRadius: '6px',
                      textAlign: 'center',
                      minWidth: 0,
                      overflow: 'hidden',
                    }}
                  >
                    <div style={{ fontSize: '0.62rem', color: tokens.textMuted, textTransform: 'uppercase', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {mat}
                    </div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: tokens.textPrimary, marginTop: '2px' }}>
                      {Number(sg).toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize: '0.7rem', color: tokens.textMuted, marginTop: '6px' }}>
                Specific gravities for individual brands can be fine-tuned per material in Master Data.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Section 3: IS 456 Table 5 Durability & Environmental Exposure Limits */}
      <div data-tour="settings-calibre-durability" style={cardStyle}>
        <div style={sectionHeaderStyle}>
          <ShieldAlert size={18} style={{ color: tokens.primaryAccent, flexShrink: 0 }} />
          <span>3. Durability & Environmental Exposure Constraints (IS 456:2000 Table 5)</span>
        </div>

        <p style={{ fontSize: '0.8rem', color: tokens.textMuted, margin: '0 0 14px 0' }}>
          Defines minimum binder content floors and maximum allowable free Water-Binder (W/B) ceilings across environmental exposure classes. The AI solver strictly satisfies these bounds.
        </p>

        <div style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch', width: '100%' }}>
          <table style={{ width: '100%', minWidth: '560px', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#F1F5F9', color: tokens.textSecondary, textAlign: 'left' }}>
                <th style={{ padding: '10px 12px', borderBottom: `1px solid ${tokens.border}`, fontWeight: 700 }}>Exposure Class</th>
                <th style={{ padding: '10px 12px', borderBottom: `1px solid ${tokens.border}`, fontWeight: 700 }}>Min. Binder Content (kg/m³)</th>
                <th style={{ padding: '10px 12px', borderBottom: `1px solid ${tokens.border}`, fontWeight: 700 }}>Max. Free W/B Ratio</th>
                <th style={{ padding: '10px 12px', borderBottom: `1px solid ${tokens.border}`, fontWeight: 700 }}>Min. Grade for RCC</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(settings.exposure_constraints_json || {}).map(([tier, constraint]) => (
                <tr key={tier} style={{ borderBottom: `1px solid ${tokens.borderLight}` }}>
                  <td style={{ padding: '10px 12px', fontWeight: 700, color: tokens.textPrimary }}>
                    {tier.replace('_', ' ')}
                  </td>
                  <td style={{ padding: '8px 12px' }}>
                    <input
                      type="number"
                      min="240"
                      max="450"
                      step="5"
                      value={constraint.min_cement_kg_m3}
                      onChange={(e) => handleExposureChange(tier, 'min_cement_kg_m3', e.target.value)}
                      style={{ ...inputStyle, width: '100%', minWidth: '70px', maxWidth: '120px' }}
                    />
                  </td>
                  <td style={{ padding: '8px 12px' }}>
                    <input
                      type="number"
                      min="0.30"
                      max="0.65"
                      step="0.01"
                      value={constraint.max_wb_ratio}
                      onChange={(e) => handleExposureChange(tier, 'max_wb_ratio', e.target.value)}
                      style={{ ...inputStyle, width: '100%', minWidth: '70px', maxWidth: '120px' }}
                    />
                  </td>
                  <td style={{ padding: '8px 12px' }}>
                    <input
                      type="text"
                      value={constraint.min_grade}
                      onChange={(e) => handleExposureChange(tier, 'min_grade', e.target.value)}
                      style={{ ...inputStyle, width: '100%', minWidth: '70px', maxWidth: '100px' }}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 4: Supplementary Cementitious Materials (SCM) Substitution Limits */}
      <div style={cardStyle}>
        <div style={sectionHeaderStyle}>
          <FlaskConical size={18} style={{ color: tokens.primaryAccent, flexShrink: 0 }} />
          <span>4. SCM Replacement Boundaries (Fly Ash, GGBS, Micro-Silica)</span>
        </div>

        <p style={{ fontSize: '0.8rem', color: tokens.textMuted, margin: '0 0 14px 0' }}>
          Governs allowable substitution percentages for clinker replacement to ensure structural integrity while optimizing cost and embodied carbon.
        </p>

        <div className="settings-scm-grid">
          {Object.entries(settings.scm_substitution_bounds_json || {}).map(([scmKey, bounds]) => (
            <div
              key={scmKey}
              style={{
                backgroundColor: '#F8FAFC',
                border: `1px solid ${tokens.borderLight}`,
                borderRadius: '8px',
                padding: '14px',
                minWidth: 0,
              }}
            >
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: tokens.textPrimary, textTransform: 'capitalize', marginBottom: '12px' }}>
                {scmKey.replace('_', ' ')} Bounds
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.75rem', color: tokens.textSecondary }}>Minimum Replacement (%)</span>
                  <input
                    type="number"
                    min="0"
                    max="50"
                    value={bounds.min_percent}
                    onChange={(e) => handleScmChange(scmKey, 'min_percent', parseFloat(e.target.value))}
                    style={{ ...inputStyle, width: '80px', textAlign: 'right', flexShrink: 0 }}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.75rem', color: tokens.textSecondary }}>Maximum Replacement (%)</span>
                  <input
                    type="number"
                    min="0"
                    max="80"
                    value={bounds.max_percent}
                    onChange={(e) => handleScmChange(scmKey, 'max_percent', parseFloat(e.target.value))}
                    style={{ ...inputStyle, width: '80px', textAlign: 'right', flexShrink: 0 }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
