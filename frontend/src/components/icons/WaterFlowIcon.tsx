import React from 'react';
import { DomainIconProps } from './types';

export const WaterFlowIcon: React.FC<DomainIconProps> = ({
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
      {/* Industrial Pipeline Flanges */}
      <rect x="6" y="38" width="4" height="18" rx="1" fill="#475569" />
      <rect x="54" y="38" width="4" height="18" rx="1" fill="#475569" />

      {/* Main Horizontal Water Delivery Pipe */}
      <rect x="10" y="41" width="44" height="12" fill="#0284C7" />
      {/* Pipe Highlight & Shadow */}
      <rect x="10" y="41" width="44" height="3" fill="#38BDF8" />
      <rect x="10" y="50" width="44" height="3" fill="#0369A1" />

      {/* Valve Body / Meter Housing */}
      <circle cx="32" cy="47" r="9" fill="#0369A1" />
      <circle cx="32" cy="47" r="7.5" fill="#E0F2FE" />
      <circle cx="32" cy="47" r="6" fill="#0284C7" />

      {/* Valve Stem & Handwheel */}
      <rect x="30" y="27" width="4" height="14" rx="1" fill="#475569" />
      {/* Red Industrial Handwheel */}
      <ellipse cx="32" cy="27" rx="14" ry="4" fill="#DC2626" />
      <ellipse cx="32" cy="27" rx="9" ry="2.5" fill="#EF4444" />
      <circle cx="32" cy="27" r="2.5" fill="#991B1B" />

      {/* Floating Dynamic Water Droplet above Meter */}
      <path
        d="M32 4C32 4 23 14 23 18C23 23 27 27 32 27C37 27 41 23 41 18C41 14 32 4 32 4Z"
        fill="#0EA5E9"
      />
      <path
        d="M32 7C32 7 25 15 25 18.5C25 22.5 28 25 32 25C36 25 39 22.5 39 18.5C39 15 32 7 32 7Z"
        fill="#38BDF8"
      />
      {/* Droplet Specular Reflection Glint */}
      <ellipse cx="28" cy="17" rx="1.5" ry="3.5" transform="rotate(-25 28 17)" fill="#FFFFFF" />
    </svg>
  );
};
