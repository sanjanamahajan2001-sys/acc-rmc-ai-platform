import React from 'react';
import { DomainIconProps } from './types';

export const HourglassTimerIcon: React.FC<DomainIconProps> = ({
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
      {/* Top Wood/Slate Plate */}
      <rect x="12" y="8" width="40" height="5" rx="2" fill="#1E293B" />
      <rect x="16" y="13" width="32" height="2" fill="#475569" />

      {/* Bottom Wood/Slate Plate */}
      <rect x="12" y="51" width="40" height="5" rx="2" fill="#1E293B" />
      <rect x="16" y="49" width="32" height="2" fill="#475569" />

      {/* Side Pillar Supports */}
      <rect x="14" y="13" width="3" height="38" rx="1" fill="#64748B" />
      <rect x="47" y="13" width="3" height="38" rx="1" fill="#64748B" />

      {/* Glass Bulb Outline */}
      <path
        d="M19 15H45C45 23 37 28 34 32C37 36 45 41 45 49H19C19 41 27 36 30 32C27 28 19 23 19 15Z"
        fill="#F0F9FF"
        stroke="#BAE6FD"
        strokeWidth="1.5"
      />

      {/* Upper Bulb Sand (Depleting) */}
      <path
        d="M23 20H41C40 25 35 28 32 30C29 28 24 25 23 20Z"
        fill="#F59E0B"
      />
      {/* Upper Sand Highlight */}
      <path d="M25 20H39C38 23 35 25 32 26C29 25 26 23 25 20Z" fill="#FBBF24" />

      {/* Sand Stream Falling Through Center Neck */}
      <line x1="32" y1="30" x2="32" y2="44" stroke="#D97706" strokeWidth="2" strokeDasharray="1 1" />

      {/* Lower Bulb Sand (Accumulating Pile) */}
      <path
        d="M21 48C21 44 26 40 32 39C38 40 43 44 43 48H21Z"
        fill="#F59E0B"
      />
      <path
        d="M25 48C25 45 28 42 32 41C36 42 39 45 39 48H25Z"
        fill="#FBBF24"
      />

      {/* Glass Highlight Glint */}
      <path
        d="M21 18C21 23 24 26 27 28"
        stroke="#FFFFFF"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <path
        d="M22 46C22 43 24 40 26 38"
        stroke="#FFFFFF"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
    </svg>
  );
};
