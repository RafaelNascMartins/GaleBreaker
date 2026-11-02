import React from 'react';
import { ElementType, FighterId, MoveType, StageId } from '../game/types';

export type ExtendedMoveIconType =
  | MoveType
  | 'down_punch'
  | 'air_punch'
  | 'breaker';

interface DrawnMoveIconProps {
  type?: ExtendedMoveIconType;
  moveType?: ExtendedMoveIconType;
  fighterId?: FighterId;
  element?: ElementType;
  size?: number;
  className?: string;
}

const ELEMENT_COLORS: Record<
  FighterId,
  { primary: string; secondary: string; glow: string }
> = {
  kaze: { primary: '#10b981', secondary: '#a7f3d0', glow: '#34d399' },
  ignis: { primary: '#ef4444', secondary: '#fde047', glow: '#f97316' },
  tophia: { primary: '#f59e0b', secondary: '#fef08a', glow: '#10b981' },
  volt: { primary: '#06b6d4', secondary: '#facc15', glow: '#38bdf8' },
};

const ELEMENT_TO_FIGHTER: Record<ElementType, FighterId> = {
  wind: 'kaze',
  fire: 'ignis',
  earth: 'tophia',
  lightning: 'volt',
};

/**
 * Hand-drawn style cel-shaded SVG icons for every punch, down punch, air punch,
 * heavy kick, elemental special, ultimate art, and combo breaker.
 */
export const DrawnMoveIcon: React.FC<DrawnMoveIconProps> = ({
  type: rawType,
  moveType,
  fighterId,
  element,
  size,
  className = 'w-10 h-10',
}) => {
  const type = rawType || moveType || 'light';
  const resolvedFighterId =
    fighterId || (element ? ELEMENT_TO_FIGHTER[element] : 'kaze') || 'kaze';
  const c = ELEMENT_COLORS[resolvedFighterId] || ELEMENT_COLORS.kaze;

  return (
    <svg
      viewBox="0 0 64 64"
      width={size}
      height={size}
      className={size ? 'shrink-0' : className}
      role="img"
      aria-label={`${type} icon`}
    >
      {/* Cel-shaded backing badge */}
      <rect
        x="4"
        y="4"
        width="56"
        height="56"
        rx="8"
        fill="#0f172a"
        stroke="#090b10"
        strokeWidth="4"
      />
      <path
        d="M8 48 L56 16 L56 56 L8 56 Z"
        fill={c.primary}
        fillOpacity="0.22"
      />

      {type === 'light' && (
        <g>
          {/* Drawn Straight Fist + Speed Lines */}
          <path
            d="M8 24 H26 M6 32 H22 M10 40 H24"
            stroke={c.secondary}
            strokeWidth="3.5"
            strokeLinecap="round"
          />
          <path
            d="M24 20 H44 C49 20 52 24 52 32 C52 40 49 44 44 44 H24 Z"
            fill={c.primary}
            stroke="#090b10"
            strokeWidth="3.5"
          />
          <path
            d="M36 20 V44 M43 22 V42"
            stroke="#090b10"
            strokeWidth="2.5"
          />
          <polygon
            points="54,18 60,32 54,46 50,32"
            fill={c.secondary}
          />
        </g>
      )}

      {type === 'down_punch' && (
        <g>
          {/* Crouching Low Sweep / Downward Uppercut Fist + Ground Shockwave */}
          <path
            d="M14 48 Q32 56 50 48"
            fill="none"
            stroke={c.secondary}
            strokeWidth="4"
            strokeLinecap="round"
          />
          <path
            d="M22 14 L38 14 L44 38 C44 44 20 44 20 38 Z"
            fill={c.primary}
            stroke="#090b10"
            strokeWidth="3.5"
          />
          <polygon
            points="12,48 20,38 24,52"
            fill={c.secondary}
            stroke="#090b10"
            strokeWidth="2"
          />
          <polygon
            points="52,48 44,38 40,52"
            fill={c.secondary}
            stroke="#090b10"
            strokeWidth="2"
          />
        </g>
      )}

      {type === 'air_punch' && (
        <g>
          {/* Aerial Juggle Winged Fist + Upward Dribble Arrows */}
          <path
            d="M12 42 Q24 14 48 16"
            fill="none"
            stroke={c.secondary}
            strokeWidth="3.5"
            strokeDasharray="6 4"
          />
          <polygon
            points="14,26 28,12 26,28"
            fill="#f8fafc"
            stroke="#090b10"
            strokeWidth="2.5"
          />
          <circle
            cx="38"
            cy="32"
            r="13"
            fill={c.primary}
            stroke="#090b10"
            strokeWidth="3.5"
          />
          <path
            d="M46 20 L56 12 M50 30 L58 26 M46 42 L56 46"
            stroke={c.secondary}
            strokeWidth="3.5"
            strokeLinecap="round"
          />
        </g>
      )}

      {type === 'heavy' && (
        <g>
          {/* Spinning Hurricane Boot / Crushing Axe Kick Arc */}
          <path
            d="M12 44 C12 16 48 12 54 34"
            fill="none"
            stroke={c.glow}
            strokeWidth="6"
            strokeLinecap="round"
          />
          <polygon
            points="22,38 46,24 54,36 30,48"
            fill={c.primary}
            stroke="#090b10"
            strokeWidth="3.5"
          />
          <circle cx="48" cy="30" r="5" fill={c.secondary} />
        </g>
      )}

      {type === 'elemental' && (
        <g>
          {/* Drawn Elemental Vortex / Flame / Monolith / Lightning Wave */}
          <circle
            cx="32"
            cy="32"
            r="18"
            fill="none"
            stroke={c.primary}
            strokeWidth="4"
            strokeDasharray="18 8"
          />
          <path
            d="M16 32 C24 14, 40 14, 48 32 C40 50, 24 50, 16 32 Z"
            fill={c.glow}
            stroke="#090b10"
            strokeWidth="3"
          />
          <circle cx="32" cy="32" r="7" fill={c.secondary} />
        </g>
      )}

      {type === 'ultimate' && (
        <g>
          {/* Explosive Super Starburst Emblem */}
          <polygon
            points="32,6 39,22 56,18 44,32 56,46 39,42 32,58 25,42 8,46 20,32 8,18 25,22"
            fill={c.primary}
            stroke="#090b10"
            strokeWidth="3"
          />
          <circle
            cx="32"
            cy="32"
            r="9"
            fill={c.secondary}
            stroke="#090b10"
            strokeWidth="2.5"
          />
        </g>
      )}

      {type === 'breaker' && (
        <g>
          {/* Shattered Chain / Shield Burst for Combo Breaker */}
          <polygon
            points="32,8 52,18 48,44 32,56 16,44 12,18"
            fill="#f59e0b"
            stroke="#090b10"
            strokeWidth="3.5"
          />
          <path
            d="M22 20 L36 32 L26 36 L42 48"
            fill="none"
            stroke="#090b10"
            strokeWidth="4"
            strokeLinecap="round"
          />
        </g>
      )}
    </svg>
  );
};

interface CharacterAttackIllustrationProps {
  fighterId: FighterId;
  activeMove?: ExtendedMoveIconType;
  moveType?: ExtendedMoveIconType;
  className?: string;
}

/**
 * Large Visual Illustration showing the drawn character executing the selected move
 * with visible attack trajectory arcs and accurate hitbox/hurtbox overlays.
 */
export const CharacterAttackIllustration: React.FC<
  CharacterAttackIllustrationProps
> = ({ fighterId, activeMove: rawActiveMove, moveType, className }) => {
  const activeMove = rawActiveMove || moveType || 'light';
  const c = ELEMENT_COLORS[fighterId] || ELEMENT_COLORS.kaze;

  return (
    <svg
      viewBox="0 0 360 220"
      className={className ? `${className} cel-border bg-slate-950` : 'w-full h-auto cel-border bg-slate-950'}
      role="img"
      aria-label={`${fighterId} performing ${activeMove}`}
    >
      <defs>
        <radialGradient id="preview-glow" cx="55%" cy="50%" r="50%">
          <stop offset="0%" stopColor={c.primary} stopOpacity="0.45" />
          <stop offset="100%" stopColor="#090b10" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Dojo Grid Background */}
      <rect width="360" height="220" fill="#090b10" />
      <rect width="360" height="220" fill="url(#preview-glow)" />
      <line
        x1="0"
        y1="184"
        x2="360"
        y2="184"
        stroke="#334155"
        strokeWidth="3"
      />

      {/* Hurtbox visualization (Green translucent box around fighter body) */}
      <rect
        x={activeMove === 'down_punch' ? '82' : '86'}
        y={
          activeMove === 'air_punch'
            ? '38'
            : activeMove === 'down_punch'
            ? '112'
            : '68'
        }
        width="54"
        height={activeMove === 'down_punch' ? '70' : '112'}
        fill="#10b981"
        fillOpacity="0.12"
        stroke="#10b981"
        strokeWidth="1.5"
        strokeDasharray="4 4"
      />

      {/* Drawn Character Silhouette & Unique Hair/Clothes */}
      <g
        transform={
          activeMove === 'air_punch'
            ? 'translate(0, -34)'
            : activeMove === 'down_punch'
            ? 'translate(0, 26)'
            : 'translate(0, 0)'
        }
      >
        {/* Head & Distinct Hair */}
        {fighterId === 'kaze' && (
          <g>
            {/* Flowing ponytail + red hachimaki */}
            <path
              d="M95 72 Q62 65 48 88 Q68 86 95 78 Z"
              fill="#e2e8f0"
              stroke="#090b10"
              strokeWidth="3"
            />
            <path
              d="M92 78 Q58 88 42 110"
              stroke="#ef4444"
              strokeWidth="5"
              strokeLinecap="round"
            />
          </g>
        )}
        {fighterId === 'ignis' && (
          <polygon
            points="92,72 86,44 104,58 114,38 124,58 138,46 128,74"
            fill="#f97316"
            stroke="#090b10"
            strokeWidth="3"
          />
        )}
        {fighterId === 'tophia' && (
          <g>
            <circle
              cx="96"
              cy="60"
              r="11"
              fill="#1e293b"
              stroke="#f59e0b"
              strokeWidth="2.5"
            />
            <circle
              cx="124"
              cy="60"
              r="11"
              fill="#1e293b"
              stroke="#f59e0b"
              strokeWidth="2.5"
            />
          </g>
        )}
        {fighterId === 'volt' && (
          <polygon
            points="94,72 88,48 106,60 118,42 126,62 142,50 130,74"
            fill="#facc15"
            stroke="#090b10"
            strokeWidth="3"
          />
        )}

        {/* Fighter Head */}
        <circle
          cx="112"
          cy="78"
          r="16"
          fill="#fde68a"
          stroke="#090b10"
          strokeWidth="3.5"
        />
        {/* Visor / Headband */}
        <rect
          x="108"
          y="72"
          width="18"
          height="6"
          fill={fighterId === 'volt' ? '#06b6d4' : '#ef4444'}
        />

        {/* Torso Clothes */}
        <polygon
          points="92,96 134,96 128,144 98,144"
          fill={c.primary}
          stroke="#090b10"
          strokeWidth="3.5"
        />

        {/* Legs */}
        <path
          d="M102 144 L92 182 M122 144 L138 182"
          stroke="#f8fafc"
          strokeWidth="12"
          strokeLinecap="round"
        />

        {/* Extending Attack Limb */}
        <path
          d={
            activeMove === 'down_punch'
              ? 'M126 112 L195 148'
              : activeMove === 'air_punch'
              ? 'M126 104 L204 126'
              : 'M126 106 L208 102'
          }
          stroke={c.secondary}
          strokeWidth="14"
          strokeLinecap="round"
        />
      </g>

      {/* Active Red Hitbox Rectangle + Elemental Slash Effect */}
      <g>
        <rect
          x="172"
          y={
            activeMove === 'down_punch'
              ? '126'
              : activeMove === 'air_punch'
              ? '64'
              : '68'
          }
          width={
            activeMove === 'elemental' || activeMove === 'ultimate'
              ? '148'
              : '96'
          }
          height={activeMove === 'down_punch' ? '52' : '68'}
          fill="#ef4444"
          fillOpacity="0.24"
          stroke="#ef4444"
          strokeWidth="2.5"
        />
        <path
          d={
            activeMove === 'down_punch'
              ? 'M176 164 Q230 176 264 136'
              : activeMove === 'air_punch'
              ? 'M176 74 Q236 88 258 128'
              : 'M180 72 Q265 102 184 134'
          }
          fill="none"
          stroke={c.secondary}
          strokeWidth="7"
          strokeLinecap="round"
        />
        <circle
          cx="228"
          cy={
            activeMove === 'down_punch'
              ? '152'
              : activeMove === 'air_punch'
              ? '96'
              : '102'
          }
          r="18"
          fill={c.primary}
          fillOpacity="0.65"
        />
      </g>

      {/* Minimal Visual Legend Badges */}
      <g transform="translate(14, 14)">
        <rect
          x="0"
          y="0"
          width="74"
          height="20"
          rx="3"
          fill="#090b10"
          stroke="#10b981"
          strokeWidth="1.5"
        />
        <text
          x="37"
          y="14"
          textAnchor="middle"
          fill="#10b981"
          fontSize="10"
          fontFamily="JetBrains Mono, monospace"
          fontWeight="700"
        >
          HURTBOX
        </text>
      </g>
      <g transform="translate(96, 14)">
        <rect
          x="0"
          y="0"
          width="74"
          height="20"
          rx="3"
          fill="#090b10"
          stroke="#ef4444"
          strokeWidth="1.5"
        />
        <text
          x="37"
          y="14"
          textAnchor="middle"
          fill="#ef4444"
          fontSize="10"
          fontFamily="JetBrains Mono, monospace"
          fontWeight="700"
        >
          HITBOX
        </text>
      </g>
    </svg>
  );
};

interface StagePreviewCardArtProps {
  stageId: StageId;
  className?: string;
}

/**
 * Visual Stage Artwork for Mountain Sanctuary (bright blue sky),
 * Crimson Anvil (giant anvil in lava lake + dark sky + red sun),
 * and Golden Arabic Bazaar (referencing the user's attached bazaar image).
 */
export const StagePreviewCardArt: React.FC<StagePreviewCardArtProps> = ({
  stageId,
  className = 'w-full h-24',
}) => {
  if (stageId === 'storm_market') {
    return (
      <svg
        viewBox="0 0 240 100"
        className={`${className} block`}
        role="img"
        aria-label="Golden Arabic Bazaar"
      >
        {/* Warm Golden Amber Vault Background */}
        <rect width="240" height="100" fill="#78350f" />
        {/* Vaulted Golden Bazaar Archways */}
        <path
          d="M 10 100 A 110 85 0 0 1 230 100"
          fill="#b45309"
          stroke="#fde047"
          strokeWidth="5"
        />
        <path
          d="M 38 100 A 82 66 0 0 1 202 100"
          fill="#d97706"
          stroke="#292524"
          strokeWidth="5"
          strokeDasharray="10 8"
        />
        <path
          d="M 68 100 A 52 46 0 0 1 172 100"
          fill="#f59e0b"
          stroke="#fef08a"
          strokeWidth="4"
        />
        {/* Glowing Palace Portal & Hanging Brass Lanterns */}
        <circle cx="120" cy="68" r="22" fill="#fef08a" />
        <line x1="75" y1="14" x2="75" y2="36" stroke="#78350f" strokeWidth="2" />
        <polygon points="75,32 82,42 75,52 68,42" fill="#fef08a" stroke="#090b10" strokeWidth="2" />
        <line x1="120" y1="8" x2="120" y2="28" stroke="#78350f" strokeWidth="2" />
        <polygon points="120,24 128,36 120,48 112,36" fill="#fef08a" stroke="#090b10" strokeWidth="2" />
        <line x1="165" y1="14" x2="165" y2="36" stroke="#78350f" strokeWidth="2" />
        <polygon points="165,32 172,42 165,52 158,42" fill="#fef08a" stroke="#090b10" strokeWidth="2" />
        {/* Golden Sandstone Floor & Royal Carpet Runner */}
        <rect x="0" y="82" width="240" height="18" fill="#f59e0b" />
        <rect x="36" y="86" width="168" height="10" fill="#991b1b" stroke="#fde047" strokeWidth="2" />
        {/* Spice Mounds */}
        <polygon points="18,84 32,68 46,84" fill="#facc15" stroke="#090b10" strokeWidth="2" />
        <polygon points="194,84 208,68 222,84" fill="#ef4444" stroke="#090b10" strokeWidth="2" />
      </svg>
    );
  }

  if (stageId === 'zephyr_dojo') {
    return (
      <svg
        viewBox="0 0 240 100"
        className={`${className} block`}
        role="img"
        aria-label="Mountain Sanctuary"
      >
        {/* Bright Blue Mountain Sky */}
        <rect width="240" height="100" fill="#38bdf8" />
        {/* Sun & White Clouds */}
        <circle cx="195" cy="24" r="14" fill="#fef08a" />
        <ellipse cx="55" cy="26" rx="26" ry="8" fill="#ffffff" fillOpacity="0.85" />
        <ellipse cx="135" cy="18" rx="32" ry="9" fill="#ffffff" fillOpacity="0.85" />
        {/* High Snow-Capped Mountains */}
        <polygon points="0,100 48,28 98,100" fill="#475569" />
        <polygon points="34,49 48,28 62,49" fill="#f8fafc" />
        <polygon points="70,100 130,18 190,100" fill="#64748b" />
        <polygon points="111,44 130,18 149,44" fill="#ffffff" />
        <polygon points="150,100 205,34 240,100" fill="#475569" />
        {/* Sanctuary Torii & Cliff Platform */}
        <rect x="0" y="82" width="240" height="18" fill="#cbd5e1" />
        <rect x="102" y="48" width="6" height="34" fill="#dc2626" />
        <rect x="132" y="48" width="6" height="34" fill="#dc2626" />
        <rect x="94" y="44" width="52" height="6" fill="#0f172a" />
      </svg>
    );
  }

  return (
    <svg
      viewBox="0 0 240 100"
      className={`${className} block`}
      role="img"
      aria-label="Crimson Anvil"
    >
      {/* Dark Volcanic Background */}
      <rect width="240" height="100" fill="#090505" />
      {/* Giant Glowing Red Sun */}
      <circle cx="120" cy="36" r="26" fill="#dc2626" />
      <circle cx="120" cy="36" r="20" fill="#ef4444" />
      {/* Lake of Molten Lava */}
      <rect x="0" y="74" width="240" height="26" fill="#ea580c" />
      <path
        d="M0 82 Q60 76 120 82 T240 82"
        stroke="#fde047"
        strokeWidth="3"
        fill="none"
      />
      {/* Colossal Giant Iron Anvil in center */}
      <polygon
        points="88,78 152,78 142,58 98,58"
        fill="#1e293b"
        stroke="#090b10"
        strokeWidth="2.5"
      />
      <polygon
        points="64,44 176,44 156,60 84,60"
        fill="#334155"
        stroke="#090b10"
        strokeWidth="2.5"
      />
    </svg>
  );
};
