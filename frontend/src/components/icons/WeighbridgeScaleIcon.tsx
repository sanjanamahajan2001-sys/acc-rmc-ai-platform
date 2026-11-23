import React from 'react';
import { DomainIconProps } from './types';

export const WeighbridgeScaleIcon: React.FC<DomainIconProps> = ({
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
      {/* Heavy Base Foundations */}
      <rect x="6" y="52" width="52" height="5" rx="1.5" fill="#1E293B" />
      {/* Load Cell Supports */}
      <rect x="12" y="47" width="8" height="5" rx="1" fill="#475569" />
      <rect x="44" y="47" width="8" height="5" rx="1" fill="#475569" />

      {/* Heavy Steel Weigh Deck Platform */}
      <path d="M8 43H56L53 47H11L8 43Z" fill="#334155" />
      <rect x="8" y="39" width="48" height="4" rx="1" fill="#475569" />
      {/* Yellow Safety Warning Stripes on Edge */}
      <line x1="12" y1="41" x2="16" y2="41" stroke="#FBBF24" strokeWidth="2" strokeLinecap="round" />
      <line x1="22" y1="41" x2="26" y2="41" stroke="#FBBF24" strokeWidth="2" strokeLinecap="round" />
      <line x1="32" y1="41" x2="36" y2="41" stroke="#FBBF24" strokeWidth="2" strokeLinecap="round" />
      <line x1="42" y1="41" x2="46" y2="41" stroke="#FBBF24" strokeWidth="2" strokeLinecap="round" />

      {/* Digital Terminal Column / Post on Left */}
      <rect x="14" y="16" width="4" height="23" rx="1" fill="#64748B" />

      {/* Digital Weigh Indicator Head */}
      <rect x="8" y="10" width="16" height="12" rx="2" fill="#1E293B" />
      <rect x="10" y="12" width="12" height="8" rx="1" fill="#0F172A" />
      {/* Green Digital LED Readout */}
      <rect x="12" y="14" width="8" height="4" rx="0.5" fill="#052E16" />
      <text x="13.5" y="17.2" fontSize="3.2" fontWeight="bold" fill="#22C55E" fontFamily="monospace">8389</text>

      {/* Cargo / Bulk Material Load on Platform */}
      <path d="M26 39L30 25H48L52 39H26Z" fill="#CBD5E1" />
      <path d="M29 39L33 27H45L49 39H29Z" fill="#E2E8F0" />
      <path d="M33 25L37 17H41L45 25H33Z" fill="#94A3B8" />
    </svg>
  );
};
