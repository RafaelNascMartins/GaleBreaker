import { DEFAULT_SETTINGS, FIGHTERS } from './fighters';
import { FighterId, GameSettings, KeyBindingMap } from './types';

export const MAX_SKILL_POINTS = 4;
export const DEFAULT_SKILLS: Record<FighterId, string[]> = {
  kaze: ['kaze_combo_1', 'kaze_elem_1'],
  ignis: ['ignis_combo_1'],
  tophia: ['tophia_def_1'],
  volt: ['volt_combo_1'],
};
const STORAGE_KEY = 'gale-breaker.preferences.v1';
const RESERVED_KEYS = new Set(['Escape', 'KeyP', 'KeyR', 'KeyM', 'Tab', 'F5', 'F11', 'F12']);

export function isBindableKey(code: unknown): code is string {
  return typeof code === 'string' && !RESERVED_KEYS.has(code) &&
    /^(Key[A-Z]|Digit[0-9]|Numpad[0-9]|Arrow(Up|Down|Left|Right)|Space|Enter|Shift(Left|Right)|Control(Left|Right)|Alt(Left|Right)|Backspace|CapsLock|Minus|Equal|BracketLeft|BracketRight|Backslash|Semicolon|Quote|Comma|Period|Slash|Backquote|Numpad(Add|Subtract|Multiply|Divide|Decimal|Enter))$/.test(code);
}

export function bindingConflict(settings: GameSettings, player: 1 | 2, action: keyof KeyBindingMap, code: string): string | null {
  if (!isBindableKey(code)) return 'This key is reserved or unsupported. Choose another key.';
  for (const p of [1, 2] as const) {
    const map = p === 1 ? settings.p1Keys : settings.p2Keys;
    if (Object.entries(map).some(([name, key]) => key === code && !(p === player && name === action))) {
      return 'This key is already assigned. Choose another key.';
    }
  }
  return null;
}

export function normalizeSkills(id: FighterId, value: unknown): string[] {
  if (!Array.isArray(value)) return [...DEFAULT_SKILLS[id]];
  const result: string[] = [];
  let spent = 0;
  for (const node of [...FIGHTERS[id].skillTree].sort((a, b) => a.tier - b.tier)) {
    const prerequisite = FIGHTERS[id].skillTree.find(n => n.branch === node.branch && n.tier === 1);
    if (value.includes(node.id) && spent + node.cost <= MAX_SKILL_POINTS &&
        (node.tier === 1 || !prerequisite || result.includes(prerequisite.id))) {
      result.push(node.id);
      spent += node.cost;
    }
  }
  return result;
}

export function toggleSkill(id: FighterId, current: string[], skillId: string): string[] {
  const node = FIGHTERS[id].skillTree.find(n => n.id === skillId);
  if (!node) return current;
  if (current.includes(skillId)) {
    return current.filter(key => key !== skillId && !(node.tier === 1 &&
      FIGHTERS[id].skillTree.some(n => n.id === key && n.branch === node.branch && n.tier > 1)));
  }
  const normalized = normalizeSkills(id, [...current, skillId]);
  return normalized.includes(skillId) && current.every(key => normalized.includes(key)) ? normalized : current;
}

export function normalizeSettings(value: unknown): GameSettings {
  const next = structuredClone(DEFAULT_SETTINGS);
  if (!value || typeof value !== 'object') return next;
  const raw = value as Record<string, unknown>;
  for (const key of ['masterVolume', 'sfxVolume', 'announcerVolume', 'fov'] as const) {
    if (typeof raw[key] === 'number' && Number.isFinite(raw[key])) {
      next[key] = Math.max(key === 'fov' ? 30 : 0, Math.min(key === 'fov' ? 90 : 1, raw[key] as number));
    }
  }
  for (const key of ['muted', 'celOutlines', 'showHitboxes', 'cameraShake', 'dynamicZoom'] as const) {
    if (typeof raw[key] === 'boolean') next[key] = raw[key] as boolean;
  }
  if (['low', 'medium', 'high'].includes(raw.particleDensity as string)) next.particleDensity = raw.particleDensity as GameSettings['particleDensity'];
  // Accept complete, unique maps atomically so invalid saves cannot strand an action.
  const used = new Set<string>();
  const maps = {} as Pick<GameSettings, 'p1Keys' | 'p2Keys'>;
  for (const player of ['p1Keys', 'p2Keys'] as const) {
    const map = raw[player] as KeyBindingMap | undefined;
    if (!map || typeof map !== 'object') return next;
    maps[player] = { ...next[player] };
    for (const action of Object.keys(next[player]) as (keyof KeyBindingMap)[]) {
      const code = map[action];
      if (!isBindableKey(code) || used.has(code)) return next;
      used.add(code);
      maps[player][action] = code;
    }
  }
  return { ...next, ...maps };
}

export function loadPreferences(storage?: Pick<Storage, 'getItem'>) {
  let saved: Record<string, unknown> = {};
  try {
    const raw = (storage ?? window.localStorage).getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    if (parsed?.version === 1) saved = parsed;
  } catch { /* Storage may be disabled or contain malformed data. */ }
  const skills = {} as Record<FighterId, string[]>;
  for (const id of Object.keys(FIGHTERS) as FighterId[]) {
    skills[id] = normalizeSkills(id, (saved.skills as Record<string, unknown> | undefined)?.[id]);
  }
  return { settings: normalizeSettings(saved.settings), skills };
}

export function savePreferences(settings: GameSettings, skills: Record<FighterId, string[]>, storage?: Pick<Storage, 'setItem'>) {
  try {
    (storage ?? window.localStorage).setItem(STORAGE_KEY, JSON.stringify({ version: 1, settings, skills }));
  } catch { /* Keep the game usable when storage is unavailable or full. */ }
}
