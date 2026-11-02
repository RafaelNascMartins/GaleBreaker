// Run from web/: npm run sync-godot-data
import { writeFileSync } from 'node:fs';
import { FIGHTERS, STAGES, FIGHTER_PALETTES } from '../../web/src/game/fighters';
import { getArcadeStageSpec } from '../../web/src/game/arcadeTower';
import type { FighterId } from '../../web/src/game/types';

const arcade = Object.fromEntries((Object.keys(FIGHTERS) as FighterId[]).map(id =>
  [id, [1, 2, 3, 4].map(index => getArcadeStageSpec(id, index))]));
writeFileSync(new URL('../data/game_data.json', import.meta.url),
  JSON.stringify({ fighters: FIGHTERS, stages: STAGES, palettes: FIGHTER_PALETTES, arcade }, null, 2));
console.log('Godot: fighter, stage, palette and arcade data synchronized.');
