import React from 'react';
import { DomainIconProps } from './types';

export const AggregateHopperIcon: React.FC<DomainIconProps> = ({
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
      {/* Ground Legs for Hopper */}
      <line x1="8" y1="42" x2="8" y2="58" stroke="#475569" strokeWidth="3" />
      <line x1="38" y1="42" x2="38" y2="58" stroke="#475569" strokeWidth="3" />
      <line x1="8" y1="50" x2="38" y2="50" stroke="#64748B" strokeWidth="2" />

      {/* Aggregate Storage Hopper Bin (V-Shaped Funnel) */}
      <path d="M6 18H40L30 42H16L6 18Z" fill="#334155" />
      <path d="M9 20H37L28 40H18L9 20Z" fill="#475569" />

      {/* Coarse Gravel & Sand Piles inside Hopper */}
      {/* 20mm / 10mm Coarse Aggregate Stones */}
      <circle cx="16" cy="24" r="3" fill="#94A3B8" />
      <circle cx="23" cy="23" r="3.5" fill="#CBD5E1" />
      <circle cx="30" cy="24" r="3" fill="#94A3B8" />
      <circle cx="19" cy="29" r="3.2" fill="#64748B" />
      <circle cx="26" cy="30" r="3.5" fill="#94A3B8" />
      {/* Fine Aggregate Sand Particles */}
      <circle cx="22" cy="36" r="2.5" fill="#D97706" />
      <circle cx="25" cy="35" r="2" fill="#F59E0B" />

      {/* Hopper Top Reinforcing Rim */}
      <rect x="5" y="16" width="36" height="3" rx="1" fill="#1E293B" />

      {/* Chemical Admixture Lab Flask / Beaker on Right */}
      {/* Flask Neck */}
      <rect x="47" y="24" width="6" height="8" rx="1" fill="#CBD5E1" />
      <rect x="45" y="22" width="10" height="3" rx="1" fill="#94A3B8" />
      {/* Flask Conical Glass Body */}
      <path d="M48 32L40 54C39 56 41 58 43 58H57C59 58 61 56 60 54L52 32H48Z" fill="#F3E8FF" stroke="#C084FC" strokeWidth="1.5" />
      {/* Liquid Chemical Admixture (High-Range PCE Superplasticizer - Purple) */}
      <path d="M49 42L43 55C42.5 56 43 57 44 57H56C57 57 57.5 56 57 55L51 42H49Z" fill="#9333EA" />
      <path d="M49 42C49 42 50 43 51 42L51 45C51 45 50 44 49 45V42Z" fill="#A855F7" />

      {/* Measurement Graduation Lines on Glass */}
      <line x1="45" y1="46" x2="48" y2="46" stroke="#FFFFFF" strokeWidth="1" />
      <line x1="46" y1="50" x2="49" y2="50" stroke="#FFFFFF" strokeWidth="1" />
    </svg>
  );
};
