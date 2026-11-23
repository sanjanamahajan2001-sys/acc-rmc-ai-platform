import React from 'react';
import { DomainIconProps } from './types';

export const TargetAccuracyIcon: React.FC<DomainIconProps> = ({
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
      {/* Outer Red Ring */}
      <circle cx="30" cy="34" r="24" fill="#EF4444" />
      {/* Outer White Ring */}
      <circle cx="30" cy="34" r="18.5" fill="#FFFFFF" />
      {/* Middle Red Ring */}
      <circle cx="30" cy="34" r="13" fill="#DC2626" />
      {/* Inner White Ring */}
      <circle cx="30" cy="34" r="8" fill="#FFFFFF" />
      {/* Bullseye Center (Golden Yellow / Scarlet) */}
      <circle cx="30" cy="34" r="4" fill="#B91C1C" />
      <circle cx="30" cy="34" r="2" fill="#F59E0B" />

      {/* Target Stand / Base Feet */}
      <path d="M18 55L14 60H18L21 55H18Z" fill="#64748B" />
      <path d="M42 55L46 60H42L39 55H42Z" fill="#64748B" />

      {/* Accuracy Arrow piercing the center */}
      {/* Arrow Shaft (Golden Amber) */}
      <line x1="30" y1="34" x2="52" y2="12" stroke="#D97706" strokeWidth="2.5" strokeLinecap="round" />
      {/* Arrow Flight Feathers (Cobalt Blue & Cyan) */}
      <path d="M52 12L58 8L57 14L52 12Z" fill="#2563EB" />
      <path d="M52 12L46 7L52 6L52 12Z" fill="#3B82F6" />
      <path d="M52 12L56 18L58 12L52 12Z" fill="#60A5FA" />
      {/* Metal Nock */}
      <circle cx="52" cy="12" r="1.5" fill="#1E293B" />
    </svg>
  );
};
