import React from 'react';
import { DomainIconProps } from './types';

export const MixerTruckIcon: React.FC<DomainIconProps> = ({
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
      {/* Chassis Beam */}
      <rect x="6" y="44" width="52" height="5" rx="1.5" fill="#334155" />

      {/* Fuel Tank & Battery Box */}
      <rect x="23" y="43" width="10" height="5" rx="1" fill="#64748B" />

      {/* Rear Discharge Chute */}
      <path d="M4 33L10 38H14L7 30L4 33Z" fill="#64748B" />
      <path d="M7 38L10 44H6L3 38H7Z" fill="#94A3B8" />

      {/* Drum Support Stand */}
      <path d="M12 44L17 32H20L15 44H12Z" fill="#475569" />
      <path d="M34 44L32 34H35L37 44H34Z" fill="#475569" />

      {/* Rotating Mixer Drum (Tilted) */}
      <g transform="rotate(-14 26 31)">
        {/* Main Drum Body */}
        <ellipse cx="26" cy="31" rx="17" ry="11" fill="#F8FAFC" />
        <path
          d="M10 31C10 25.5 17 21 26 21C35 21 42 25.5 42 31C42 36.5 35 41 26 41C17 41 10 36.5 10 31Z"
          fill="#F1F5F9"
          stroke="#CBD5E1"
          strokeWidth="1"
        />
        {/* Spiral Mixing Stripes (High-Visibility Safety Orange) */}
        <path
          d="M14 28C19 22 24 23 29 27C34 31 38 31 41 30"
          stroke="#EA580C"
          strokeWidth="3.5"
          strokeLinecap="round"
        />
        <path
          d="M12 34C17 28 22 29 27 33C32 37 36 37 39 36"
          stroke="#F97316"
          strokeWidth="3"
          strokeLinecap="round"
        />
        {/* Drum Rear Cone End */}
        <path d="M8 28L12 26V36L8 34C7.5 32 7.5 30 8 28Z" fill="#94A3B8" />
        <ellipse cx="9" cy="31" rx="1.5" ry="3.5" fill="#475569" />
      </g>

      {/* Water Tank behind Cab */}
      <rect x="38" y="27" width="4" height="15" rx="1.5" fill="#0284C7" />

      {/* Truck Cab Structure */}
      <path
        d="M42 24H52C53.5 24 55 25.5 55.5 27L58.5 36.5C59 37.5 59 38.5 59 40V46C59 47 58 48 57 48H42V24Z"
        fill="#EA580C"
      />
      {/* Cab Roof Deflector / Sun Visor */}
      <path d="M41 23H53L55 26H41V23Z" fill="#C2410C" />

      {/* Windshield */}
      <path
        d="M48 26H52.5C53.5 26 54.3 26.8 54.7 27.8L56.8 34H48V26Z"
        fill="#93C5FD"
        stroke="#60A5FA"
        strokeWidth="0.8"
      />
      {/* Side Window */}
      <rect x="43" y="26" width="4" height="8" rx="0.5" fill="#BAE6FD" />

      {/* Headlight (Warm Amber/Yellow) */}
      <rect x="56.5" y="40" width="2.5" height="4" rx="1" fill="#FDE047" />

      {/* Front Chrome Bumper */}
      <path d="M56 44H60C60.5 44 61 44.5 61 45V47C61 47.5 60.5 48 60 48H56V44Z" fill="#CBD5E1" />

      {/* Cab Door Line & Handle */}
      <line x1="48" y1="35" x2="48" y2="46" stroke="#C2410C" strokeWidth="1" />
      <rect x="44" y="37" width="2.5" height="1" rx="0.5" fill="#1E293B" />

      {/* Mudguards */}
      <path d="M10 44C10 40 16 40 16 44" stroke="#1E293B" strokeWidth="2.5" strokeLinecap="round" fill="none" />
      <path d="M21 44C21 40 27 40 27 44" stroke="#1E293B" strokeWidth="2.5" strokeLinecap="round" fill="none" />
      <path d="M47 44C47 40 55 40 55 44" stroke="#1E293B" strokeWidth="2.5" strokeLinecap="round" fill="none" />

      {/* Wheels - Triple Axle Heavy Industrial */}
      {/* Rear Wheel 1 */}
      <circle cx="13" cy="47" r="5.5" fill="#0F172A" />
      <circle cx="13" cy="47" r="2.8" fill="#94A3B8" />
      <circle cx="13" cy="47" r="1.2" fill="#334155" />

      {/* Rear Wheel 2 */}
      <circle cx="24" cy="47" r="5.5" fill="#0F172A" />
      <circle cx="24" cy="47" r="2.8" fill="#94A3B8" />
      <circle cx="24" cy="47" r="1.2" fill="#334155" />

      {/* Front Steer Wheel */}
      <circle cx="51" cy="47" r="5.5" fill="#0F172A" />
      <circle cx="51" cy="47" r="2.8" fill="#94A3B8" />
      <circle cx="51" cy="47" r="1.2" fill="#334155" />
    </svg>
  );
};
