import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from 'three';
import { DEFAULT_SETTINGS } from './fighters';
import { createInitialCombatSnapshot, PlayerFrameInput, stepCombatSimulation } from './combatEngine';
import { FixedStepClock, SIMULATION_STEP } from './fixedStep';
import { bindingConflict, loadPreferences, normalizeSettings, normalizeSkills, savePreferences, toggleSkill } from './preferences';
import { disposeObjectResources } from './render/disposeResources';
import { TransitionTimers } from './transitionTimers';

test('key remapping rejects reserved keys and collisions across both players', () => {
  for (const code of ['KeyR', 'KeyP', 'KeyM', 'Escape', 'Tab', 'F5']) {
    assert.ok(bindingConflict(DEFAULT_SETTINGS, 1, 'lightAttack', code));
  }
  assert.ok(bindingConflict(DEFAULT_SETTINGS, 1, 'lightAttack', 'KeyW'));
  assert.ok(bindingConflict(DEFAULT_SETTINGS, 1, 'lightAttack', 'Numpad1'));
  assert.equal(bindingConflict(DEFAULT_SETTINGS, 1, 'lightAttack', 'KeyJ'), null);
  assert.equal(bindingConflict(DEFAULT_SETTINGS, 1, 'lightAttack', 'KeyH'), null);
});

test('removing a prerequisite also removes its dependent skills', () => {
  assert.deepEqual(toggleSkill('kaze', ['kaze_combo_1', 'kaze_combo_2', 'kaze_elem_1'], 'kaze_combo_1'), ['kaze_elem_1']);
  assert.deepEqual(toggleSkill('kaze', [], 'kaze_combo_2'), []);
});

test('unlocking cannot exceed the budget or replace existing skills', () => {
  const full = ['kaze_combo_1', 'kaze_combo_2', 'kaze_elem_1'];
  assert.deepEqual(toggleSkill('kaze', full, 'kaze_def_1'), full);
  assert.deepEqual(toggleSkill('kaze', full, 'missing'), full);
  assert.deepEqual(normalizeSkills('kaze', ['kaze_combo_2', 'missing']), []);
});

test('saved preferences round-trip controls, volume and skills', () => {
  const entries = new Map<string, string>();
  const storage = { getItem: (key: string) => entries.get(key) ?? null, setItem: (key: string, value: string) => { entries.set(key, value); } };
  const settings = structuredClone(DEFAULT_SETTINGS);
  settings.p1Keys.lightAttack = 'KeyH';
  settings.masterVolume = 0.25;
  const skills = { kaze: ['kaze_combo_1', 'kaze_combo_2'], ignis: [], tophia: [], volt: [] };
  savePreferences(settings, skills, storage);
  assert.deepEqual(loadPreferences(storage), { settings, skills });
});

test('malformed, future-version and unavailable storage fall back safely', () => {
  for (const value of ['{invalid', 'null', '[]', '{"version":2,"settings":{"muted":true}}']) {
    const loaded = loadPreferences({ getItem: () => value });
    assert.deepEqual(loaded.settings, DEFAULT_SETTINGS);
    assert.ok(loaded.skills.kaze.includes('kaze_combo_1'));
  }
  const storage = { getItem: () => { throw new Error('blocked'); }, setItem: () => { throw new Error('quota'); } };
  const loaded = loadPreferences(storage);
  assert.doesNotThrow(() => savePreferences(loaded.settings, loaded.skills, storage));
});

test('saved settings clamp numbers and reject invalid bindings', () => {
  const settings = normalizeSettings({ ...DEFAULT_SETTINGS, masterVolume: 20, sfxVolume: -2, fov: 500,
    p1Keys: { ...DEFAULT_SETTINGS.p1Keys, lightAttack: 'KeyR' } });
  assert.equal(settings.masterVolume, 1);
  assert.equal(settings.sfxVolume, 0);
  assert.equal(settings.fov, 90);
  assert.deepEqual(settings.p1Keys, DEFAULT_SETTINGS.p1Keys);
  assert.equal(normalizeSettings({ masterVolume: NaN }).masterVolume, DEFAULT_SETTINGS.masterVolume);
});

const IDLE: PlayerFrameInput = {
  moveX: 0, jumpJustPressed: false, crouchHeld: false, guardHeld: false,
  guardJustPressed: false, dashJustPressed: false, breakerJustPressed: false, attackJustPressed: null,
};

test('combat produces the same result at 30, 60 and 144 rendered frames per second', () => {
  function simulate(fps: number) {
    const state = createInitialCombatSnapshot('kaze', 'ignis', 'zephyr_dojo', [], [], 'versus');
    state.hazards = [];
    state.p1.x = -0.5;
    state.p2.x = 0.5;
    const clock = new FixedStepClock();
    let steps = 0;
    for (let frame = 0; frame < fps * 2; frame++) {
      clock.advance(1 / fps, dt => {
        assert.equal(dt, SIMULATION_STEP);
        stepCombatSimulation(state, { ...IDLE, attackJustPressed: steps === 0 ? 'light' : null }, IDLE, dt, 'versus');
        steps++;
      });
    }
    assert.equal(steps, 120);
    return state;
  }
  assert.deepEqual(simulate(30), simulate(60));
  assert.deepEqual(simulate(144), simulate(60));
});

test('fixed clock bounds catch-up and clears residual time on reset', () => {
  const clock = new FixedStepClock();
  let steps = 0;
  clock.advance(1 / 144, () => steps++);
  assert.equal(steps, 0);
  clock.reset();
  clock.advance(10, () => steps++);
  assert.equal(steps, 15);
  clock.reset();
  clock.advance(SIMULATION_STEP / 2, () => steps++);
  assert.equal(steps, 15);
});

test('canceling transitions prevents stale result and nested loading callbacks', async () => {
  const timers = new TransitionTimers();
  const fired: string[] = [];
  timers.schedule(() => fired.push('old KO'), 5);
  timers.cancel();
  timers.schedule(() => {
    fired.push('new match');
    timers.schedule(() => fired.push('stale loading'), 5);
    timers.cancel();
  }, 0);
  await new Promise(resolve => setTimeout(resolve, 30));
  assert.deepEqual(fired, ['new match']);
});

test('disposing a model releases shared geometry once and preserves arena textures', () => {
  const root = new THREE.Group();
  const geometry = new THREE.BoxGeometry();
  const texture = new THREE.Texture();
  const material = new THREE.MeshToonMaterial({ gradientMap: texture });
  let geometryDisposed = 0, materialDisposed = 0, textureDisposed = 0;
  geometry.addEventListener('dispose', () => geometryDisposed++);
  material.addEventListener('dispose', () => materialDisposed++);
  texture.addEventListener('dispose', () => textureDisposed++);
  root.add(new THREE.Mesh(geometry, material), new THREE.Mesh(geometry, material));
  disposeObjectResources(root);
  assert.equal(geometryDisposed, 1);
  assert.equal(materialDisposed, 1);
  assert.equal(textureDisposed, 0);
});
