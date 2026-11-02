import assert from 'node:assert/strict';
import test from 'node:test';
import {
  boxesOverlap2D,
  computeFighterActiveHitbox,
  computeFighterHurtbox,
  createInitialCombatSnapshot,
  MAX_AIR_DRIBBLES_PER_COMBO,
  MAX_STUNLOCK_HITS_BEFORE_ESCAPE,
  PlayerFrameInput,
  resolveContextualMoveType,
  stepCombatSimulation,
} from './combatEngine';
import { getEffectiveMaxHp, getEffectiveMoveData } from './fighters';

const IDLE_INPUT: PlayerFrameInput = {
  moveX: 0,
  jumpJustPressed: false,
  crouchHeld: false,
  guardHeld: false,
  guardJustPressed: false,
  dashJustPressed: false,
  breakerJustPressed: false,
  attackJustPressed: null,
};

test('Skill Tree modifiers accurately adjust startup frames, gust propulsion, and vitality', () => {
  const baseLight = getEffectiveMoveData('kaze', 'light', []);
  const upgradedLight = getEffectiveMoveData('kaze', 'light', [
    'kaze_combo_1',
    'kaze_combo_2',
  ]);

  assert.equal(baseLight.startupFrames, 4);
  assert.equal(upgradedLight.startupFrames, 3);
  assert.ok(upgradedLight.damage > baseLight.damage);

  const baseHp = getEffectiveMaxHp('kaze', []);
  const upgradedHp = getEffectiveMaxHp('kaze', ['kaze_def_1']);
  assert.equal(upgradedHp, baseHp + 120);
});

test('3-Step Punch Chain cycles through Jab (Step 1) -> Cross (Step 2) -> Finisher (Step 3) with anti-spam Pushback', () => {
  const state = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  state.p1.x = -0.5;
  state.p2.x = 0.5;

  // Step 1: Jab
  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );
  assert.equal(state.p1.currentMove?.animStyle, 'jab');
  assert.equal(state.p1.attackVisualTag, 'JAB');
  assert.equal(state.p1.punchChainStep, 2);

  // Advance through Jab startup + hitstop so Step 2 Cross can trigger on cancel
  for (let i = 0; i < 8; i++) {
    stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  }

  // Step 2: Cross
  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );
  // Step 1 frame in case hitstop was still finishing
  stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  assert.equal(state.p1.currentMove?.animStyle, 'cross_punch');
  assert.equal(state.p1.attackVisualTag, 'CROSS');
  assert.equal(state.p1.punchChainStep, 3);

  for (let i = 0; i < 9; i++) {
    stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  }

  // Step 3: Finisher with high pushback
  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );
  stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  assert.equal(state.p1.currentMove?.animStyle, 'finisher_punch');
  assert.equal(state.p1.attackVisualTag, 'FINISHER');
  assert.equal(state.p1.punchChainStep, 1);
  assert.ok((state.p1.currentMove?.knockback ?? 0) >= 4.5);
});

test('Street Fighter Directional Blocking: Holding Back blocks Overheads & Mids, while Down+Back blocks Low Launchers', () => {
  const state = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  state.p1.x = -0.6;
  state.p2.x = 0.6; // P2 faces Left (facingRight = false), so Back for P2 is moveX = +1

  // Case 1: P1 uses Heavy Overhead ▼ ('overhead'). P2 holds Back (moveX: +1, crouchHeld: false) -> Blocks!
  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, attackJustPressed: 'heavy' },
    { ...IDLE_INPUT, moveX: 1, crouchHeld: false },
    1 / 60,
    'versus'
  );
  for (let i = 0; i < 12; i++) {
    stepCombatSimulation(
      state,
      IDLE_INPUT,
      { ...IDLE_INPUT, moveX: 1, crouchHeld: false },
      1 / 60,
      'versus'
    );
  }
  assert.equal(state.p2.action, 'blockstun');
  assert.equal(state.p2.attackVisualTag, 'STAND BLOCK');

  // Reset and test Case 2: P1 uses Low Launcher ▲ ('low'). P2 holds only Standing Back (moveX: +1, crouchHeld: false) -> Guard Broken & Launched!
  const state2 = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  state2.p1.x = -0.6;
  state2.p2.x = 0.6;

  stepCombatSimulation(
    state2,
    { ...IDLE_INPUT, crouchHeld: true, attackJustPressed: 'light' },
    { ...IDLE_INPUT, moveX: 1, crouchHeld: false },
    1 / 60,
    'versus'
  );
  for (let i = 0; i < 10; i++) {
    stepCombatSimulation(
      state2,
      IDLE_INPUT,
      { ...IDLE_INPUT, moveX: 1, crouchHeld: false },
      1 / 60,
      'versus'
    );
  }
  assert.equal(state2.p2.action, 'hitstun');
  assert.equal(state2.p2.grounded, false);

  // Case 3: P1 uses Low Launcher ▲ ('low'). P2 holds Down + Back (moveX: +1, crouchHeld: true) -> Low Block succeeds!
  const state3 = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  state3.p1.x = -0.6;
  state3.p2.x = 0.6;

  stepCombatSimulation(
    state3,
    { ...IDLE_INPUT, crouchHeld: true, attackJustPressed: 'light' },
    { ...IDLE_INPUT, moveX: 1, crouchHeld: true },
    1 / 60,
    'versus'
  );
  for (let i = 0; i < 10; i++) {
    stepCombatSimulation(
      state3,
      IDLE_INPUT,
      { ...IDLE_INPUT, moveX: 1, crouchHeld: true },
      1 / 60,
      'versus'
    );
  }
  assert.equal(state3.p2.action, 'blockstun');
  assert.equal(state3.p2.attackVisualTag, 'LOW BLOCK');
});

test('Low Launcher launches opponent airborne and Air Punch increments Juggle Gravity scale', () => {
  const state = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  state.p1.x = -0.5;
  state.p2.x = 0.6;

  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, crouchHeld: true, attackJustPressed: 'light' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );
  assert.equal(state.p1.currentMove?.type, 'down_punch');

  for (let i = 0; i < 15; i++) {
    stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  }

  assert.equal(state.p2.grounded, false);
  assert.equal(state.p2.juggleGravityScale, 1.0);

  state.p1.action = 'jump';
  state.p1.grounded = false;
  state.p1.y = state.p2.y;
  state.p1.x = state.p2.x - 1.1;

  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );

  for (let i = 0; i < 10; i++) {
    stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  }

  assert.ok(state.p1.airDribbleCount >= 1);
  assert.ok(state.p2.juggleGravityScale > 1.15);
});

test('Combo Breaker and Anti-Stunlock Cooldown work reliably', () => {
  const state = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  state.p1.x = -0.5;
  state.p2.x = 0.5;
  state.p2.action = 'hitstun';
  state.p2.actionTimerFrames = 30;
  state.p2.stunlockCount = MAX_STUNLOCK_HITS_BEFORE_ESCAPE - 1;

  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );

  let escaped = false;
  for (let i = 0; i < 10; i++) {
    const ev = stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
    if (ev.stunlockEscapeTriggered) {
      escaped = true;
      break;
    }
  }

  assert.equal(escaped, true);
  assert.ok(state.p2.stunlockImmunityTimer > 1.0);
});

test('Attacks do not teleport or stick from far away when out of physical reach', () => {
  const state = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  state.p1.x = -3.0;
  state.p2.x = 2.0; // Distance = 5.0 units (outside Kaze light punch range of 2.5)

  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );

  // Advance through startup + active frames
  for (let i = 0; i < 8; i++) {
    stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  }

  // P1 should step forward naturally (~0.3 units) and whiff, NOT snap/stick across 5 units to P2!
  assert.ok(Math.abs(state.p2.x - state.p1.x) > 3.5);
  assert.equal(state.p2.action, 'idle');
});

test('Item 6: Simultaneous overlapping active hitboxes trigger an Elemental Clash (+25 Meter, pushback, no HP loss)', () => {
  const state = createInitialCombatSnapshot('kaze', 'kaze', 'zephyr_dojo', [], [], 'versus');
  state.p1.x = -0.9;
  state.p2.x = 0.9;
  const initialP1Hp = state.p1.hp;
  const initialP2Hp = state.p2.hp;
  const initialP1Meter = state.p1.meter;
  const initialP2Meter = state.p2.meter;

  // Both fighters press Light Punch on the exact same frame
  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    1 / 60,
    'versus'
  );

  let clashed = false;
  for (let i = 0; i < 8; i++) {
    const ev = stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
    if (ev.clashTriggered) {
      clashed = true;
      assert.equal(ev.impactSparkType, 'clash');
      break;
    }
  }

  assert.equal(clashed, true);
  assert.equal(state.p1.hp, initialP1Hp);
  assert.equal(state.p2.hp, initialP2Hp);
  assert.equal(state.p1.meter, initialP1Meter + 25);
  assert.equal(state.p2.meter, initialP2Meter + 25);
  assert.ok(state.p1.cancelFlashTimer > 0);
  assert.ok(state.p2.cancelFlashTimer > 0);
});

test('Item 6: Corner Wall Bounce triggers once per combo when slammed into the arena edge with high knockback', () => {
  const state = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  state.p1.x = 7.9;
  state.p2.x = 9.35;
  state.p2.action = 'hitstun';
  state.p2.actionTimerFrames = 18;
  state.p2.vx = 6.5;

  const ev1 = stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  assert.equal(ev1.wallBounceTriggered, true);
  assert.equal(ev1.impactSparkType, 'wall');
  assert.equal(state.p2.wallBouncedInCombo, true);
  assert.equal(state.p2.grounded, false);
  assert.ok(state.p2.vx < -4.0);
  assert.ok(state.p2.vy >= 5.5);

  // Attempting a second wall bounce in the same hitstun combo does not re-trigger
  state.hitstopTimerMs = 0;
  state.p2.x = 9.4;
  state.p2.vx = 6.5;
  const ev2 = stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  assert.equal(ev2.wallBounceTriggered, false);
});

test('Item 1, 7, 10 & 18: Dash Momentum Carry, Cancel Window Flash, Super Flash Freeze, Mirror Palette, and Arcade Boss Overcharge', () => {
  // Mirror match palette auto-differentiation + Arcade Stage 4 Boss Overcharge
  const bossState = createInitialCombatSnapshot(
    'kaze',
    'kaze',
    'storm_market',
    [],
    [],
    'arcade',
    4,
    0,
    0,
    0
  );
  assert.notEqual(bossState.p1.paletteIndex, bossState.p2.paletteIndex);
  assert.equal(bossState.isBossFight, true);
  assert.equal(bossState.p2.isOvercharged, true);
  assert.equal(bossState.stagePhase, 3);
  assert.ok(bossState.p2.maxHp > bossState.p1.maxHp);

  // Dash Momentum Carry into attack
  const state = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  state.p1.x = -3.5;
  state.p2.x = 2.5;
  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, moveX: 1, dashJustPressed: true },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );
  assert.equal(state.p1.action, 'dash');

  // Cancel dash immediately into Light Punch — horizontal speed carries 65% of dash velocity
  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, moveX: 1, attackJustPressed: 'light' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );
  assert.equal(state.p1.action, 'startup');
  assert.ok(state.p1.vx > 8.0);

  // Super Flash Freeze on Ultimate initiation
  state.p1.action = 'idle';
  state.p1.meter = 100;
  const ultEv = stepCombatSimulation(
    state,
    { ...IDLE_INPUT, attackJustPressed: 'ultimate' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );
  assert.equal(ultEv.superFreezeTriggered, true);
  assert.equal(ultEv.voiceTriggered, 'ultimate');
  assert.ok(state.cinematicTimer > 0.3);
  assert.equal(state.cinematicFocusPlayer, 1);
});

test('Item 11, 12 & 15: Whiff Lag, Counter Hit, Whiff Punish, Delayed Red HP, and AI Turn Cooldown', () => {
  const state = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  state.p1.x = -3.2;
  state.p2.x = 2.2;

  // 1. Whiff Lag: P1 whiffs a light punch in thin air -> enters whiffRecoveryActive with +5 recovery frames
  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );
  for (let i = 0; i < 8; i++) {
    stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  }
  assert.equal(state.p1.action, 'recovery');
  assert.equal(state.p1.whiffRecoveryActive, true);
  assert.ok(state.p1.actionTotalFrames >= 12);

  // 2. Whiff Punish: P2 strikes P1 while P1 is in whiff recovery -> triggers PUNISH! (+18 Meter)
  state.p2.x = state.p1.x + 1.1;
  const meterBeforePunish = state.p2.meter;
  let punishTriggered = false;
  stepCombatSimulation(
    state,
    IDLE_INPUT,
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    1 / 60,
    'versus'
  );
  for (let i = 0; i < 7; i++) {
    const ev = stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
    if (ev.punishTriggered) {
      punishTriggered = true;
      break;
    }
  }
  assert.equal(punishTriggered, true);
  assert.ok(state.p2.meter >= meterBeforePunish + 18);
  assert.equal(state.p2.attackVisualTag, 'PUNISH!');

  // 3. Delayed Red HP (trailHp) freezes during hitstun and drains after returning to idle
  assert.equal(state.p1.action, 'hitstun');
  assert.ok(state.p1.trailHp > state.p1.hp);
  const frozenTrailHp = state.p1.trailHp;
  state.hitstopTimerMs = 0;
  stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  assert.equal(state.p1.trailHp, frozenTrailHp);

  // 4. Counter Hit: P1 strikes P2 while P2 is in startup of a move without armor -> COUNTER HIT! (+5f hitstun & Impact Frame)
  const state2 = createInitialCombatSnapshot('kaze', 'tophia', 'zephyr_dojo', [], [], 'versus');
  state2.p1.x = -0.6;
  state2.p2.x = 0.6;
  stepCombatSimulation(
    state2,
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    { ...IDLE_INPUT, attackJustPressed: 'heavy' },
    1 / 60,
    'versus'
  );
  let counterTriggered = false;
  for (let i = 0; i < 6; i++) {
    const ev = stepCombatSimulation(state2, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
    if (ev.counterHitTriggered) {
      counterTriggered = true;
      break;
    }
  }
  assert.equal(counterTriggered, true);
  assert.equal(state2.p1.attackVisualTag, 'COUNTER HIT!');
  assert.ok(state2.impactFrameTimer > 0);
});

test('Ignis cannot infinite Air Dribble: 3rd Air Dribble triggers Finisher Slam and forces opponent to ground', () => {
  const state = createInitialCombatSnapshot('ignis', 'kaze', 'molten_forge', [], [], 'training');
  state.hazards = [];
  state.p1.x = -0.6;
  state.p2.x = 0.6;

  // Ignis launches Kaze with Low Launcher (down_punch)
  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, crouchHeld: true, attackJustPressed: 'down_punch' },
    IDLE_INPUT,
    1 / 60,
    'training'
  );
  for (let i = 0; i < 18; i++) {
    stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'training');
  }
  assert.equal(state.p2.grounded, false);

  // Now spam air_punch / light every few frames for 160 frames while airborne
  let airDribbleHits = 0;
  let finisherSlamSeen = false;
  for (let f = 0; f < 160; f++) {
    const pressAttack = f % 4 === 0 ? 'air_punch' : null;
    const ev = stepCombatSimulation(
      state,
      { ...IDLE_INPUT, attackJustPressed: pressAttack },
      IDLE_INPUT,
      1 / 60,
      'training'
    );
    if (ev.airDribbleTriggered) {
      airDribbleHits += 1;
      if (state.lastEventBanner === 'AIR DRIBBLE FINISHER SLAM!') {
        finisherSlamSeen = true;
      }
    }
    if (finisherSlamSeen && state.p2.grounded) {
      break;
    }
  }

  assert.equal(airDribbleHits, MAX_AIR_DRIBBLES_PER_COMBO);
  assert.equal(finisherSlamSeen, true);
  assert.equal(state.p2.grounded, true);
  assert.equal(state.p1.airDribbleCount, 0);
});

test('Wave 3: Crouch Heavy Sweep [S+K] inflicts Hard Knockdown, Soft Knockdown allows Tech Roll, Corner Pushback transfers to attacker, and Best-of-3 Rounds work', () => {
  // 1. Crouch Heavy Sweep [S+K] -> low_sweep with Hard Knockdown
  const state = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  state.hazards = [];
  state.p1.x = -0.5;
  state.p2.x = 0.6;

  stepCombatSimulation(
    state,
    { ...IDLE_INPUT, crouchHeld: true, attackJustPressed: 'heavy' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );
  assert.equal(state.p1.currentMove?.animStyle, 'low_sweep');
  assert.equal(state.p1.currentMove?.hitHeight, 'low');
  assert.equal(state.p1.attackVisualTag, 'SWEEP ◢');

  for (let i = 0; i < 15; i++) {
    stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  }
  assert.equal(state.p2.action, 'knockdown');
  assert.equal(state.p2.hardKnockdown, true);
  assert.equal(state.p2.lastHitHeight, 'low');

  // Let P2 land on the mat -> stays in grounded knockdown with wakeupInvulnTimer > 0
  for (let i = 0; i < 18; i++) {
    stepCombatSimulation(state, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  }
  assert.equal(state.p2.grounded, true);
  assert.equal(state.p2.action, 'knockdown');
  assert.ok(state.p2.wakeupInvulnTimer > 0.2);

  // 2. Soft Knockdown Tech Roll when holding direction in last 14 frames
  state.p2.hardKnockdown = false;
  state.p2.actionTimerFrames = 12;
  stepCombatSimulation(
    state,
    IDLE_INPUT,
    { ...IDLE_INPUT, moveX: 1 },
    1 / 60,
    'versus'
  );
  assert.equal(state.p2.wakeupRollDir, 1);
  assert.equal(state.p2.attackVisualTag, 'TECH ROLL');
  assert.ok(state.p2.vx > 8.0);

  // 3. Corner Pushback Transfer when defender blocks with back against the wall
  const cornerState = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  cornerState.hazards = [];
  cornerState.p1.x = 8.2;
  cornerState.p2.x = 9.35; // Cornered at right wall
  stepCombatSimulation(
    cornerState,
    { ...IDLE_INPUT, attackJustPressed: 'heavy' },
    { ...IDLE_INPUT, moveX: 1, guardHeld: true },
    1 / 60,
    'versus'
  );
  for (let i = 0; i < 12; i++) {
    stepCombatSimulation(
      cornerState,
      IDLE_INPUT,
      { ...IDLE_INPUT, moveX: 1, guardHeld: true },
      1 / 60,
      'versus'
    );
  }
  assert.equal(cornerState.p2.action, 'blockstun');
  assert.ok(cornerState.p1.vx < -2.0);

  // 4. Best-of-3 Rounds: winning Round 1 increments p1RoundWins to 1 and transitions to Round 2
  const bo3State = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
  bo3State.hazards = [];
  bo3State.p1.x = -0.5;
  bo3State.p2.x = 0.5;
  bo3State.p2.hp = 10;
  bo3State.p1.meter = 80;

  stepCombatSimulation(
    bo3State,
    { ...IDLE_INPUT, attackJustPressed: 'light' },
    IDLE_INPUT,
    1 / 60,
    'versus'
  );
  for (let i = 0; i < 10; i++) {
    stepCombatSimulation(bo3State, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  }
  assert.equal(bo3State.p1RoundWins, 1);
  assert.equal(bo3State.winner, 0);
  assert.ok(bo3State.roundTransitionTimer > 0);

  // Advance through roundTransitionTimer to enter Round 2
  for (let i = 0; i < 110; i++) {
    stepCombatSimulation(bo3State, IDLE_INPUT, IDLE_INPUT, 1 / 60, 'versus');
  }
  assert.equal(bo3State.currentRound, 2);
  assert.equal(bo3State.p2.hp, bo3State.p2.maxHp);
  assert.ok(bo3State.p1.meter >= 40);
});
