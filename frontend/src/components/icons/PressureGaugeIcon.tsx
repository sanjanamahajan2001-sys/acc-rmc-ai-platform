import React from 'react';
import { DomainIconProps } from './types';

export const PressureGaugeIcon: React.FC<DomainIconProps> = ({
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
      {/* Hydraulic Mount / Inlet Stem */}
      <rect x="29" y="50" width="6" height="10" rx="1" fill="#475569" />
      <rect x="27" y="57" width="10" height="3" rx="0.5" fill="#334155" />

      {/* Outer Metal Bezel */}
      <circle cx="32" cy="28" r="24" fill="#334155" />
      <circle cx="32" cy="28" r="22" fill="#64748B" />
      <circle cx="32" cy="28" r="20" fill="#E2E8F0" />

      {/* Inner White Face */}
      <circle cx="32" cy="28" r="18.5" fill="#FFFFFF" />

      {/* Pressure Range Arcs */}
      {/* 1. Low Pressure Arc (Amber) */}
      <path
        d="M17 34 A 15 15 0 0 1 24 18"
        stroke="#FBBF24"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* 2. Optimal Design Strength Arc (Green) */}
      <path
        d="M26 17 A 15 15 0 0 1 38 17"
        stroke="#10B981"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* 3. High Load Capacity Arc (Crimson) */}
      <path
        d="M40 18 A 15 15 0 0 1 47 34"
        stroke="#EF4444"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />

      {/* Dial Ticks */}
      <line x1="20" y1="28" x2="23" y2="28" stroke="#94A3B8" strokeWidth="1.5" />
      <line x1="44" y1="28" x2="41" y2="28" stroke="#94A3B8" strokeWidth="1.5" />
      <line x1="32" y1="16" x2="32" y2="19" stroke="#94A3B8" strokeWidth="1.5" />

      {/* Center Pivot Boss */}
      <circle cx="32" cy="30" r="4" fill="#1E293B" />
      <circle cx="32" cy="30" r="2" fill="#94A3B8" />

      {/* Red Indicator Needle pointing into Green Zone (Target MPa) */}
      <path
        d="M31.2 30L34 14L32.8 30H31.2Z"
        fill="#DC2626"
      />
      <circle cx="32" cy="30" r="1.5" fill="#DC2626" />
    </svg>
  );
};
