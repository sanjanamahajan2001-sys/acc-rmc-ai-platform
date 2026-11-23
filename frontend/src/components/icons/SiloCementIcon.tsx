import React from 'react';
import { DomainIconProps } from './types';

export const SiloCementIcon: React.FC<DomainIconProps> = ({
  size = 20,
  className = '',
  style = {},
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ display: 'inline-block', verticalAlign: 'middle', flexShrink: 0, ...style }}
    >
      {/* Ground Foundation Slab */}
      <rect x="8" y="56" width="48" height="4" rx="1" fill="#334155" />

      {/* Heavy Steel Support Legs */}
      <line x1="16" y1="44" x2="16" y2="56" stroke="#475569" strokeWidth="3" />
      <line x1="48" y1="44" x2="48" y2="56" stroke="#475569" strokeWidth="3" />
      <line x1="24" y1="48" x2="24" y2="56" stroke="#64748B" strokeWidth="2.5" />
      <line x1="40" y1="48" x2="40" y2="56" stroke="#64748B" strokeWidth="2.5" />

      {/* Cross Braces */}
      <line x1="16" y1="48" x2="24" y2="55" stroke="#94A3B8" strokeWidth="1.2" />
      <line x1="48" y1="48" x2="40" y2="55" stroke="#94A3B8" strokeWidth="1.2" />

      {/* Lower Discharge Funnel / Cone */}
      <path d="M16 42L28 52H36L48 42H16Z" fill="#1E40AF" />
      <path d="M20 42L29 50H35L44 42H20Z" fill="#1D4ED8" />
      {/* Discharge Slide Gate */}
      <rect x="29" y="52" width="6" height="3" fill="#1E293B" />

      {/* Main Silo Cylinder Body (Corporate Industrial Blue) */}
      <rect x="16" y="14" width="32" height="28" fill="#2563EB" />
      {/* Silo Highlight Shading */}
      <rect x="16" y="14" width="6" height="28" fill="#1D4ED8" />
      <rect x="24" y="14" width="16" height="28" fill="#3B82F6" />
      <rect x="42" y="14" width="6" height="28" fill="#1D4ED8" />

      {/* Reinforcing Steel Hoop Bands */}
      <line x1="16" y1="21" x2="48" y2="21" stroke="#60A5FA" strokeWidth="1.5" />
      <line x1="16" y1="28" x2="48" y2="28" stroke="#60A5FA" strokeWidth="1.5" />
      <line x1="16" y1="35" x2="48" y2="35" stroke="#60A5FA" strokeWidth="1.5" />

      {/* Vertical Level Sight Gauge */}
      <rect x="20" y="18" width="3" height="20" rx="1.5" fill="#1E293B" />
      <rect x="20.5" y="24" width="2" height="13" rx="1" fill="#FBBF24" />

      {/* Silo Domed Roof */}
      <path d="M16 14C16 7 48 7 48 14H16Z" fill="#E2E8F0" />
      <path d="M19 14C19 9 45 9 45 14H19Z" fill="#F8FAFC" />

      {/* Top Filter Vent / Dust Collector */}
      <rect x="30" y="4" width="4" height="4" rx="1" fill="#64748B" />
      <rect x="28" y="3" width="8" height="2" rx="0.5" fill="#94A3B8" />

      {/* Access Ladder with Safety Cages on Right */}
      <line x1="45" y1="8" x2="45" y2="55" stroke="#CBD5E1" strokeWidth="1.2" />
      <line x1="47" y1="8" x2="47" y2="55" stroke="#CBD5E1" strokeWidth="1.2" />
      <line x1="45" y1="14" x2="47" y2="14" stroke="#CBD5E1" strokeWidth="1" />
      <line x1="45" y1="20" x2="47" y2="20" stroke="#CBD5E1" strokeWidth="1" />
      <line x1="45" y1="26" x2="47" y2="26" stroke="#CBD5E1" strokeWidth="1" />
      <line x1="45" y1="32" x2="47" y2="32" stroke="#CBD5E1" strokeWidth="1" />
      <line x1="45" y1="38" x2="47" y2="38" stroke="#CBD5E1" strokeWidth="1" />
    </svg>
  );
};
