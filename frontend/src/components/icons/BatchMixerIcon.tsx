import React from 'react';
import { DomainIconProps } from './types';

export const BatchMixerIcon: React.FC<DomainIconProps> = ({
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
      {/* Heavy Base Supports */}
      <rect x="8" y="52" width="48" height="6" rx="2" fill="#1E293B" />
      <path d="M12 52L17 40H21L17 52H12Z" fill="#334155" />
      <path d="M52 52L47 40H43L47 52H52Z" fill="#334155" />

      {/* Mixer Drum Body (Industrial Emerald / Forest Green) */}
      <rect x="14" y="20" width="36" height="24" rx="4" fill="#059669" />
      <path d="M14 20H50V26H14V20Z" fill="#10B981" />
      <path d="M14 38H50V44H14V38Z" fill="#047857" />

      {/* Rotating Drive Gear on Left */}
      <circle cx="14" cy="32" r="7" fill="#475569" />
      <circle cx="14" cy="32" r="4" fill="#94A3B8" />
      <circle cx="14" cy="32" r="2" fill="#1E293B" />
      {/* Gear Teeth */}
      <rect x="12.5" y="23" width="3" height="3" fill="#475569" />
      <rect x="12.5" y="38" width="3" height="3" fill="#475569" />
      <rect x="5.5" y="30.5" width="3" height="3" fill="#475569" />

      {/* Mixer View Window / Inspection Port */}
      <circle cx="32" cy="32" r="7" fill="#1E293B" />
      <circle cx="32" cy="32" r="5.5" fill="#F8FAFC" />

      {/* Twin-Shaft Mixing Spiral Paddle Blades inside View Window */}
      <path
        d="M28 29C28 29 32 31 35 29C35 32 33 34 31 34C29 34 28 31 28 29Z"
        fill="#059669"
      />
      <circle cx="32" cy="32" r="1.5" fill="#D97706" />

      {/* Top Batch Feed Chute */}
      <path d="M25 10H39L35 20H29L25 10Z" fill="#475569" />
      <rect x="23" y="8" width="18" height="3" rx="1" fill="#64748B" />

      {/* Electric Motor Housing on Right */}
      <rect x="49" y="26" width="9" height="12" rx="2" fill="#1E293B" />
      <line x1="51" y1="28" x2="51" y2="36" stroke="#475569" strokeWidth="1" />
      <line x1="53" y1="28" x2="53" y2="36" stroke="#475569" strokeWidth="1" />
      <line x1="55" y1="28" x2="55" y2="36" stroke="#475569" strokeWidth="1" />
    </svg>
  );
};
