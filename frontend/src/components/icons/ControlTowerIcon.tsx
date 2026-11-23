import React from 'react';
import { DomainIconProps } from './types';

export const ControlTowerIcon: React.FC<DomainIconProps> = ({
  size = 18,
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
      {/* Desktop Monitor Stand */}
      <rect x="28" y="47" width="8" height="6" fill="#334155" />
      <path d="M22 53H42L45 57H19L22 53Z" fill="#1E293B" />

      {/* Monitor Outer Bezel */}
      <rect x="8" y="12" width="48" height="35" rx="3" fill="#0F172A" stroke="#334155" strokeWidth="1.5" />
      {/* Inner Screen (Dark Slate Glow) */}
      <rect x="11" y="15" width="42" height="29" rx="1.5" fill="#030712" />

      {/* Screen Analytics Widgets */}
      {/* Metric 1 - Blue Bar */}
      <rect x="14" y="32" width="5" height="9" rx="1" fill="#38BDF8" />
      {/* Metric 2 - Indigo Bar */}
      <rect x="21" y="27" width="5" height="14" rx="1" fill="#818CF8" />
      {/* Metric 3 - Emerald Bar */}
      <rect x="28" y="22" width="5" height="19" rx="1" fill="#34D399" />
      {/* Metric 4 - Amber Bar */}
      <rect x="35" y="25" width="5" height="16" rx="1" fill="#FBBF24" />

      {/* Telemetry Progression Line */}
      <path
        d="M14 26L21 21L28 17L35 22L42 16L49 19"
        stroke="#F43F5E"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="49" cy="19" r="2" fill="#F43F5E" />

      {/* Status Blinking LED on Bezel */}
      <circle cx="32" cy="49" r="1.5" fill="#22C55E" />
    </svg>
  );
};
