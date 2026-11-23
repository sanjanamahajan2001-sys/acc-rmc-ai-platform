import React from 'react';
import { DomainIconProps } from './types';

export const QualitySealIcon: React.FC<DomainIconProps> = ({
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
      {/* Ribbon Tails (Emerald / Teal) */}
      <path d="M23 44L14 59L25 54L31 59L29 44H23Z" fill="#047857" />
      <path d="M41 44L50 59L39 54L33 59L35 44H41Z" fill="#059669" />

      {/* Gold Rosette Star Outer Notches */}
      <circle cx="32" cy="28" r="22" fill="#F59E0B" />
      <circle cx="32" cy="28" r="20" fill="#FBBF24" />

      {/* Scalloped Edge Teeth */}
      <path
        d="M32 5L36 10L42 7L44 13L50 12L50 18L56 19L54 25L59 28L55 33L58 38L53 41L54 47L48 48L47 54L41 53L38 58L33 55L28 58L26 53L20 54L19 48L13 47L14 41L9 38L12 33L8 28L13 25L11 19L17 18L17 12L23 13L25 7L31 10L32 5Z"
        fill="#D97706"
        opacity="0.25"
      />

      {/* Inner Rosette Body */}
      <circle cx="32" cy="28" r="17" fill="#F59E0B" />
      <circle cx="32" cy="28" r="15" fill="#FFFFFF" />

      {/* Certified Laurel / Ring Accent */}
      <circle cx="32" cy="28" r="13" stroke="#FDE68A" strokeWidth="1.5" strokeDasharray="3 2" fill="none" />

      {/* Bold Green Checkmark */}
      <path
        d="M24 28.5L29.5 34L40 22"
        stroke="#10B981"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};
