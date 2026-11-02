export type ElementType = 'wind' | 'fire' | 'earth' | 'lightning';

export type FighterId = 'kaze' | 'ignis' | 'tophia' | 'volt';

export type StageId = 'zephyr_dojo' | 'molten_forge' | 'storm_market';

export type GameMode = 'arcade' | 'training' | 'versus';

export type GameScreenState =
  | 'title'
  | 'select'
  | 'loading'
  | 'playing'
  | 'paused'
  | 'gameover';

export type MoveType =
  | 'light'
  | 'down_punch'
  | 'air_punch'
  | 'heavy'
  | 'elemental'
  | 'ultimate';

export type HitHeight = 'mid' | 'low' | 'overhead';

export type AttackVisualTag =
  | 'JAB'
  | 'CROSS'
  | 'FINISHER'
  | 'LOW LAUNCHER ▲'
  | 'AIR DRIBBLE'
  | 'OVERHEAD ▼'
  | 'ELEMENTAL'
  | 'ULTIMATE ★'
  | 'STAND BLOCK'
  | 'LOW BLOCK'
  | 'ARMOR HIT!'
  | 'CLASH ⚡'
  | 'WALL BOUNCE!'
  | 'COUNTER HIT!'
  | 'PUNISH!'
  | 'SWEEP ◢'
  | 'TECH ROLL';

export interface HitboxSpec {
  offsetX: number; // Forward offset from fighter center X
  offsetY: number; // Vertical center offset from fighter base Y
  width: number;   // 2D AABB width
  height: number;  // 2D AABB height
}

export interface BoundingBox2D {
  x: number;       // World center X
  y: number;       // World center Y
  width: number;   // Box width
  height: number;  // Box height
}

export interface MoveFrameData {
  id: string;
  name: string;
  type: MoveType;
  hitHeight: HitHeight;      // Street Fighter guard height ('mid' | 'low' | 'overhead')
  armorHits?: number;        // Super armor hits absorbed during startup/active (e.g. Ignis Brawler)
  startupFrames: number;     // at 60fps
  activeFrames: number;      // at 60fps
  recoveryFrames: number;    // at 60fps
  hitstunFrames: number;
  blockstunFrames: number;
  hitstopMs: number;
  damage: number;
  chipDamage: number;
  meterGain: number;
  meterCost: number;
  range: number;
  hitbox: HitboxSpec;        // Accurate 2D hitbox specification
  knockback: number;         // Pushback on hit
  blockPushback?: number;    // Pushback on block
  launchY: number;           // Vertical launch velocity on hit
  airDribblePopY?: number;   // Base vertical juggle pop when hitting an airborne opponent
  gustForce: number;         // Horizontal propulsion force on stage hazards
  spawnsHazard?: boolean;
  animStyle:
    | 'jab'
    | 'cross_punch'
    | 'finisher_punch'
    | 'low_punch'
    | 'air_spike'
    | 'spin_kick'
    | 'uppercut'
    | 'palm_blast'
    | 'axe_kick'
    | 'tonfa_slash'
    | 'super_flurry'
    | 'low_sweep';
  description: string;
}

export interface SkillNode {
  id: string;
  name: string;
  branch: 'combo' | 'elemental' | 'defense';
  tier: 1 | 2;
  cost: number;
  previewMove: MoveType;
  statTag: string;
  description: string;
  effect: {
    startupReductionFrames?: number;
    damageMultiplier?: number;
    gustForceBonus?: number;
    maxHpBonus?: number;
    meterGainMultiplier?: number;
    chipDamageBonus?: number;
  };
}

export interface FighterStatsRadar {
  speed: 1 | 2 | 3 | 4 | 5;
  range: 1 | 2 | 3 | 4 | 5;
  power: 1 | 2 | 3 | 4 | 5;
  defense: 1 | 2 | 3 | 4 | 5;
}

export interface FighterDefinition {
  id: FighterId;
  name: string;
  title: string;
  element: ElementType;
  martialStyle: string;
  stats: FighterStatsRadar;
  archetype: string;
  appearanceSummary: string;
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  hairColor: string;
  outfitColor: string;
  baseHp: number;
  walkSpeed: number;
  dashSpeed: number;
  jumpVelocity: number;
  passiveName: string;
  passiveDesc: string;
  moves: Record<MoveType, MoveFrameData>;
  skillTree: SkillNode[];
}

export interface StageDefinition {
  id: StageId;
  name: string;
  subtitle: string;
  skyColor: string;
  fogColor: string;
  groundColor: string;
  accentColor: string;
  hazardCount: number;
  spectatorDescription: string;
  climaxEventName: string;
}

export interface KeyBindingMap {
  jump: string;
  crouch: string;
  moveLeft: string;
  moveRight: string;
  lightAttack: string;
  heavyAttack: string;
  elementalSkill: string;
  ultimateArt: string;
  guardParry: string;
  dashStep: string;
  comboBreaker: string;
}

export interface GameSettings {
  masterVolume: number;
  sfxVolume: number;
  announcerVolume: number;
  muted: boolean;
  fov: number;
  celOutlines: boolean;
  showHitboxes: boolean;
  particleDensity: 'low' | 'medium' | 'high';
  cameraShake: boolean;
  dynamicZoom: boolean;
  p1Keys: KeyBindingMap;
  p2Keys: KeyBindingMap;
}

export type ActionState =
  | 'idle'
  | 'walk'
  | 'crouch'
  | 'jump'
  | 'dash'
  | 'startup'
  | 'active'
  | 'recovery'
  | 'guard'
  | 'parry'
  | 'hitstun'
  | 'blockstun'
  | 'knockdown'
  | 'breaker'
  | 'ko';

export interface FighterRuntimeState {
  id: FighterId;
  playerIndex: 1 | 2;
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  facingRight: boolean;
  facingAngle: number;
  grounded: boolean;
  crouching: boolean;
  walkCyclePhase: number;
  hp: number;
  maxHp: number;
  trailHp: number;
  meter: number;
  maxMeter: number;
  action: ActionState;
  actionTimerFrames: number;
  actionTotalFrames: number;
  currentMove: MoveFrameData | null;
  moveHasConnected: boolean;
  hurtbox: BoundingBox2D;
  activeHitbox: BoundingBox2D | null;
  punchChainStep: 1 | 2 | 3;
  punchChainTimer: number;
  juggleGravityScale: number;
  armorHitsRemaining: number;
  attackVisualTag: AttackVisualTag | null;
  attackVisualTimer: number;
  comboCount: number;
  comboDamage: number;
  comboDecayTimer: number;
  airDribbleCount: number;
  breakerCooldown: number;
  stunlockCount: number;
  stunlockImmunityTimer: number;
  lastFrameAdvantage: number;
  guardIntegrity: number;
  parryWindowFrames: number;
  bufferedMove: MoveType | null;
  bufferTimerFrames: number;
  hitFlashTimer: number;
  unlockedSkills: string[];
  aiArchetype: 'rushdown' | 'zoner' | 'counter' | 'dummy';
  aiDecisionTimer: number;
  /** AI reaction tempo multiplier (1 = normal, lower = faster decisions; Arcade Boss uses ~0.72). */
  aiTempo: number;
  /** Active color palette (0-3) used for skins & mirror-match differentiation. */
  paletteIndex: number;
  /** Brief gold flash on the striking limb when a hit opens a cancel window (combo timing feedback). */
  cancelFlashTimer: number;
  /** Limits Wall Bounce to once per combo (resets when the fighter leaves hitstun). */
  wallBouncedInCombo: boolean;
  /** Set when an Ultimate starts so the simulation can trigger the Super Flash freeze. */
  pendingSuperFlash: boolean;
  /** Arcade Boss "Overcharged" state: permanent double aura & buffed stats. */
  isOvercharged: boolean;
  /** True when the fighter is currently in Whiff Lag (extra recovery frames after missing an attack). */
  whiffRecoveryActive: boolean;
  /** Mandatory AI tactical breathing/spacing cooldown after completing a strike string or whiffing. */
  aiCooldownTimer: number;
  /** Height of the last strike that hit this fighter ('mid' | 'low' | 'overhead') for directional hitstun snap. */
  lastHitHeight: HitHeight;
  /** True when knocked down by a Sweep or Ultimate (disables directional Tech Roll). */
  hardKnockdown: boolean;
  /** Active directional Tech Roll direction (-1 = Left, 0 = None, 1 = Right) during knockdown wake-up. */
  wakeupRollDir: -1 | 0 | 1;
  /** Brief wake-up / Tech Roll invulnerability timer (seconds, flashes silver-white outline). */
  wakeupInvulnTimer: number;
}

export interface PropHazard {
  id: string;
  kind: 'lantern' | 'bamboo_crate' | 'stone_pillar' | 'wind_orb' | 'magma_brazier';
  x: number;
  z: number;
  vx: number;
  vz: number;
  radius: number;
  hp: number;
  maxHp: number;
  destroyed: boolean;
  respawnTimer: number;
  launchedByPlayer: 0 | 1 | 2;
  hitFlash: number;
  shatterCount: number;
}

export interface CombatSnapshot {
  p1: FighterRuntimeState;
  p2: FighterRuntimeState;
  hazards: PropHazard[];
  roundTimer: number;
  countdownTimer: number;
  hitstopTimerMs: number;
  stagePhase: 1 | 2 | 3;
  spectatorExcitement: number;
  totalPropsBroken: number;
  maxComboReached: number;
  lastEventBanner: string;
  bannerTimer: number;
  winner: 0 | 1 | 2;
  arcadeStageIndex: number;
  inputHistoryP1: string[];
  /** Super Flash freeze timer (seconds). While > 0 the simulation is paused for the cinematic. */
  cinematicTimer: number;
  /** Which player the cinematic camera focuses on (0 = none). */
  cinematicFocusPlayer: 0 | 1 | 2;
  /** K.O. slow-motion aftermath timer (seconds). */
  koSlowMoTimer: number;
  /** True during the Arcade Tower final boss fight. */
  isBossFight: boolean;
  /** High-contrast anime Impact Frame timer (seconds, ~0.055s on Counter Hit / Clash / Wall Bounce / Ultimate). */
  impactFrameTimer: number;
  /** Accent hex color used during the active Impact Frame flash. */
  impactFrameColorHex: number;
  /** Current round number in Best-of-3 match (1, 2, or 3). */
  currentRound: number;
  /** Rounds won by Player 1 (0 to 2). */
  p1RoundWins: number;
  /** Rounds won by Player 2 (0 to 2). */
  p2RoundWins: number;
  /** Inter-round transition timer (seconds) before resetting positions for the next round. */
  roundTransitionTimer: number;
}

export type ImpactSparkType = 'hit' | 'heavy' | 'block' | 'parry' | 'clash' | 'wall';

export type VoiceIntensity = 'light' | 'heavy' | 'ultimate' | 'hurt' | 'ko';

export interface FighterPalette {
  id: string;
  name: string;
  /** Three swatch colors shown in the select screen UI. */
  swatch: [string, string, string];
  /** Hex → Hex substitutions applied to the fighter's base model colors (empty = default look). */
  remap: Record<string, string>;
}
