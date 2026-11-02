import { getArcadeStageSpec } from './arcadeTower';
import {
  FIGHTERS,
  getEffectiveMaxHp,
  getEffectiveMoveData,
  resolveMirrorPaletteIndex,
  STAGES,
} from './fighters';
import {
  AttackVisualTag,
  BoundingBox2D,
  CombatSnapshot,
  FighterId,
  FighterRuntimeState,
  GameMode,
  ImpactSparkType,
  MoveFrameData,
  MoveType,
  PropHazard,
  StageId,
  VoiceIntensity,
} from './types';

export interface PlayerFrameInput {
  moveX: number; // -1 (Left) to +1 (Right)
  jumpJustPressed: boolean;
  crouchHeld: boolean;
  guardHeld: boolean;
  guardJustPressed: boolean;
  dashJustPressed: boolean;
  breakerJustPressed?: boolean;
  attackJustPressed: MoveType | null;
}

export interface StepEvents {
  hitTriggered: boolean;
  blockTriggered: boolean;
  heavyHit: boolean;
  parryTriggered: boolean;
  breakerTriggered: boolean;
  stunlockEscapeTriggered: boolean;
  airDribbleTriggered: boolean;
  launcherTriggered: boolean;
  armorAbsorbed: boolean;
  gustTriggered: boolean;
  hazardShattered: boolean;
  stagePhaseChanged: boolean;
  koTriggered: boolean;
  whiffTriggered: boolean;
  clashTriggered: boolean;
  wallBounceTriggered: boolean;
  superFreezeTriggered: boolean;
  cancelConfirmTriggered: boolean;
  counterHitTriggered: boolean;
  punishTriggered: boolean;
  floorCrackTriggered: boolean;
  voiceTriggered: VoiceIntensity | null;
  voiceFighterId: FighterId | null;
  impactSparkType: ImpactSparkType | null;
  attackerId: FighterId | null;
  impactX: number;
  impactY: number;
  impactZ: number;
}

const STAGE_HALF_WIDTH = 9.5;
const GRAVITY = 28.0;
export const COMBO_BREAKER_COOLDOWN_SECONDS = 6.0;
export const MAX_STUNLOCK_HITS_BEFORE_ESCAPE = 5;
export const STUNLOCK_IMMUNITY_DURATION_SECONDS = 2.0;
export const JUGGLE_GRAVITY_STEP = 0.24;
export const MAX_AIR_DRIBBLES_PER_COMBO = 3;

export function isHoldingBackDirection(
  fighter: FighterRuntimeState,
  moveX: number
): boolean {
  return fighter.facingRight ? moveX < -0.15 : moveX > 0.15;
}

export function isOpponentThreatening(
  fighter: FighterRuntimeState,
  opponent: FighterRuntimeState,
  hazards: PropHazard[]
): boolean {
  const dist = Math.abs(opponent.x - fighter.x);
  const oppMoveRange = opponent.currentMove?.range ?? 3.5;
  if (
    (opponent.action === 'startup' || opponent.action === 'active') &&
    dist <= oppMoveRange + 2.4
  ) {
    return true;
  }
  for (const h of hazards) {
    if (!h.destroyed && Math.abs(h.vx) > 3.5 && Math.abs(h.x - fighter.x) < 3.4) {
      return true;
    }
  }
  return false;
}

export function canDirectionalGuardBlockMove(
  crouchingGuard: boolean,
  move: MoveFrameData
): boolean {
  if (move.hitHeight === 'low') {
    // Low attacks (like Down Punch Launcher ▲) MUST be blocked crouching (Down + Back)
    return crouchingGuard === true;
  }
  if (move.hitHeight === 'overhead') {
    // Overhead attacks (like Heavy Kick ▼ & Air Punch) MUST be blocked standing (Back)
    return crouchingGuard === false;
  }
  // Mid attacks are blocked by both Standing and Crouching Guard
  return true;
}

export function computeFighterHurtbox(fighter: FighterRuntimeState): BoundingBox2D {
  if (fighter.crouching && fighter.grounded) {
    return {
      x: fighter.x,
      y: fighter.y + 0.68,
      width: 1.15,
      height: 1.36,
    };
  }
  if (!fighter.grounded) {
    return {
      x: fighter.x,
      y: fighter.y + 1.08,
      width: 1.08,
      height: 1.88,
    };
  }
  return {
    x: fighter.x,
    y: fighter.y + 1.05,
    width: 1.05,
    height: 2.1,
  };
}

export function computeFighterActiveHitbox(
  fighter: FighterRuntimeState
): BoundingBox2D | null {
  if (fighter.action !== 'active' || !fighter.currentMove) {
    return null;
  }
  const spec = fighter.currentMove.hitbox;
  const dirX = fighter.facingRight ? 1 : -1;
  return {
    x: fighter.x + dirX * spec.offsetX,
    y: fighter.y + spec.offsetY,
    width: spec.width,
    height: spec.height,
  };
}

export function boxesOverlap2D(a: BoundingBox2D, b: BoundingBox2D): boolean {
  return (
    Math.abs(a.x - b.x) * 2 <= a.width + b.width &&
    Math.abs(a.y - b.y) * 2 <= a.height + b.height
  );
}

export const CONTACT_STICK_DIST = 1.05;

export function resolveContextualMoveType(
  fighter: FighterRuntimeState,
  requestedMove: MoveType,
  crouchHeld: boolean
): MoveType {
  if (requestedMove === 'light') {
    if (!fighter.grounded) {
      return 'air_punch';
    }
    if (crouchHeld || fighter.crouching) {
      return 'down_punch';
    }
    return 'light';
  }
  return requestedMove;
}

export function createInitialFighterState(
  fighterId: FighterId,
  playerIndex: 1 | 2,
  unlockedSkills: string[],
  aiArchetype: FighterRuntimeState['aiArchetype'] = 'rushdown',
  paletteIndex = 0,
  aiTempo = 1.0,
  isOvercharged = false,
  hpMultiplier = 1.0,
  startingMeter = 25
): FighterRuntimeState {
  const maxHp = Math.round(getEffectiveMaxHp(fighterId, unlockedSkills) * hpMultiplier);
  const xPos = playerIndex === 1 ? -1.5 : 1.5;
  const facingRight = playerIndex === 1;

  const state: FighterRuntimeState = {
    id: fighterId,
    playerIndex,
    x: xPos,
    y: 0,
    z: 0,
    vx: 0,
    vy: 0,
    vz: 0,
    facingRight,
    facingAngle: facingRight ? Math.PI * 0.5 : -Math.PI * 0.5,
    grounded: true,
    crouching: false,
    walkCyclePhase: 0,
    hp: maxHp,
    maxHp,
    trailHp: maxHp,
    meter: startingMeter,
    maxMeter: 100,
    action: 'idle',
    actionTimerFrames: 0,
    actionTotalFrames: 1,
    currentMove: null,
    moveHasConnected: false,
    hurtbox: { x: xPos, y: 1.05, width: 1.05, height: 2.1 },
    activeHitbox: null,
    punchChainStep: 1,
    punchChainTimer: 0,
    juggleGravityScale: 1.0,
    armorHitsRemaining: 0,
    attackVisualTag: null,
    attackVisualTimer: 0,
    comboCount: 0,
    comboDamage: 0,
    comboDecayTimer: 0,
    airDribbleCount: 0,
    breakerCooldown: 0,
    stunlockCount: 0,
    stunlockImmunityTimer: 0,
    lastFrameAdvantage: 0,
    guardIntegrity: 100,
    parryWindowFrames: 0,
    bufferedMove: null,
    bufferTimerFrames: 0,
    hitFlashTimer: 0,
    unlockedSkills: [...unlockedSkills],
    aiArchetype,
    aiDecisionTimer: 0,
    aiTempo,
    paletteIndex,
    cancelFlashTimer: 0,
    wallBouncedInCombo: false,
    pendingSuperFlash: false,
    isOvercharged,
    whiffRecoveryActive: false,
    aiCooldownTimer: 0,
    lastHitHeight: 'mid',
    hardKnockdown: false,
    wakeupRollDir: 0,
    wakeupInvulnTimer: 0,
  };
  state.hurtbox = computeFighterHurtbox(state);
  return state;
}

export function createStageHazards(stageId: StageId): PropHazard[] {
  const stage = STAGES[stageId];
  const hazards: PropHazard[] = [];
  const count = stage.hazardCount;
  const kinds: PropHazard['kind'][] =
    stageId === 'zephyr_dojo'
      ? ['lantern', 'bamboo_crate', 'wind_orb', 'stone_pillar']
      : stageId === 'molten_forge'
      ? ['magma_brazier', 'stone_pillar', 'lantern', 'bamboo_crate']
      : ['bamboo_crate', 'lantern', 'wind_orb', 'stone_pillar'];

  const positions = [
    { x: -0.1, z: -0.25 },
    { x: 3.1, z: -0.35 },
    { x: -3.2, z: -0.35 },
    { x: 5.8, z: -0.4 },
    { x: -5.8, z: -0.4 },
    { x: 7.8, z: -0.3 },
    { x: -7.8, z: -0.3 },
  ];

  for (let i = 0; i < count; i++) {
    const pos = positions[i % positions.length];
    const kind = kinds[i % kinds.length];
    const maxHp = kind === 'stone_pillar' ? 110 : 65;
    hazards.push({
      id: `hazard_${i}`,
      kind,
      x: pos.x,
      z: pos.z,
      vx: 0,
      vz: 0,
      radius: kind === 'stone_pillar' ? 0.78 : 0.62,
      hp: maxHp,
      maxHp,
      destroyed: false,
      respawnTimer: 0,
      launchedByPlayer: 0,
      hitFlash: 0,
      shatterCount: 0,
    });
  }
  return hazards;
}

export function createInitialCombatSnapshot(
  p1Id: FighterId,
  p2Id: FighterId,
  stageId: StageId,
  p1Skills: string[],
  p2Skills: string[],
  mode: GameMode,
  arcadeStageIndex = 1,
  initialCountdown = 0,
  p1Palette = 0,
  p2Palette = 0
): CombatSnapshot {
  const aiTypes: FighterRuntimeState['aiArchetype'][] = ['rushdown', 'zoner', 'counter'];
  const arcadeSpec = mode === 'arcade' ? getArcadeStageSpec(p1Id, arcadeStageIndex) : null;
  const p2Ai =
    mode === 'training'
      ? 'dummy'
      : arcadeSpec
      ? arcadeSpec.aiArchetype
      : aiTypes[(arcadeStageIndex - 1) % aiTypes.length];

  const desiredP2Palette = arcadeSpec ? arcadeSpec.opponentPalette : p2Palette;
  const resolvedP2Palette = resolveMirrorPaletteIndex(
    p1Id,
    p1Palette,
    p2Id,
    desiredP2Palette
  );
  const isBossFight = arcadeSpec?.isBoss ?? false;
  const effectiveP2Skills =
    arcadeSpec && p2Skills.length === 0 ? arcadeSpec.unlockedSkills : p2Skills;

  return {
    p1: createInitialFighterState(p1Id, 1, p1Skills, 'rushdown', p1Palette),
    p2: createInitialFighterState(
      p2Id,
      2,
      effectiveP2Skills,
      p2Ai,
      resolvedP2Palette,
      arcadeSpec?.aiTempo ?? 1.0,
      isBossFight,
      isBossFight ? 1.15 : 1.0,
      isBossFight ? 50 : 25
    ),
    hazards: createStageHazards(stageId),
    roundTimer: 99,
    countdownTimer: initialCountdown,
    hitstopTimerMs: 0,
    stagePhase: isBossFight ? 3 : 1,
    spectatorExcitement: isBossFight ? 0.9 : 0.2,
    totalPropsBroken: 0,
    maxComboReached: 0,
    lastEventBanner:
      initialCountdown > 0 ? arcadeSpec?.rivalryBanner ?? 'GET READY!' : '',
    bannerTimer: initialCountdown > 0 ? initialCountdown : 0,
    winner: 0,
    arcadeStageIndex,
    inputHistoryP1: [],
    cinematicTimer: 0,
    cinematicFocusPlayer: 0,
    koSlowMoTimer: 0,
    isBossFight,
    impactFrameTimer: 0,
    impactFrameColorHex: 0xffffff,
    currentRound: 1,
    p1RoundWins: 0,
    p2RoundWins: 0,
    roundTransitionTimer: 0,
  };
}

export function canCancelInto(
  current: MoveType,
  next: MoveType,
  currentPunchStep: 1 | 2 | 3 = 1
): boolean {
  // Allow 3-Step Punch Target Combo chaining (Step 1 Jab -> Step 2 Cross -> Step 3 Finisher)
  // After Step 3 Finisher, punchChainStep resets to 1 and cannot cancel into another light punch!
  if (current === 'light' && next === 'light') {
    return currentPunchStep > 1; // Step 1 advanced to 2, Step 2 advanced to 3; Step 3 resets to 1 (false)
  }
  if (current === 'air_punch' && next === 'air_punch') {
    return false;
  }
  if (current === 'down_punch' && next === 'air_punch') {
    return true;
  }
  const order: Record<MoveType, number> = {
    light: 1,
    down_punch: 2,
    air_punch: 2,
    heavy: 3,
    elemental: 4,
    ultimate: 5,
  };
  return order[next] > order[current];
}

export function startFighterAttack(
  fighter: FighterRuntimeState,
  rawMoveType: MoveType,
  opponent: FighterRuntimeState,
  hazards: PropHazard[],
  inputHistory?: string[],
  crouchHeld = false
): boolean {
  const moveType = resolveContextualMoveType(fighter, rawMoveType, crouchHeld);
  const baseMove = getEffectiveMoveData(fighter.id, moveType, fighter.unlockedSkills);
  if (baseMove.meterCost > fighter.meter) {
    return false;
  }

  const wasDashing = fighter.action === 'dash';
  const dashCarryVx = wasDashing ? fighter.vx * 0.65 : 0;

  let move: MoveFrameData = { ...baseMove, hitbox: { ...baseMove.hitbox } };
  let visualTag: AttackVisualTag = 'JAB';

  // Apply 3-Step Punch Chain variations so pressing Punch repeatedly executes 3 distinct moves & animations!
  if (moveType === 'light') {
    const step = fighter.punchChainTimer > 0 ? fighter.punchChainStep : 1;
    if (step === 1) {
      move.animStyle = fighter.id === 'volt' ? 'tonfa_slash' : 'jab';
      move.name = `${baseMove.name.split(' ')[0]} Jab`;
      move.knockback = baseMove.knockback;
      visualTag = 'JAB';
      fighter.punchChainStep = 2;
      fighter.punchChainTimer = 0.85;
    } else if (step === 2) {
      move.animStyle = 'cross_punch';
      move.name = `${baseMove.name.split(' ')[0]} Cross`;
      move.startupFrames = baseMove.startupFrames + 1;
      move.recoveryFrames = baseMove.recoveryFrames + 2;
      move.damage = Math.round(baseMove.damage * 1.2);
      move.hitbox.width = Number((baseMove.hitbox.width * 1.12).toFixed(2));
      move.knockback = Number((baseMove.knockback * 1.35).toFixed(2));
      visualTag = 'CROSS';
      fighter.punchChainStep = 3;
      fighter.punchChainTimer = 0.9;
    } else {
      move.animStyle = 'finisher_punch';
      move.name = `${baseMove.name.split(' ')[0]} Finisher`;
      move.startupFrames = baseMove.startupFrames + 2;
      move.activeFrames = baseMove.activeFrames + 1;
      move.recoveryFrames = baseMove.recoveryFrames + 6;
      move.hitstunFrames = baseMove.hitstunFrames + 5;
      move.damage = Math.round(baseMove.damage * 1.45);
      move.hitbox.width = Number((baseMove.hitbox.width * 1.25).toFixed(2));
      // Strong Pushback on 3rd hit to prevent infinite punch spam and reset to neutral footsies!
      move.knockback = 5.4;
      move.blockPushback = 5.0;
      visualTag = 'FINISHER';
      fighter.punchChainStep = 1;
      fighter.punchChainTimer = 0;
    }
  } else {
    fighter.punchChainStep = 1;
    fighter.punchChainTimer = 0;
    if (moveType === 'down_punch') {
      visualTag = 'LOW LAUNCHER ▲';
    } else if (moveType === 'air_punch') {
      visualTag = 'AIR DRIBBLE';
    } else if (moveType === 'heavy') {
      if ((crouchHeld || fighter.crouching) && fighter.grounded) {
        // Item 3: Crouch Heavy Sweep [S + K] — Low Sweep that inflicts Hard Knockdown!
        move.name = `${FIGHTERS[fighter.id].name.split(' ')[0]} Sweep ◢`;
        move.hitHeight = 'low';
        move.animStyle = 'low_sweep';
        move.armorHits = 0;
        move.startupFrames = 8;
        move.activeFrames = 4;
        move.recoveryFrames = 18;
        move.hitstunFrames = 26;
        move.blockstunFrames = 12;
        move.damage = 95;
        move.hitbox = { offsetX: 1.45, offsetY: 0.42, width: 2.55, height: 0.72 };
        move.knockback = 3.6;
        move.blockPushback = 3.8;
        move.launchY = 2.4;
        move.airDribblePopY = undefined;
        visualTag = 'SWEEP ◢';
      } else {
        visualTag = 'OVERHEAD ▼';
      }
    } else if (moveType === 'elemental') {
      visualTag = 'ELEMENTAL';
    } else {
      visualTag = 'ULTIMATE ★';
    }
  }

  fighter.meter = Math.max(0, fighter.meter - move.meterCost);
  fighter.action = 'startup';
  fighter.actionTimerFrames = move.startupFrames;
  fighter.actionTotalFrames = move.startupFrames;
  fighter.currentMove = move;
  fighter.moveHasConnected = false;
  fighter.whiffRecoveryActive = false;
  fighter.bufferedMove = null;
  fighter.bufferTimerFrames = 0;
  fighter.crouching = moveType === 'down_punch' || move.animStyle === 'low_sweep';
  fighter.armorHitsRemaining = move.armorHits ?? 0;
  fighter.attackVisualTag = visualTag;
  fighter.attackVisualTimer = 0.65;
  if (moveType === 'ultimate') {
    fighter.pendingSuperFlash = true;
  }

  if (inputHistory) {
    inputHistory.unshift(`${visualTag} (${move.startupFrames}f)`);
    if (inputHistory.length > 7) inputHistory.pop();
  }

  const dirX = fighter.facingRight ? 1 : -1;

  if (move.spawnsHazard) {
    const destroyedHazard = hazards.find((h) => h.destroyed);
    if (destroyedHazard) {
      destroyedHazard.destroyed = false;
      destroyedHazard.hp = destroyedHazard.maxHp;
      destroyedHazard.x = fighter.x + dirX * 1.9;
      destroyedHazard.z = -0.25;
      destroyedHazard.vx = dirX * 3.5;
      destroyedHazard.vz = 0;
      destroyedHazard.launchedByPlayer = fighter.playerIndex;
    }
  }

  // Honest Physical Attack Stepping & Close-Range Contact (No long-distance teleporting!)
  const dxToOpp = opponent.x - fighter.x;
  const distToOpp = Math.abs(dxToOpp);
  const closeAssistMaxDist = move.range + 0.35;

  // If the opponent is airborne right in front of us and the grounded player triggers air_punch,
  // hop into the air to follow the juggle naturally (only while under the Air Dribble limit!)
  if (
    moveType === 'air_punch' &&
    fighter.grounded &&
    (!opponent.grounded || opponent.y > 0.25) &&
    distToOpp <= closeAssistMaxDist &&
    fighter.airDribbleCount < MAX_AIR_DRIBBLES_PER_COMBO
  ) {
    fighter.grounded = false;
    fighter.crouching = false;
    fighter.vy = Math.max(fighter.vy, opponent.vy * 0.8 + 2.2, 5.2);
  }

  // Natural forward footwork momentum per move type & fighter martial arts style
  const baseStepSpeed =
    moveType === 'heavy' || moveType === 'ultimate'
      ? 5.4
      : moveType === 'air_punch'
      ? 3.8
      : move.animStyle === 'finisher_punch'
      ? 4.6
      : move.animStyle === 'cross_punch'
      ? 3.6
      : 2.8;

  if (distToOpp <= CONTACT_STICK_DIST) {
    // Already in close contact: slight forward pressure without passing through
    fighter.vx = dirX * 1.1;
  } else if (distToOpp <= closeAssistMaxDist) {
    // Opponent is within physical reach of the attack: step in smoothly during startup
    const gap = distToOpp - CONTACT_STICK_DIST;
    fighter.vx = dirX * Math.min(8.2, Math.max(baseStepSpeed, gap * 5.2));
  } else {
    // Out of range: honest martial arts step forward (whiffs if too far!)
    fighter.vx = dirX * baseStepSpeed;
  }

  // Item 18: Dash Momentum Carry (carry 65% of dash horizontal velocity into the attack)
  if (wasDashing) {
    fighter.vx = Math.max(-13.5, Math.min(13.5, fighter.vx + dashCarryVx));
  }

  if (move.animStyle === 'uppercut' && fighter.grounded) {
    fighter.vy = 8.4;
    fighter.grounded = false;
  } else if (move.animStyle === 'spin_kick' && fighter.grounded) {
    fighter.vy = 4.5;
    fighter.grounded = false;
  } else if (
    moveType === 'air_punch' &&
    !fighter.grounded &&
    (!opponent.grounded || opponent.y > 0.25) &&
    distToOpp <= closeAssistMaxDist &&
    fighter.airDribbleCount < MAX_AIR_DRIBBLES_PER_COMBO
  ) {
    // Aerial hover boost decays with each dribble and tracks opponent vertical speed!
    const hoverVy = Math.max(0.4, 2.4 - fighter.airDribbleCount * 1.0);
    fighter.vy = Math.max(opponent.vy, Math.min(fighter.vy, hoverVy));
  }

  fighter.hurtbox = computeFighterHurtbox(fighter);
  fighter.activeHitbox = null;

  return true;
}

export function triggerComboBreaker(
  fighter: FighterRuntimeState,
  opponent: FighterRuntimeState,
  state: CombatSnapshot,
  events: StepEvents
): boolean {
  if (fighter.breakerCooldown > 0) {
    return false;
  }
  fighter.breakerCooldown = COMBO_BREAKER_COOLDOWN_SECONDS;
  fighter.action = 'breaker';
  fighter.actionTimerFrames = 14;
  fighter.actionTotalFrames = 14;
  fighter.stunlockCount = 0;
  fighter.stunlockImmunityTimer = 1.6;
  fighter.hitFlashTimer = 0.18;

  const pushDir = opponent.x >= fighter.x ? 1 : -1;
  opponent.action = 'hitstun';
  opponent.actionTimerFrames = 20;
  opponent.actionTotalFrames = 20;
  opponent.vx = pushDir * 9.5;
  opponent.vy = 4.4;
  opponent.grounded = false;
  opponent.comboCount = 0;
  opponent.comboDamage = 0;
  opponent.airDribbleCount = 0;
  opponent.currentMove = null;
  opponent.activeHitbox = null;

  state.hitstopTimerMs = 65;
  state.lastEventBanner = 'COMBO BREAKER!';
  state.bannerTimer = 1.5;
  events.breakerTriggered = true;
  events.impactSparkType = 'heavy';
  events.impactX = fighter.x;
  events.impactY = fighter.y + 1.2;
  events.impactZ = 0;
  return true;
}

export function computeAiInput(
  ai: FighterRuntimeState,
  opponent: FighterRuntimeState,
  hazards: PropHazard[],
  dt: number
): PlayerFrameInput {
  const empty: PlayerFrameInput = {
    moveX: 0,
    jumpJustPressed: false,
    crouchHeld: false,
    guardHeld: false,
    guardJustPressed: false,
    dashJustPressed: false,
    breakerJustPressed: false,
    attackJustPressed: null,
  };

  if (ai.aiArchetype === 'dummy') {
    return empty;
  }

  const tempo = ai.aiTempo || 1.0;

  if (
    (ai.action === 'hitstun' || ai.action === 'blockstun') &&
    opponent.comboCount >= 4 &&
    ai.breakerCooldown <= 0
  ) {
    return { ...empty, breakerJustPressed: true };
  }

  ai.aiDecisionTimer -= dt;
  if (ai.aiCooldownTimer > 0) {
    ai.aiCooldownTimer = Math.max(0, ai.aiCooldownTimer - dt);
  }
  const dx = opponent.x - ai.x;
  const dist = Math.abs(dx);
  const dirToOpponent = dx >= 0 ? 1 : -1;
  const backDir = -dirToOpponent;

  // Item 15: Tactical Turn Breathing — while in post-combo / whiff cooldown, hold spacing or guard!
  if (ai.aiCooldownTimer > 0 && ai.grounded) {
    const incomingLow =
      (opponent.action === 'startup' || opponent.action === 'active') &&
      opponent.currentMove?.hitHeight === 'low';
    return {
      ...empty,
      moveX: dist < 2.6 ? backDir * 0.85 : 0,
      crouchHeld: incomingLow,
      guardHeld: opponent.action === 'startup' || opponent.action === 'active',
    };
  }

  // If opponent is airborne nearby, jump or use Air Punch to dribble!
  if (!opponent.grounded && dist < 2.6 && ai.aiDecisionTimer <= 0) {
    ai.aiDecisionTimer = 0.28 * tempo;
    if (ai.grounded) {
      return { ...empty, jumpJustPressed: true };
    }
    return { ...empty, attackJustPressed: 'air_punch' };
  }

  // Street Fighter Directional Blocking & Anti-Hazard Defense by AI
  const incomingHazard = hazards.some(
    (h) =>
      !h.destroyed &&
      Math.abs(h.vx) > 3.5 &&
      Math.abs(h.x - ai.x) < 3.6 &&
      Math.sign(h.vx) === Math.sign(ai.x - h.x)
  );
  if (incomingHazard) {
    return {
      ...empty,
      moveX: backDir,
      crouchHeld: false,
    };
  }

  if (
    (opponent.action === 'startup' || opponent.action === 'active') &&
    dist < 3.5 &&
    (ai.aiArchetype === 'counter' || ai.hp < ai.maxHp * 0.45)
  ) {
    const incomingLow = opponent.currentMove?.hitHeight === 'low';
    // Counter archetype also attempts a timely Perfect Parry when the opponent starts a heavy/elemental move!
    const tryParry =
      (ai.aiArchetype === 'counter' || ai.isOvercharged) &&
      opponent.action === 'startup' &&
      opponent.actionTimerFrames <= 5 &&
      ai.parryWindowFrames <= 0;
    return {
      ...empty,
      moveX: backDir,
      crouchHeld: incomingLow,
      guardJustPressed: tryParry,
    };
  }

  // Zoner archetype maintains spacing and launches props toward the player
  if (ai.aiArchetype === 'zoner' && dist < 1.85 && ai.grounded && ai.aiDecisionTimer <= 0) {
    ai.aiDecisionTimer = 0.42 * tempo;
    return {
      ...empty,
      moveX: backDir,
      dashJustPressed: true,
    };
  }

  if (dist > 2.8) {
    const rushDash =
      (ai.aiArchetype === 'rushdown' || ai.isOvercharged) &&
      dist > 3.8 &&
      ai.grounded &&
      ai.aiDecisionTimer <= 0;
    if (rushDash) {
      ai.aiDecisionTimer = 0.55 * tempo;
    }
    return {
      ...empty,
      moveX: dirToOpponent * 0.9,
      dashJustPressed: rushDash,
      attackJustPressed:
        dist < 5.6 && ai.aiDecisionTimer <= 0 && (ai.aiArchetype === 'zoner' || ai.isOvercharged)
          ? ((ai.aiDecisionTimer = 0.72 * tempo), 'elemental')
          : null,
    };
  }

  if (ai.aiDecisionTimer <= 0) {
    ai.aiDecisionTimer = (ai.aiArchetype === 'rushdown' ? 0.34 : 0.42) * tempo;
    if (ai.meter >= 50 && opponent.hp < 360) {
      ai.aiCooldownTimer = 0.55 * tempo;
      return { ...empty, attackJustPressed: 'ultimate' };
    }
    // Punish counter when opponent is in recovery frames!
    if (opponent.action === 'recovery' && dist < 2.7) {
      ai.aiCooldownTimer = 0.45 * tempo;
      return {
        ...empty,
        crouchHeld: true,
        attackJustPressed: 'down_punch',
      };
    }
    // Mix-up against a blocking opponent: Crouching Guard -> Overhead [K], Standing Guard -> Low Launcher [S+J]!
    if (opponent.action === 'guard' || opponent.action === 'blockstun') {
      ai.aiCooldownTimer = 0.48 * tempo;
      if (opponent.crouching) {
        return { ...empty, attackJustPressed: 'heavy' };
      }
      return { ...empty, crouchHeld: true, attackJustPressed: 'down_punch' };
    }
    if (ai.action === 'active' || ai.action === 'recovery') {
      // Item 15: Never continue mashing punch chains if the previous strike whiffed in thin air!
      if (!ai.moveHasConnected) {
        ai.aiCooldownTimer = 0.45 * tempo;
        return { ...empty, moveX: backDir * 0.8 };
      }
      if (ai.currentMove?.type === 'light' && ai.punchChainStep === 2) {
        return { ...empty, attackJustPressed: 'light' };
      }
      if (ai.currentMove?.type === 'light' && ai.punchChainStep === 3) {
        ai.aiCooldownTimer = 0.52 * tempo;
        return ai.aiArchetype === 'rushdown' || ai.isOvercharged
          ? { ...empty, crouchHeld: true, attackJustPressed: 'down_punch' }
          : { ...empty, attackJustPressed: 'light' };
      }
      if (ai.currentMove?.type === 'down_punch') {
        ai.aiCooldownTimer = 0.48 * tempo;
        return { ...empty, attackJustPressed: 'heavy' };
      }
    }
    return { ...empty, attackJustPressed: 'light' };
  }

  return {
    ...empty,
    moveX: dist > 2.0 ? dirToOpponent * 0.5 : 0,
  };
}

export function stepCombatSimulation(
  state: CombatSnapshot,
  p1Input: PlayerFrameInput,
  p2Input: PlayerFrameInput,
  rawDt: number,
  mode: GameMode
): StepEvents {
  const clampedRawDt = Math.min(rawDt, 0.05);
  let dt = clampedRawDt;
  if (state.koSlowMoTimer > 0) {
    state.koSlowMoTimer = Math.max(0, state.koSlowMoTimer - clampedRawDt);
    dt = clampedRawDt * 0.22;
  }

  const events: StepEvents = {
    hitTriggered: false,
    blockTriggered: false,
    heavyHit: false,
    parryTriggered: false,
    breakerTriggered: false,
    stunlockEscapeTriggered: false,
    airDribbleTriggered: false,
    launcherTriggered: false,
    armorAbsorbed: false,
    gustTriggered: false,
    hazardShattered: false,
    stagePhaseChanged: false,
    koTriggered: false,
    whiffTriggered: false,
    clashTriggered: false,
    wallBounceTriggered: false,
    superFreezeTriggered: false,
    cancelConfirmTriggered: false,
    counterHitTriggered: false,
    punishTriggered: false,
    floorCrackTriggered: false,
    voiceTriggered: null,
    voiceFighterId: null,
    impactSparkType: null,
    attackerId: null,
    impactX: 0,
    impactY: 1.2,
    impactZ: 0,
  };

  if (state.winner !== 0) {
    // Allow K.O. knockdown physics & trailHp to settle smoothly during K.O. Slow-Motion
    if (state.koSlowMoTimer > 0) {
      state.p1.trailHp += (state.p1.hp - state.p1.trailHp) * Math.min(1, dt * 4.5);
      state.p2.trailHp += (state.p2.hp - state.p2.trailHp) * Math.min(1, dt * 4.5);
      for (const f of [state.p1, state.p2]) {
        if (!f.grounded || f.action === 'ko') {
          f.x = Math.max(-STAGE_HALF_WIDTH, Math.min(STAGE_HALF_WIDTH, f.x + f.vx * dt));
          f.y = Math.max(0, f.y + f.vy * dt);
          if (f.y > 0) {
            f.vy -= GRAVITY * dt;
          } else {
            f.vy = 0;
            f.grounded = true;
            f.vx *= Math.pow(0.05, dt);
          }
        }
      }
    }
    return events;
  }

  // Item 7: Inter-Round Transition for Best-of-3 Matches
  if (state.roundTransitionTimer > 0) {
    state.roundTransitionTimer = Math.max(0, state.roundTransitionTimer - clampedRawDt);
    state.p1.trailHp += (state.p1.hp - state.p1.trailHp) * Math.min(1, dt * 4.5);
    state.p2.trailHp += (state.p2.hp - state.p2.trailHp) * Math.min(1, dt * 4.5);
    for (const f of [state.p1, state.p2]) {
      if (!f.grounded || f.action === 'ko' || f.action === 'knockdown') {
        f.x = Math.max(-STAGE_HALF_WIDTH, Math.min(STAGE_HALF_WIDTH, f.x + f.vx * dt));
        f.y = Math.max(0, f.y + f.vy * dt);
        if (f.y > 0) {
          f.vy -= GRAVITY * dt;
        } else {
          f.vy = 0;
          f.grounded = true;
          f.vx *= Math.pow(0.05, dt);
        }
      }
    }
    if (state.roundTransitionTimer === 0) {
      state.currentRound += 1;
      state.roundTimer = 99;
      for (const f of [state.p1, state.p2]) {
        f.x = f.playerIndex === 1 ? -1.5 : 1.5;
        f.y = 0;
        f.z = 0;
        f.vx = 0;
        f.vy = 0;
        f.vz = 0;
        f.grounded = true;
        f.crouching = false;
        f.facingRight = f.playerIndex === 1;
        f.facingAngle = f.facingRight ? Math.PI * 0.5 : -Math.PI * 0.5;
        f.hp = f.maxHp;
        f.trailHp = f.maxHp;
        f.meter = Math.max(25, Math.round(f.meter * 0.5));
        f.action = 'idle';
        f.actionTimerFrames = 0;
        f.actionTotalFrames = 1;
        f.currentMove = null;
        f.activeHitbox = null;
        f.moveHasConnected = false;
        f.comboCount = 0;
        f.comboDamage = 0;
        f.comboDecayTimer = 0;
        f.airDribbleCount = 0;
        f.stunlockCount = 0;
        f.stunlockImmunityTimer = 0;
        f.wakeupInvulnTimer = 0;
        f.hardKnockdown = false;
        f.wakeupRollDir = 0;
        f.wallBouncedInCombo = false;
        f.whiffRecoveryActive = false;
        f.hurtbox = computeFighterHurtbox(f);
      }
      state.countdownTimer = 1.4;
      state.lastEventBanner =
        state.currentRound >= 3
          ? 'FINAL ROUND — GET READY!'
          : `ROUND ${state.currentRound} — GET READY!`;
      state.bannerTimer = 1.4;
    }
    return events;
  }

  if (state.countdownTimer > 0) {
    state.countdownTimer = Math.max(0, state.countdownTimer - clampedRawDt);
    if (state.countdownTimer === 0) {
      state.lastEventBanner = 'FIGHT!';
      state.bannerTimer = 1.0;
    }
    state.p1.hurtbox = computeFighterHurtbox(state.p1);
    state.p2.hurtbox = computeFighterHurtbox(state.p2);
    return events;
  }

  // Item 1: Cinematic Super Flash Freeze on Ultimate Activation
  if (state.cinematicTimer > 0) {
    for (const [f, inp] of [
      [state.p1, p1Input],
      [state.p2, p2Input],
    ] as const) {
      if (inp.attackJustPressed) {
        f.bufferedMove = resolveContextualMoveType(
          f,
          inp.attackJustPressed,
          inp.crouchHeld
        );
        f.bufferTimerFrames = 10;
      }
    }
    state.cinematicTimer = Math.max(0, state.cinematicTimer - clampedRawDt);
    if (state.cinematicTimer === 0) {
      state.cinematicFocusPlayer = 0;
    }
    return events;
  }

  if (state.hitstopTimerMs > 0) {
    // Buffer attack inputs pressed during hitstop so 3-step punch chains and cancels never drop!
    for (const [f, inp] of [
      [state.p1, p1Input],
      [state.p2, p2Input],
    ] as const) {
      if (inp.attackJustPressed) {
        f.bufferedMove = resolveContextualMoveType(
          f,
          inp.attackJustPressed,
          inp.crouchHeld
        );
        f.bufferTimerFrames = 10;
      }
    }
    state.hitstopTimerMs = Math.max(0, state.hitstopTimerMs - dt * 1000);
    return events;
  }

  if (state.bannerTimer > 0) {
    state.bannerTimer = Math.max(0, state.bannerTimer - dt);
  }
  if (state.impactFrameTimer > 0) {
    state.impactFrameTimer = Math.max(0, state.impactFrameTimer - clampedRawDt);
  }

  if (mode === 'training') {
    if (state.p2.action === 'idle' && state.p1.comboCount === 0) {
      state.p2.hp = Math.min(state.p2.maxHp, state.p2.hp + 240 * dt);
    }
    state.p1.hp = Math.min(state.p1.maxHp, state.p1.hp + 120 * dt);
    state.p1.meter = Math.min(state.p1.maxMeter, state.p1.meter + 18 * dt);
  } else {
    state.roundTimer = Math.max(0, state.roundTimer - dt);
  }

  // Item 1: Delayed Red Damage Bar — freeze trailHp while fighter is in hitstun/juggled so player sees full combo damage!
  for (const f of [state.p1, state.p2]) {
    if (f.hp >= f.trailHp) {
      f.trailHp = f.hp;
    } else if (f.action !== 'hitstun' && (f.grounded || f.action === 'idle' || f.action === 'jump')) {
      f.trailHp = Math.max(f.hp, f.trailHp - 220 * dt);
    }
  }

  const frameAdvance = dt * 60;

  // Item 6: Pre-check Simultaneous Elemental Clash before individual hurtbox resolution
  // Check if both fighters are currently active (or transitioning to active on this exact frame)
  const p1BecomingActive =
    state.p1.action === 'startup' &&
    state.p1.currentMove !== null &&
    state.p1.actionTimerFrames - frameAdvance <= 0;
  const p2BecomingActive =
    state.p2.action === 'startup' &&
    state.p2.currentMove !== null &&
    state.p2.actionTimerFrames - frameAdvance <= 0;

  if (
    (state.p1.action === 'active' || p1BecomingActive) &&
    (state.p2.action === 'active' || p2BecomingActive) &&
    !state.p1.moveHasConnected &&
    !state.p2.moveHasConnected &&
    state.p1.currentMove &&
    state.p2.currentMove
  ) {
    if (p1BecomingActive) {
      state.p1.action = 'active';
      state.p1.actionTimerFrames = state.p1.currentMove.activeFrames;
      state.p1.actionTotalFrames = state.p1.currentMove.activeFrames;
    }
    if (p2BecomingActive) {
      state.p2.action = 'active';
      state.p2.actionTimerFrames = state.p2.currentMove.activeFrames;
      state.p2.actionTotalFrames = state.p2.currentMove.activeFrames;
    }
    const hb1 = computeFighterActiveHitbox(state.p1);
    const hb2 = computeFighterActiveHitbox(state.p2);
    state.p1.activeHitbox = hb1;
    state.p2.activeHitbox = hb2;

    if (hb1 && hb2 && boxesOverlap2D(hb1, hb2)) {
      state.p1.moveHasConnected = true;
      state.p2.moveHasConnected = true;
      state.p1.meter = Math.min(state.p1.maxMeter, state.p1.meter + 25);
      state.p2.meter = Math.min(state.p2.maxMeter, state.p2.meter + 25);
      const p1Dir = state.p1.facingRight ? 1 : -1;
      state.p1.vx = -p1Dir * 5.2;
      state.p2.vx = p1Dir * 5.2;
      state.p1.cancelFlashTimer = 0.25;
      state.p2.cancelFlashTimer = 0.25;
      state.p1.hitFlashTimer = 0.12;
      state.p2.hitFlashTimer = 0.12;
      state.p1.attackVisualTag = 'CLASH ⚡';
      state.p2.attackVisualTag = 'CLASH ⚡';
      state.p1.attackVisualTimer = 0.75;
      state.p2.attackVisualTimer = 0.75;
      state.hitstopTimerMs = 90;
      state.impactFrameTimer = 0.055;
      state.impactFrameColorHex = 0xfacc15;
      state.lastEventBanner = 'ELEMENTAL CLASH! (+25 METER)';
      state.bannerTimer = 1.4;
      events.clashTriggered = true;
      events.impactSparkType = 'clash';
      events.impactX = (hb1.x + hb2.x) * 0.5;
      events.impactY = (hb1.y + hb2.y) * 0.5;
      events.impactZ = 0;
    }
  }

  const fighters: [FighterRuntimeState, FighterRuntimeState, PlayerFrameInput][] = [
    [state.p1, state.p2, p1Input],
    [state.p2, state.p1, p2Input],
  ];

  for (const [fighter, opponent, input] of fighters) {
    if (fighter.breakerCooldown > 0) {
      fighter.breakerCooldown = Math.max(0, fighter.breakerCooldown - dt);
    }
    if (fighter.stunlockImmunityTimer > 0) {
      fighter.stunlockImmunityTimer = Math.max(0, fighter.stunlockImmunityTimer - dt);
    }
    if (fighter.wakeupInvulnTimer > 0) {
      fighter.wakeupInvulnTimer = Math.max(0, fighter.wakeupInvulnTimer - dt);
    }
    if (fighter.cancelFlashTimer > 0) {
      fighter.cancelFlashTimer = Math.max(0, fighter.cancelFlashTimer - dt);
    }
    if (fighter.punchChainTimer > 0) {
      fighter.punchChainTimer = Math.max(0, fighter.punchChainTimer - dt);
      if (fighter.punchChainTimer === 0) {
        fighter.punchChainStep = 1;
      }
    }
    if (fighter.attackVisualTimer > 0) {
      fighter.attackVisualTimer = Math.max(0, fighter.attackVisualTimer - dt);
      if (fighter.attackVisualTimer === 0) {
        fighter.attackVisualTag = null;
      }
    }

    if (
      fighter.grounded &&
      (fighter.action === 'idle' ||
        fighter.action === 'walk' ||
        fighter.action === 'crouch' ||
        fighter.action === 'guard')
    ) {
      fighter.facingRight = opponent.x >= fighter.x;
    }
    fighter.facingAngle = fighter.facingRight ? Math.PI * 0.5 : -Math.PI * 0.5;

    if (fighter.hitFlashTimer > 0) {
      fighter.hitFlashTimer = Math.max(0, fighter.hitFlashTimer - dt);
    }

    if (fighter.comboDecayTimer > 0) {
      fighter.comboDecayTimer -= dt;
      if (fighter.comboDecayTimer <= 0) {
        fighter.comboCount = 0;
        fighter.comboDamage = 0;
        if (opponent.grounded) {
          fighter.airDribbleCount = 0;
        }
      }
    }

    // Combo Breaker check while in hitstun or blockstun
    const wantsBreaker =
      input.breakerJustPressed ||
      (input.guardHeld && input.attackJustPressed !== null);
    if (
      (fighter.action === 'hitstun' || fighter.action === 'blockstun') &&
      wantsBreaker &&
      fighter.breakerCooldown <= 0
    ) {
      triggerComboBreaker(fighter, opponent, state, events);
      continue;
    }

    // Input buffer handling (10-frame buffer)
    if (input.attackJustPressed) {
      fighter.bufferedMove = resolveContextualMoveType(
        fighter,
        input.attackJustPressed,
        input.crouchHeld
      );
      fighter.bufferTimerFrames = 10;
    } else if (fighter.bufferTimerFrames > 0) {
      fighter.bufferTimerFrames = Math.max(0, fighter.bufferTimerFrames - frameAdvance);
      if (fighter.bufferTimerFrames === 0) {
        fighter.bufferedMove = null;
      }
    }

    // Item 18: Allow immediate Dash-Cancel into Attack or Jump with 65% Dash Momentum Carry
    if (fighter.action === 'dash') {
      if (fighter.bufferedMove) {
        startFighterAttack(
          fighter,
          fighter.bufferedMove,
          opponent,
          state.hazards,
          fighter.playerIndex === 1 ? state.inputHistoryP1 : undefined,
          input.crouchHeld
        );
      } else if (input.jumpJustPressed && fighter.grounded) {
        const def = FIGHTERS[fighter.id];
        const dashCarry = fighter.vx * 0.65;
        fighter.grounded = false;
        fighter.crouching = false;
        fighter.vy = def.jumpVelocity;
        fighter.vx = dashCarry + input.moveX * def.walkSpeed * 0.55;
        fighter.action = 'jump';
        fighter.actionTimerFrames = 0;
      }
    }

    // State machine transitions
    if (
      fighter.action === 'hitstun' ||
      fighter.action === 'blockstun' ||
      fighter.action === 'knockdown' ||
      fighter.action === 'dash' ||
      fighter.action === 'breaker'
    ) {
      fighter.activeHitbox = null;
      fighter.armorHitsRemaining = 0;

      // Item 1: Wake-up Tech Roll during grounded Soft Knockdown when holding Left/Right
      if (
        fighter.action === 'knockdown' &&
        fighter.grounded &&
        !fighter.hardKnockdown &&
        fighter.wakeupRollDir === 0 &&
        fighter.actionTimerFrames <= 14 &&
        Math.abs(input.moveX) > 0.25
      ) {
        const rollDir = Math.sign(input.moveX) as -1 | 1;
        fighter.wakeupRollDir = rollDir;
        fighter.vx = rollDir * 10.5;
        fighter.wakeupInvulnTimer = Math.max(fighter.wakeupInvulnTimer, 0.32);
        fighter.attackVisualTag = 'TECH ROLL';
        fighter.attackVisualTimer = 0.65;
      }

      if (fighter.action === 'knockdown' && fighter.grounded && fighter.wakeupRollDir !== 0) {
        fighter.vx = fighter.wakeupRollDir * 9.5;
      }

      fighter.actionTimerFrames -= frameAdvance;
      if (fighter.actionTimerFrames <= 0) {
        if (fighter.action === 'hitstun' || fighter.action === 'blockstun') {
          if (fighter.grounded) {
            fighter.stunlockCount = 0;
          }
          fighter.wallBouncedInCombo = false;
        }
        if (fighter.action === 'knockdown') {
          fighter.hardKnockdown = false;
          fighter.wakeupRollDir = 0;
          fighter.stunlockCount = 0;
          fighter.wallBouncedInCombo = false;
          fighter.wakeupInvulnTimer = Math.max(fighter.wakeupInvulnTimer, 0.14);
        }
        fighter.action = fighter.grounded ? 'idle' : 'jump';
        fighter.actionTimerFrames = 0;
      }
    } else if (fighter.action === 'startup') {
      fighter.activeHitbox = null;
      // Only assist close-range alignment when already within physical reach (no long-range pulling!)
      const dirX = fighter.facingRight ? 1 : -1;
      const dist = Math.abs(opponent.x - fighter.x);
      const closeReach = (fighter.currentMove?.range ?? 2.5) + 0.15;
      if (dist > CONTACT_STICK_DIST && dist <= closeReach) {
        const targetX = opponent.x - dirX * CONTACT_STICK_DIST;
        fighter.x += (targetX - fighter.x) * Math.min(1, dt * 6.5);
      }
      if (
        fighter.currentMove?.type === 'air_punch' &&
        !opponent.grounded &&
        fighter.airDribbleCount < MAX_AIR_DRIBBLES_PER_COMBO &&
        dist <= closeReach &&
        Math.abs(opponent.y - fighter.y) < 1.65
      ) {
        fighter.y += (opponent.y - fighter.y) * Math.min(1, dt * 8.0);
      }

      fighter.actionTimerFrames -= frameAdvance;
      if (fighter.actionTimerFrames <= 0 && fighter.currentMove) {
        fighter.action = 'active';
        fighter.actionTimerFrames = fighter.currentMove.activeFrames;
        fighter.actionTotalFrames = fighter.currentMove.activeFrames;
        fighter.activeHitbox = computeFighterActiveHitbox(fighter);
        events.whiffTriggered = true;
        events.attackerId = fighter.id;
        if (!events.voiceTriggered) {
          events.voiceFighterId = fighter.id;
          events.voiceTriggered =
            fighter.currentMove.type === 'ultimate'
              ? 'ultimate'
              : fighter.currentMove.type === 'heavy' ||
                fighter.currentMove.type === 'elemental' ||
                fighter.currentMove.animStyle === 'finisher_punch'
              ? 'heavy'
              : 'light';
        }

        if (
          fighter.currentMove.type === 'elemental' ||
          fighter.currentMove.type === 'ultimate' ||
          fighter.currentMove.gustForce >= 7.5
        ) {
          if (
            fighter.currentMove.type === 'elemental' ||
            fighter.currentMove.type === 'ultimate'
          ) {
            events.gustTriggered = true;
            events.impactX = fighter.x + (fighter.facingRight ? 1.05 : -1.05);
            events.impactY = fighter.y + 1.2;
            events.impactZ = 0;
          }
          const gust = fighter.currentMove.gustForce;
          for (const hazard of state.hazards) {
            if (hazard.destroyed) continue;
            const hDist = Math.abs(hazard.x - fighter.x);
            if (hDist <= fighter.currentMove.range + 2.4) {
              const launchDir = opponent.x >= hazard.x ? 1 : -1;
              hazard.vx = launchDir * gust;
              hazard.vz = 0;
              hazard.launchedByPlayer = fighter.playerIndex;
              events.gustTriggered = true;
            }
          }
        }
      }
    } else if (fighter.action === 'active') {
      fighter.activeHitbox = computeFighterActiveHitbox(fighter);
      opponent.hurtbox = computeFighterHurtbox(opponent);

      const opponentInput = fighter.playerIndex === 1 ? p2Input : p1Input;

      if (
        fighter.currentMove &&
        !fighter.moveHasConnected &&
        fighter.activeHitbox &&
        boxesOverlap2D(fighter.activeHitbox, opponent.hurtbox)
      ) {
        fighter.moveHasConnected = true;
        resolveStrikeHit(
          fighter,
          opponent,
          opponentInput,
          fighter.currentMove,
          state,
          events
        );
      }

      if (
        fighter.moveHasConnected &&
        fighter.bufferedMove &&
        fighter.currentMove &&
        canCancelInto(
          fighter.currentMove.type,
          fighter.bufferedMove,
          fighter.punchChainStep
        )
      ) {
        if (
          startFighterAttack(
            fighter,
            fighter.bufferedMove,
            opponent,
            state.hazards,
            fighter.playerIndex === 1 ? state.inputHistoryP1 : undefined,
            input.crouchHeld
          )
        ) {
          events.cancelConfirmTriggered = true;
          fighter.cancelFlashTimer = 0.14;
          continue;
        }
      }

      fighter.actionTimerFrames -= frameAdvance;
      if (fighter.actionTimerFrames <= 0 && fighter.currentMove) {
        fighter.action = 'recovery';
        // Item 11: Whiff Punish Cadence — missing an attack in thin air adds noticeable Whiff Lag!
        const whiffPenalty = !fighter.moveHasConnected
          ? fighter.currentMove.type === 'light' || fighter.currentMove.type === 'air_punch'
            ? 5
            : 8
          : 0;
        fighter.whiffRecoveryActive = whiffPenalty > 0;
        const totalRec = fighter.currentMove.recoveryFrames + whiffPenalty;
        fighter.actionTimerFrames = totalRec;
        fighter.actionTotalFrames = totalRec;
        fighter.activeHitbox = null;
        fighter.armorHitsRemaining = 0;
      }
    } else if (fighter.action === 'recovery') {
      fighter.activeHitbox = null;
      fighter.armorHitsRemaining = 0;
      if (
        fighter.moveHasConnected &&
        fighter.bufferedMove &&
        fighter.currentMove &&
        canCancelInto(
          fighter.currentMove.type,
          fighter.bufferedMove,
          fighter.punchChainStep
        )
      ) {
        if (
          startFighterAttack(
            fighter,
            fighter.bufferedMove,
            opponent,
            state.hazards,
            fighter.playerIndex === 1 ? state.inputHistoryP1 : undefined,
            input.crouchHeld
          )
        ) {
          events.cancelConfirmTriggered = true;
          fighter.cancelFlashTimer = 0.14;
          continue;
        }
      }

      fighter.actionTimerFrames -= frameAdvance;
      if (fighter.actionTimerFrames <= 0) {
        fighter.action = fighter.grounded ? 'idle' : 'jump';
        fighter.currentMove = null;
        fighter.whiffRecoveryActive = false;
      }
    }

    // Neutral, Street Fighter Directional Guard (Back / Down-Back) & Aerial states
    if (
      fighter.action === 'idle' ||
      fighter.action === 'walk' ||
      fighter.action === 'crouch' ||
      fighter.action === 'jump' ||
      fighter.action === 'guard' ||
      fighter.action === 'parry'
    ) {
      fighter.activeHitbox = null;
      fighter.wallBouncedInCombo = false;
      if (fighter.parryWindowFrames > 0) {
        fighter.parryWindowFrames = Math.max(0, fighter.parryWindowFrames - frameAdvance);
      }

      const holdingBack = isHoldingBackDirection(fighter, input.moveX);
      const threatActive = isOpponentThreatening(fighter, opponent, state.hazards);
      // Street Fighter Directional Blocking:
      // - Holding Down + Back (crouchHeld && holdingBack) always enters Crouching Guard!
      // - Holding Back (holdingBack) enters Standing Guard when threatened by an attack, or walks back in neutral!
      const directionalGuardActive =
        fighter.grounded &&
        holdingBack &&
        (input.crouchHeld || threatActive);

      if (input.guardJustPressed && fighter.grounded) {
        fighter.action = 'parry';
        fighter.parryWindowFrames = 6;
      } else if (fighter.bufferedMove) {
        startFighterAttack(
          fighter,
          fighter.bufferedMove,
          opponent,
          state.hazards,
          fighter.playerIndex === 1 ? state.inputHistoryP1 : undefined,
          input.crouchHeld
        );
      } else if ((input.guardHeld || directionalGuardActive) && fighter.grounded) {
        fighter.action = fighter.parryWindowFrames > 0 ? 'parry' : 'guard';
        fighter.vx *= 0.6;
        fighter.crouching = input.crouchHeld;
      } else if (input.dashJustPressed && fighter.grounded) {
        const def = FIGHTERS[fighter.id];
        fighter.action = 'dash';
        fighter.actionTimerFrames = 10;
        fighter.actionTotalFrames = 10;
        const dashDir =
          Math.abs(input.moveX) > 0.05
            ? Math.sign(input.moveX)
            : fighter.facingRight
            ? 1
            : -1;
        fighter.vx = dashDir * def.dashSpeed;
      } else if (input.jumpJustPressed && fighter.grounded) {
        const def = FIGHTERS[fighter.id];
        fighter.grounded = false;
        fighter.crouching = false;
        fighter.vy = def.jumpVelocity;
        fighter.vx = input.moveX * def.walkSpeed * 0.95;
        fighter.action = 'jump';
      } else if (!fighter.grounded) {
        const def = FIGHTERS[fighter.id];
        fighter.action = 'jump';
        if (Math.abs(input.moveX) > 0.05) {
          fighter.vx += input.moveX * def.walkSpeed * 2.5 * dt;
          fighter.vx = Math.max(-def.walkSpeed, Math.min(def.walkSpeed, fighter.vx));
        }
      } else if (input.crouchHeld) {
        fighter.crouching = true;
        fighter.action = 'crouch';
        fighter.vx *= 0.6;
      } else {
        fighter.crouching = false;
        const def = FIGHTERS[fighter.id];
        fighter.vx = input.moveX * def.walkSpeed;
        if (Math.abs(input.moveX) > 0.05) {
          fighter.action = 'walk';
          const walkSign =
            Math.sign(input.moveX) === (fighter.facingRight ? 1 : -1) ? 1 : -1;
          fighter.walkCyclePhase += dt * Math.abs(fighter.vx) * 2.2 * walkSign;
        } else {
          fighter.action = 'idle';
        }
      }
    }

    // Item 1: Trigger Cinematic Super Flash if this fighter just initiated an Ultimate move
    if (fighter.pendingSuperFlash) {
      fighter.pendingSuperFlash = false;
      state.cinematicTimer = 0.35;
      state.cinematicFocusPlayer = fighter.playerIndex;
      state.lastEventBanner = `${fighter.currentMove?.name.toUpperCase() ?? 'ULTIMATE ART'}!`;
      state.bannerTimer = 1.6;
      events.superFreezeTriggered = true;
      events.voiceFighterId = fighter.id;
      events.voiceTriggered = 'ultimate';
      events.attackerId = fighter.id;
      events.impactX = fighter.x;
      events.impactY = fighter.y + 1.35;
      events.impactZ = 0;
    }

    // Integrate 2D X and Y physics with progressive Juggle Gravity
    fighter.x += fighter.vx * dt;
    fighter.z = 0;
    if (fighter.grounded) {
      fighter.vx *= Math.pow(0.05, dt);
      fighter.juggleGravityScale = 1.0;
    } else {
      if (fighter.action === 'startup' || fighter.action === 'active') {
        fighter.vx *= Math.pow(0.08, dt);
      }
      fighter.y += fighter.vy * dt;
      const effectiveGravity = GRAVITY * fighter.juggleGravityScale;
      fighter.vy -= effectiveGravity * dt;
      if (fighter.y <= 0) {
        const hardLanding = fighter.vy < -10.5 || fighter.action === 'hitstun' || fighter.action === 'knockdown';
        fighter.y = 0;
        fighter.vy = 0;
        fighter.grounded = true;
        fighter.juggleGravityScale = 1.0;
        opponent.airDribbleCount = 0;
        if (fighter.action !== 'hitstun' && fighter.action !== 'blockstun') {
          fighter.stunlockCount = 0;
        }
        if (hardLanding) {
          events.floorCrackTriggered = true;
          events.impactX = fighter.x;
          events.impactZ = 0;
        }
        if (fighter.action === 'knockdown') {
          const matFrames = fighter.hardKnockdown ? 34 : 26;
          fighter.actionTimerFrames = matFrames;
          fighter.actionTotalFrames = matFrames;
          fighter.wakeupRollDir = 0;
          fighter.wakeupInvulnTimer = Math.max(
            fighter.wakeupInvulnTimer,
            matFrames / 60 + 0.14
          );
        } else if (fighter.action === 'jump') {
          fighter.action = 'idle';
        }
      }
    }

    // Item 6: Corner Wall Bounce (once per combo when slammed into the arena wall in hitstun)
    if (
      Math.abs(fighter.x) >= STAGE_HALF_WIDTH - 0.15 &&
      fighter.action === 'hitstun' &&
      Math.abs(fighter.vx) >= 4.2 &&
      !fighter.wallBouncedInCombo &&
      Math.sign(fighter.vx) === Math.sign(fighter.x)
    ) {
      const wallSign = Math.sign(fighter.x) || 1;
      fighter.x = wallSign * (STAGE_HALF_WIDTH - 0.16);
      fighter.wallBouncedInCombo = true;
      fighter.vx = -wallSign * 4.6;
      fighter.vy = Math.max(fighter.vy, 6.2);
      fighter.grounded = false;
      fighter.actionTimerFrames = Math.max(fighter.actionTimerFrames, 24);
      fighter.actionTotalFrames = Math.max(fighter.actionTotalFrames, 24);
      fighter.hitFlashTimer = 0.16;
      fighter.attackVisualTag = 'WALL BOUNCE!';
      fighter.attackVisualTimer = 0.85;
      state.hitstopTimerMs = Math.max(state.hitstopTimerMs, 65);
      state.impactFrameTimer = 0.055;
      state.impactFrameColorHex = 0xf97316;
      state.lastEventBanner = 'WALL BOUNCE!';
      state.bannerTimer = 1.35;
      events.wallBounceTriggered = true;
      events.floorCrackTriggered = true;
      events.impactSparkType = 'wall';
      events.impactX = wallSign * STAGE_HALF_WIDTH;
      events.impactY = fighter.y + 1.1;
      events.impactZ = 0;
    } else if (fighter.x < -STAGE_HALF_WIDTH) {
      fighter.x = -STAGE_HALF_WIDTH;
    } else if (fighter.x > STAGE_HALF_WIDTH) {
      fighter.x = STAGE_HALF_WIDTH;
    }

    fighter.hurtbox = computeFighterHurtbox(fighter);
  }

  // Prevent fighters from overlapping horizontally when grounded or during close attacks
  const sepX = state.p2.x - state.p1.x;
  const absSep = Math.abs(sepX);
  const minSep = CONTACT_STICK_DIST;
  if (absSep < minSep && Math.abs(state.p1.y - state.p2.y) < 1.35) {
    const push = (minSep - absSep) * 0.5;
    const sign = sepX >= 0 ? 1 : -1;
    state.p1.x -= sign * push;
    state.p2.x += sign * push;
    state.p1.hurtbox = computeFighterHurtbox(state.p1);
    state.p2.hurtbox = computeFighterHurtbox(state.p2);
  }

  // Step destructible stage hazards along the 2D plane
  for (const hazard of state.hazards) {
    if (hazard.hitFlash > 0) {
      hazard.hitFlash = Math.max(0, hazard.hitFlash - dt);
    }

    if (hazard.destroyed) {
      hazard.respawnTimer -= dt;
      if (hazard.respawnTimer <= 0) {
        hazard.destroyed = false;
        hazard.hp = hazard.maxHp;
        hazard.vx = 0;
        hazard.vz = 0;
        hazard.launchedByPlayer = 0;
      }
      continue;
    }

    hazard.x += hazard.vx * dt;
    hazard.vx *= Math.pow(0.18, dt);
    const speed = Math.abs(hazard.vx);

    for (const target of [state.p1, state.p2]) {
      const dx = Math.abs(target.x - hazard.x);
      if (dx < hazard.radius + 0.75 && target.y < 1.3) {
        if (speed > 4.0 && hazard.launchedByPlayer !== target.playerIndex) {
          const targetInput = target.playerIndex === 1 ? p1Input : p2Input;
          const isHoldingBack = isHoldingBackDirection(target, targetInput.moveX);
          const isBlockingHazard =
            target.action === 'guard' ||
            target.action === 'blockstun' ||
            (target.grounded && (targetInput.guardHeld || isHoldingBack));

          if (isBlockingHazard) {
            target.hp = Math.max(1, target.hp - 10);
            target.action = 'blockstun';
            target.actionTimerFrames = 12;
            target.actionTotalFrames = 12;
            target.attackVisualTag = target.crouching ? 'LOW BLOCK' : 'STAND BLOCK';
            target.attackVisualTimer = 0.55;
            events.blockTriggered = true;
            events.impactSparkType = 'block';
            shatterHazard(hazard, state, events);
            break;
          }

          const dmg = 65;
          target.hp = Math.max(0, target.hp - dmg);
          target.action = 'hitstun';
          target.actionTimerFrames = 22;
          target.actionTotalFrames = 22;
          target.hitFlashTimer = 0.14;
          target.vy = 3.5;
          target.grounded = false;

          const attacker = target.playerIndex === 1 ? state.p2 : state.p1;
          attacker.comboCount += 1;
          attacker.comboDamage += dmg;
          attacker.comboDecayTimer = 2.4;
          state.maxComboReached = Math.max(state.maxComboReached, attacker.comboCount);
          state.hitstopTimerMs = 68;
          state.lastEventBanner = 'HAZARD SMASH!';
          state.bannerTimer = 1.4;
          events.impactSparkType = 'heavy';

          shatterHazard(hazard, state, events);
          break;
        } else if (
          (target.action === 'active' || target.action === 'dash') &&
          dx < hazard.radius + 0.85
        ) {
          hazard.hp -= 70;
          hazard.hitFlash = 0.12;
          if (hazard.hp <= 0) {
            shatterHazard(hazard, state, events);
          }
        }
      }
    }

    if (Math.abs(hazard.x) > STAGE_HALF_WIDTH) {
      if (speed > 7.5) {
        shatterHazard(hazard, state, events);
      } else {
        hazard.x = Math.sign(hazard.x) * STAGE_HALF_WIDTH;
        hazard.vx *= -0.5;
      }
    }
  }

  // Dynamic Stage Phase evolution
  const lowestHpRatio = Math.min(
    state.p1.hp / state.p1.maxHp,
    state.p2.hp / state.p2.maxHp
  );
  const targetPhase: 1 | 2 | 3 =
    lowestHpRatio < 0.35 || state.totalPropsBroken >= 4
      ? 3
      : lowestHpRatio < 0.7 || state.totalPropsBroken >= 2
      ? 2
      : 1;

  if (targetPhase > state.stagePhase) {
    state.stagePhase = targetPhase;
    events.stagePhaseChanged = true;
    state.lastEventBanner =
      targetPhase === 3 ? 'STAGE CLIMAX UNLEASHED!' : 'CROWD HEATING UP!';
    state.bannerTimer = 1.8;
  }

  state.spectatorExcitement = Math.min(
    1,
    0.2 +
      (state.stagePhase - 1) * 0.25 +
      Math.min(0.35, (state.p1.comboCount + state.p2.comboCount) * 0.06)
  );

  if (mode === 'training') {
    state.p1.hp = Math.max(1, state.p1.hp);
    state.p2.hp = Math.max(1, state.p2.hp);
  } else {
    let roundWinner: 0 | 1 | 2 = 0;
    let isTimeOver = false;
    if (state.p2.hp <= 0) {
      state.p2.hp = 0;
      state.p2.action = 'ko';
      state.p2.vy = Math.max(state.p2.vy, 5.2);
      state.p2.grounded = false;
      roundWinner = 1;
      events.voiceFighterId = state.p2.id;
      events.voiceTriggered = 'ko';
    } else if (state.p1.hp <= 0) {
      state.p1.hp = 0;
      state.p1.action = 'ko';
      state.p1.vy = Math.max(state.p1.vy, 5.2);
      state.p1.grounded = false;
      roundWinner = 2;
      events.voiceFighterId = state.p1.id;
      events.voiceTriggered = 'ko';
    } else if (state.roundTimer <= 0) {
      roundWinner =
        state.p1.hp / state.p1.maxHp >= state.p2.hp / state.p2.maxHp ? 1 : 2;
      isTimeOver = true;
    }

    if (roundWinner !== 0) {
      if (roundWinner === 1) {
        state.p1RoundWins += 1;
      } else {
        state.p2RoundWins += 1;
      }
      state.hitstopTimerMs = 85;
      const matchDecided = state.p1RoundWins >= 2 || state.p2RoundWins >= 2;
      if (matchDecided) {
        state.winner = roundWinner;
        state.koSlowMoTimer = isTimeOver ? 0.45 : 0.65;
        events.koTriggered = true;
        state.lastEventBanner = isTimeOver
          ? 'TIME OVER!'
          : roundWinner === 1
          ? 'K.O. — VICTORY!'
          : 'K.O. — DEFEAT!';
        state.bannerTimer = 3.0;
      } else {
        state.roundTransitionTimer = 1.65;
        state.koSlowMoTimer = 0.48;
        const winFighter = roundWinner === 1 ? state.p1 : state.p2;
        const winName = FIGHTERS[winFighter.id].name.split(' ')[0].toUpperCase();
        state.lastEventBanner = `ROUND ${state.currentRound} — ${winName} WINS!`;
        state.bannerTimer = 1.65;
      }
    }
  }

  return events;
}

function shatterHazard(
  hazard: PropHazard,
  state: CombatSnapshot,
  events: StepEvents
) {
  hazard.destroyed = true;
  hazard.respawnTimer = 8.5;
  hazard.shatterCount += 1;
  state.totalPropsBroken += 1;
  events.hazardShattered = true;
  events.impactX = hazard.x;
  events.impactY = 0.8;
  events.impactZ = hazard.z;
}

function resolveStrikeHit(
  attacker: FighterRuntimeState,
  defender: FighterRuntimeState,
  defenderInput: PlayerFrameInput,
  move: FighterRuntimeState['currentMove'],
  state: CombatSnapshot,
  events: StepEvents
) {
  if (!move) return;

  // Item 1 & 10: Wake-up & Grounded Knockdown Invulnerability
  if (
    (defender.action === 'knockdown' && defender.grounded) ||
    defender.wakeupInvulnTimer > 0
  ) {
    return;
  }

  const dirX = attacker.facingRight ? 1 : -1;
  events.attackerId = attacker.id;
  events.impactX = (attacker.x + defender.x) * 0.5;
  events.impactY = defender.y + 1.25;
  events.impactZ = 0;

  if (defender.action === 'parry' && defender.parryWindowFrames > 0) {
    events.parryTriggered = true;
    events.impactSparkType = 'parry';
    state.hitstopTimerMs = 75;
    defender.meter = Math.min(defender.maxMeter, defender.meter + 22);
    attacker.action = 'recovery';
    attacker.actionTimerFrames = move.recoveryFrames + 8;
    attacker.actionTotalFrames = move.recoveryFrames + 8;
    defender.lastFrameAdvantage = 10;
    attacker.lastFrameAdvantage = -10;
    state.lastEventBanner = 'PERFECT PARRY! (+10F)';
    state.bannerTimer = 1.2;
    return;
  }

  // Street Fighter Directional Blocking Check:
  // Defender blocks if in 'guard'/'blockstun' OR if grounded in neutral/walk/crouch while holding Back / Down-Back!
  const isNeutralGrounded =
    defender.grounded &&
    (defender.action === 'idle' ||
      defender.action === 'walk' ||
      defender.action === 'crouch' ||
      defender.action === 'guard' ||
      defender.action === 'blockstun');
  const holdingBack = isHoldingBackDirection(defender, defenderInput.moveX);
  const attemptingGuard =
    defender.action === 'guard' ||
    defender.action === 'blockstun' ||
    (isNeutralGrounded && (defenderInput.guardHeld || holdingBack));
  const crouchingGuard = defenderInput.crouchHeld;

  if (attemptingGuard && canDirectionalGuardBlockMove(crouchingGuard, move)) {
    defender.hp = Math.max(1, defender.hp - move.chipDamage);
    defender.action = 'blockstun';
    defender.crouching = crouchingGuard;
    defender.actionTimerFrames = move.blockstunFrames;
    defender.actionTotalFrames = move.blockstunFrames;

    // On block: keep Jab & Cross glued close so blockstrings connect; push out on Finisher/Heavy
    const isFinisherOrHeavy =
      move.animStyle === 'finisher_punch' ||
      move.type === 'heavy' ||
      move.type === 'elemental';
    const blockPush = isFinisherOrHeavy
      ? move.blockPushback ?? move.knockback * 0.85
      : 1.05;
    defender.vx = dirX * blockPush;
    const isDefenderCornered =
      Math.abs(defender.x) >= STAGE_HALF_WIDTH - 0.45 &&
      Math.sign(dirX) === Math.sign(defender.x);
    if (isDefenderCornered) {
      // Item 4: Corner Pushback Transfer — push the attacker back when the defender's back is against the wall!
      attacker.vx = -dirX * Math.max(2.6, blockPush * 0.85);
    } else {
      attacker.vx = isFinisherOrHeavy ? 0 : dirX * 0.85;
    }
    defender.attackVisualTag = crouchingGuard ? 'LOW BLOCK' : 'STAND BLOCK';
    defender.attackVisualTimer = 0.55;

    attacker.meter = Math.min(
      attacker.maxMeter,
      attacker.meter + Math.round(move.meterGain * 0.5)
    );
    const frameAdv = move.blockstunFrames - move.recoveryFrames;
    attacker.lastFrameAdvantage = frameAdv;
    defender.lastFrameAdvantage = -frameAdv;
    state.hitstopTimerMs = Math.round(move.hitstopMs * 0.65);
    events.blockTriggered = true;
    events.impactSparkType = 'block';
    return;
  }

  // Check if defender currently has Anti-Stunlock Armor Immunity active
  if (defender.stunlockImmunityTimer > 0) {
    const armoredDamage = Math.max(5, Math.round(move.damage * 0.35));
    defender.hp = Math.max(0, defender.hp - armoredDamage);
    defender.hitFlashTimer = 0.08;
    attacker.vx = -dirX * 3.5;
    events.hitTriggered = true;
    events.impactSparkType = 'hit';
    state.lastEventBanner = 'STUNLOCK ARMOR!';
    state.bannerTimer = 0.8;
    return;
  }

  // Check if defender has Super Armor on their active/startup Heavy move (e.g. Ignis Brawler)
  if (defender.armorHitsRemaining > 0 && move.type !== 'ultimate') {
    defender.armorHitsRemaining -= 1;
    const armorDamage = Math.round(move.damage * 0.45);
    defender.hp = Math.max(1, defender.hp - armorDamage);
    defender.hitFlashTimer = 0.12;
    defender.attackVisualTag = 'ARMOR HIT!';
    defender.attackVisualTimer = 0.75;
    attacker.vx = 0;
    state.hitstopTimerMs = 55;
    state.lastEventBanner = 'SUPER ARMOR ABSORBED!';
    state.bannerTimer = 1.1;
    events.armorAbsorbed = true;
    events.hitTriggered = true;
    events.impactSparkType = 'heavy';
    return;
  }

  const wasInHitstun = defender.action === 'hitstun';
  const wasAirborne = !defender.grounded || defender.y > 0.12;
  const isCounterHit = defender.action === 'startup' || defender.action === 'active';
  const isPunishHit = defender.action === 'recovery' && !defender.moveHasConnected;
  const comboScaling = Math.max(0.45, 1 - attacker.comboCount * 0.08);
  const counterMult = isCounterHit ? 1.2 : 1.0;
  const finalDamage = Math.round(move.damage * comboScaling * counterMult);

  defender.hp = Math.max(0, defender.hp - finalDamage);
  defender.whiffRecoveryActive = false;

  if (wasInHitstun) {
    defender.stunlockCount += 1;
  } else {
    defender.stunlockCount = 1;
  }

  if (defender.stunlockCount >= MAX_STUNLOCK_HITS_BEFORE_ESCAPE) {
    defender.stunlockCount = 0;
    defender.stunlockImmunityTimer = STUNLOCK_IMMUNITY_DURATION_SECONDS;
    defender.action = 'idle';
    defender.actionTimerFrames = 0;
    defender.vx = dirX * 6.5;
    defender.vy = 4.0;
    defender.grounded = false;
    attacker.vx = -dirX * 5.5;
    attacker.comboCount = 0;
    attacker.airDribbleCount = 0;
    state.hitstopTimerMs = 55;
    state.lastEventBanner = 'STUNLOCK ESCAPE — COOLDOWN ARMOR!';
    state.bannerTimer = 1.5;
    events.stunlockEscapeTriggered = true;
    events.hitTriggered = true;
    events.impactSparkType = 'heavy';
    return;
  }

  const isHardKnockdownMove =
    move.animStyle === 'low_sweep' || move.type === 'ultimate';
  defender.action = isHardKnockdownMove ? 'knockdown' : 'hitstun';
  defender.hardKnockdown = isHardKnockdownMove;
  defender.wakeupRollDir = 0;
  defender.lastHitHeight = move.hitHeight;
  const totalHitstun = move.hitstunFrames + (isCounterHit ? 5 : 0);
  defender.actionTimerFrames = totalHitstun;
  defender.actionTotalFrames = totalHitstun;
  defender.hitFlashTimer = 0.12;

  if (isCounterHit) {
    events.counterHitTriggered = true;
    attacker.attackVisualTag = 'COUNTER HIT!';
    attacker.attackVisualTimer = 0.85;
    state.impactFrameTimer = 0.055;
    state.impactFrameColorHex = 0xf43f5e;
  } else if (isPunishHit) {
    events.punishTriggered = true;
    attacker.meter = Math.min(attacker.maxMeter, attacker.meter + 18);
    attacker.attackVisualTag = 'PUNISH!';
    attacker.attackVisualTimer = 0.85;
  }
  if (move.type === 'ultimate' || move.type === 'heavy' || move.type === 'down_punch') {
    events.floorCrackTriggered = true;
    if (move.type === 'ultimate') {
      state.impactFrameTimer = 0.06;
      state.impactFrameColorHex = 0x38bdf8;
    }
  }

  // Item 18: Cancel Window Flash — briefly illuminate striking hands/weapons when a cancelable move connects
  if (move.type !== 'ultimate') {
    attacker.cancelFlashTimer = 0.18;
  }

  // Close-range strike alignment on hit: only nudge into contact if already close (never teleport on long pokes!)
  const currentDist = Math.abs(defender.x - attacker.x);
  if (
    move.type !== 'elemental' &&
    move.type !== 'ultimate' &&
    currentDist > CONTACT_STICK_DIST &&
    currentDist <= CONTACT_STICK_DIST + 0.65
  ) {
    attacker.x += dirX * (currentDist - CONTACT_STICK_DIST) * 0.55;
  }

  // Air Dribble Juggle Mechanics with progressive Street Fighter Juggle Gravity & Finisher Spike!
  if (wasAirborne && (move.type === 'air_punch' || move.airDribblePopY)) {
    attacker.airDribbleCount += 1;
    events.airDribbleTriggered = true;

    defender.juggleGravityScale = Math.min(
      3.4,
      defender.juggleGravityScale + JUGGLE_GRAVITY_STEP
    );

    if (attacker.airDribbleCount >= MAX_AIR_DRIBBLES_PER_COMBO) {
      // 3rd Air Dribble Finisher Spike: slam the opponent down & away with knockdown immunity to end infinite air loops!
      defender.vy = -8.5;
      defender.vx = dirX * 5.5;
      defender.grounded = false;
      defender.action = 'knockdown';
      defender.stunlockImmunityTimer = Math.max(defender.stunlockImmunityTimer, 0.75);
      attacker.vx = -dirX * 2.2;
      attacker.vy = Math.min(attacker.vy, -1.5);
      events.floorCrackTriggered = true;
    } else {
      const rawPop = move.airDribblePopY ?? 6.8;
      const scaledPop = rawPop / Math.pow(defender.juggleGravityScale, 0.55);
      defender.y = Math.max(defender.y, 0.85);
      defender.vy = Math.max(5.8, scaledPop);
      defender.grounded = false;
      // Stick attacker and defender together in mid-air for the first 2 Air Dribbles
      defender.vx = dirX * 0.65;
      if (!attacker.grounded) {
        attacker.x = defender.x - dirX * CONTACT_STICK_DIST;
        attacker.y = defender.y;
        attacker.vx = defender.vx;
        attacker.vy = Math.max(attacker.vy, defender.vy * 0.94);
      }
    }
  } else {
    const isFinisher = move.animStyle === 'finisher_punch';
    const isSweep = move.animStyle === 'low_sweep';
    const isDefenderCornered =
      Math.abs(defender.x) >= STAGE_HALF_WIDTH - 0.45 &&
      Math.sign(dirX) === Math.sign(defender.x);
    if (isSweep) {
      // Item 3: Crouch Heavy Sweep [S + K] trips feet into Hard Knockdown!
      defender.vy = move.launchY;
      defender.vx = dirX * move.knockback;
      defender.grounded = false;
      attacker.vx = isDefenderCornered ? -dirX * 2.6 : 0;
    } else if (move.launchY > 0 && move.type !== 'air_punch') {
      // Launcher (e.g. Low Launcher ▲ or Heavy Overhead ▼):
      // Keep the enemy right in front of the attacker so follow-up air attacks stick!
      defender.vy = move.launchY;
      defender.grounded = false;
      defender.juggleGravityScale = 1.0;
      attacker.airDribbleCount = 0;
      const launchDrift = move.type === 'down_punch' ? 0.45 : 1.15;
      defender.vx = dirX * launchDrift;
      attacker.vx = dirX * launchDrift;
      events.launcherTriggered = true;
    } else if (isFinisher || move.type === 'elemental' || move.type === 'ultimate') {
      // 3rd Hit Finisher / Elemental / Ultimate: strong pushback after connecting squarely!
      defender.vx = dirX * move.knockback;
      attacker.vx = isDefenderCornered
        ? -dirX * Math.max(2.8, move.knockback * 0.78)
        : dirX * 1.4;
    } else {
      // Combo-building strikes (Jab Step 1, Cross Step 2, or jumping Air Punch on grounded foe):
      // Glue attacker and defender together with matching forward momentum!
      const stickySlide = 0.85;
      defender.vx = dirX * stickySlide;
      attacker.vx = isDefenderCornered ? -dirX * 1.1 : dirX * stickySlide;
    }
  }

  attacker.comboCount += 1;
  attacker.comboDamage += finalDamage;
  attacker.comboDecayTimer = 2.4;
  attacker.meter = Math.min(attacker.maxMeter, attacker.meter + move.meterGain);
  state.maxComboReached = Math.max(state.maxComboReached, attacker.comboCount);

  const frameAdv = totalHitstun - move.recoveryFrames;
  attacker.lastFrameAdvantage = frameAdv;
  defender.lastFrameAdvantage = -frameAdv;

  state.hitstopTimerMs = isCounterHit ? Math.min(85, move.hitstopMs + 15) : move.hitstopMs;
  events.hitTriggered = true;
  events.heavyHit = move.type !== 'light' || move.animStyle === 'finisher_punch' || isCounterHit;
  events.impactSparkType = events.heavyHit ? 'heavy' : 'hit';
  if (events.heavyHit && defender.hp > 0) {
    events.voiceFighterId = defender.id;
    events.voiceTriggered = 'hurt';
  }

  if (attemptingGuard && !canDirectionalGuardBlockMove(crouchingGuard, move)) {
    state.lastEventBanner =
      move.hitHeight === 'low'
        ? 'LOW LAUNCHER ▲ BROKE STAND GUARD!'
        : 'OVERHEAD ▼ CRUSHED LOW GUARD!';
    state.bannerTimer = 1.3;
  } else if (events.airDribbleTriggered && attacker.airDribbleCount >= MAX_AIR_DRIBBLES_PER_COMBO) {
    state.lastEventBanner = 'AIR DRIBBLE FINISHER SLAM!';
    state.bannerTimer = 1.35;
  } else if (events.airDribbleTriggered && attacker.airDribbleCount >= 1) {
    state.lastEventBanner = `AIR DRIBBLE x${attacker.airDribbleCount}!`;
    state.bannerTimer = 1.2;
  } else if (move.animStyle === 'low_sweep') {
    state.lastEventBanner = 'HARD KNOCKDOWN SWEEP ◢!';
    state.bannerTimer = 1.25;
  } else if (move.type === 'down_punch') {
    state.lastEventBanner = 'LOW LAUNCHER ▲!';
    state.bannerTimer = 1.0;
  } else if (isCounterHit) {
    state.lastEventBanner = `COUNTER HIT! (+${frameAdv}F)`;
    state.bannerTimer = 1.25;
  } else if (isPunishHit) {
    state.lastEventBanner = 'WHIFF PUNISH! (+18 METER)';
    state.bannerTimer = 1.25;
  } else if (attacker.comboCount >= 3) {
    state.lastEventBanner = `${attacker.comboCount} HIT COMBO!`;
    state.bannerTimer = 1.1;
  }
}
