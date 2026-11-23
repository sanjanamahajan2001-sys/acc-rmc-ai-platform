import React from 'react';
import { DomainIconProps } from './types';

export const BatchPlantIcon: React.FC<DomainIconProps> = ({
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
      {/* Ground Foundation */}
      <rect x="4" y="52" width="56" height="4" rx="1" fill="#334155" />

      {/* Main Plant Building (Industrial Brick Red / Coral Rose as in Snippet 2) */}
      <path d="M18 28H44V52H18V28Z" fill="#E11D48" />
      <path d="M18 28L31 19L44 28V52H18V28Z" fill="#BE123C" />

      {/* Sawtooth Roof / Shed on Right */}
      <path d="M44 36L52 30V52H44V36Z" fill="#9F1239" />
      <path d="M52 38L58 33V52H52V38Z" fill="#881337" />

      {/* Industrial Chimneys / Exhaust Stacks with White Tops */}
      {/* Stack 1 */}
      <path d="M22 14H26V28H22V14Z" fill="#FB7185" />
      <rect x="21" y="12" width="6" height="3" rx="0.8" fill="#FFF1F2" />
      {/* Smoke puffs from Stack 1 */}
      <circle cx="24" cy="8" r="2.5" fill="#E2E8F0" opacity="0.8" />
      <circle cx="26" cy="4" r="2" fill="#CBD5E1" opacity="0.6" />

      {/* Stack 2 */}
      <path d="M30 16H34V28H30V16Z" fill="#FB7185" />
      <rect x="29" y="14" width="6" height="3" rx="0.8" fill="#FFF1F2" />

      {/* Cement Storage Silo on Left */}
      <rect x="6" y="20" width="11" height="24" rx="2" fill="#3B82F6" />
      <path d="M6 22C6 19 17 19 17 22V20H6V22Z" fill="#60A5FA" />
      <path d="M6 44L11.5 50L17 44H6Z" fill="#1D4ED8" />
      {/* Silo Legs */}
      <line x1="8" y1="50" x2="8" y2="52" stroke="#475569" strokeWidth="2" />
      <line x1="15" y1="50" x2="15" y2="52" stroke="#475569" strokeWidth="2" />
      {/* Silo Band Rings */}
      <line x1="6" y1="28" x2="17" y2="28" stroke="#60A5FA" strokeWidth="1" />
      <line x1="6" y1="36" x2="17" y2="36" stroke="#60A5FA" strokeWidth="1" />

      {/* Plant Windows Grid */}
      <rect x="22" y="33" width="5" height="5" rx="0.5" fill="#FEF08A" />
      <rect x="30" y="33" width="5" height="5" rx="0.5" fill="#FEF08A" />
      <rect x="37" y="33" width="5" height="5" rx="0.5" fill="#FEF08A" />

      <rect x="22" y="41" width="5" height="5" rx="0.5" fill="#FEF08A" />
      <rect x="30" y="41" width="5" height="5" rx="0.5" fill="#FEF08A" />
      <rect x="37" y="41" width="5" height="5" rx="0.5" fill="#FEF08A" />

      {/* Plant Truck Bay / Loading Chute Door */}
      <path d="M27 47H35V52H27V47Z" fill="#1E293B" />
      <path d="M28 47C28 45 34 45 34 47V52H28V47Z" fill="#0F172A" />

      {/* Diagonal Incline Conveyor Belt */}
      <line x1="12" y1="46" x2="22" y2="28" stroke="#475569" strokeWidth="2.5" />
      <line x1="12" y1="48" x2="22" y2="30" stroke="#94A3B8" strokeWidth="1" />
    </svg>
  );
};
