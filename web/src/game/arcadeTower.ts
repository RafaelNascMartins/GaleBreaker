import { FIGHTERS } from './fighters';
import { FighterId, FighterRuntimeState, StageId } from './types';

export interface ArcadeStageSpec {
  stageIndex: 1 | 2 | 3 | 4;
  title: string;
  opponentId: FighterId;
  stageId: StageId;
  aiArchetype: FighterRuntimeState['aiArchetype'];
  aiTempo: number;
  opponentPalette: number;
  isBoss: boolean;
  rivalryBanner: string;
  unlockedSkills: string[];
}

const ALL_FIGHTERS: FighterId[] = ['kaze', 'ignis', 'tophia', 'volt'];
const STAGE_BY_FIGHTER: Record<FighterId, StageId> = {
  kaze: 'zephyr_dojo',
  ignis: 'molten_forge',
  tophia: 'storm_market',
  volt: 'storm_market',
};

const RIVAL_PAIR: Record<FighterId, FighterId> = {
  kaze: 'volt',
  volt: 'kaze',
  ignis: 'tophia',
  tophia: 'ignis',
};

const BOSS_PAIR: Record<FighterId, FighterId> = {
  kaze: 'ignis',
  ignis: 'volt',
  tophia: 'kaze',
  volt: 'tophia',
};

const RIVALRY_QUOTES: Record<FighterId, Record<FighterId, string>> = {
  kaze: {
    kaze: 'SHADOW TRIAL — SURPASS YOUR OWN WIND!',
    ignis: 'GALE VS MAGMA — DISPERSE THE VOLCANIC ASH!',
    tophia: 'WIND VS MONOLITH — ERODE THE GOLDEN FORTRESS!',
    volt: 'RIVAL CLASH — WIND SHINOBI VS THUNDER ASSASSIN!',
  },
  ignis: {
    kaze: 'SCORCH THE SKY — BURN THROUGH THE HURRICANE!',
    ignis: 'CRUCIBLE MIRROR — FORGE THE STRONGEST FLAME!',
    tophia: 'RIVAL CLASH — VOLCANIC FIST VS UNBREAKABLE EARTH!',
    volt: 'PLASMA & PYRE — OUTPACE THE LIGHTNING FLASH!',
  },
  tophia: {
    kaze: 'SILENCE THE GALE — ANCHOR THE MOUNTAIN PEAK!',
    ignis: 'RIVAL CLASH — IMPERIAL MONOLITH VS MOLTEN FURY!',
    tophia: 'SOVEREIGN TRIAL — GOLDEN EARTH RESONANCE!',
    volt: 'GROUND THE STORM — SHATTER THE CYBER BLITZ!',
  },
  volt: {
    kaze: 'RIVAL CLASH — SUPERSONIC SPARK VS RAZOR WIND!',
    ignis: 'HIGH-VOLTAGE OVERLOAD — CRUSH THE IRON ANVIL!',
    tophia: 'PIERCE THE MONOLITH — SHATTER GOLD WITH LIGHTNING!',
    volt: 'SHORT CIRCUIT — TWIN TONFA OVERDRIVE!',
  },
};

export const ARCADE_TOTAL_STAGES = 4;

export function getArcadeStageSpec(
  p1Id: FighterId,
  rawStageIndex: number
): ArcadeStageSpec {
  const clamped = Math.max(1, Math.min(ARCADE_TOTAL_STAGES, rawStageIndex)) as
    | 1
    | 2
    | 3
    | 4;

  const rivalId = RIVAL_PAIR[p1Id];
  const bossId = BOSS_PAIR[p1Id];
  const remaining = ALL_FIGHTERS.filter(
    (id) => id !== p1Id && id !== rivalId && id !== bossId
  );
  const stage1Opp = remaining[0] || 'tophia';
  const stage2Opp = p1Id; // Stage 2: Shadow Mirror / Elemental Challenger

  if (clamped === 1) {
    return {
      stageIndex: 1,
      title: 'STAGE 1 • ELEMENTAL VANGUARD',
      opponentId: stage1Opp,
      stageId: STAGE_BY_FIGHTER[stage1Opp],
      aiArchetype: 'zoner',
      aiTempo: 1.05,
      opponentPalette: 0,
      isBoss: false,
      rivalryBanner: RIVALRY_QUOTES[p1Id][stage1Opp],
      unlockedSkills: [FIGHTERS[stage1Opp].skillTree[0].id],
    };
  }

  if (clamped === 2) {
    const secondCandidate =
      ALL_FIGHTERS.find((id) => id !== p1Id && id !== stage1Opp && id !== rivalId) ||
      stage2Opp;
    return {
      stageIndex: 2,
      title: 'STAGE 2 • SANCTUARY GUARDIAN',
      opponentId: secondCandidate,
      stageId: STAGE_BY_FIGHTER[secondCandidate],
      aiArchetype: 'counter',
      aiTempo: 0.92,
      opponentPalette: 1,
      isBoss: false,
      rivalryBanner: RIVALRY_QUOTES[p1Id][secondCandidate],
      unlockedSkills: [
        FIGHTERS[secondCandidate].skillTree[0].id,
        FIGHTERS[secondCandidate].skillTree[2].id,
      ],
    };
  }

  if (clamped === 3) {
    return {
      stageIndex: 3,
      title: 'STAGE 3 • DESTINED RIVAL',
      opponentId: rivalId,
      stageId: STAGE_BY_FIGHTER[rivalId],
      aiArchetype: 'rushdown',
      aiTempo: 0.82,
      opponentPalette: 2,
      isBoss: false,
      rivalryBanner: RIVALRY_QUOTES[p1Id][rivalId],
      unlockedSkills: [
        FIGHTERS[rivalId].skillTree[0].id,
        FIGHTERS[rivalId].skillTree[1].id,
        FIGHTERS[rivalId].skillTree[2].id,
      ],
    };
  }

  // Stage 4: Overcharged Elemental Archon Boss!
  const bossDef = FIGHTERS[bossId];
  return {
    stageIndex: 4,
    title: `FINAL STAGE • OVERCHARGED ${bossDef.name.toUpperCase()}`,
    opponentId: bossId,
    stageId: STAGE_BY_FIGHTER[bossId],
    aiArchetype: 'rushdown',
    aiTempo: 0.72,
    opponentPalette: 3,
    isBoss: true,
    rivalryBanner: `FINAL BOSS — OVERCHARGED ${bossDef.name.toUpperCase()} AWAKENS!`,
    unlockedSkills: bossDef.skillTree.map((s) => s.id),
  };
}
