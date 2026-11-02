import React from 'react';
import { ARCADE_TOTAL_STAGES, getArcadeStageSpec } from '../game/arcadeTower';
import { COMBAT_TIPS, FIGHTERS, STAGES } from '../game/fighters';
import { FighterId, GameMode, StageId } from '../game/types';
import { DrawnMoveIcon } from './DrawnVisuals';

interface LoadingScreenProps {
  p1Fighter: FighterId;
  p2Fighter: FighterId;
  stageId: StageId;
  tipIndex: number;
  mode?: GameMode;
  arcadeStageIndex?: number;
}

const RIVAL_TACTICAL_TIPS: Record<FighterId, string> = {
  kaze: 'TACTICAL NOTE: Kaze uses long-range Wind Waves and fast Low Launchers — block low at mid-range and punish whiffs!',
  ignis: 'TACTICAL NOTE: Ignis has Super Armor on her Heavy Overhead [K] — stand-block her overhead or sweep her legs with [S+J]!',
  tophia: 'TACTICAL NOTE: Tophia controls space with extended Hung Gar palms & stone pillars — dash-cancel inside her guard!',
  volt: 'TACTICAL NOTE: Volt dashes fast with acrobatic Taekwondo kicks — hold guard through his 3-hit chain, then punish his recovery!',
};

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
  p1Fighter,
  p2Fighter,
  stageId,
  tipIndex,
  mode = 'arcade',
  arcadeStageIndex = 1,
}) => {
  const f1 = FIGHTERS[p1Fighter];
  const f2 = FIGHTERS[p2Fighter];
  const stage = STAGES[stageId];
  const tip =
    mode === 'arcade'
      ? RIVAL_TACTICAL_TIPS[p2Fighter]
      : COMBAT_TIPS[tipIndex % COMBAT_TIPS.length];

  const towerSpecs = [4, 3, 2, 1].map((idx) =>
    getArcadeStageSpec(p1Fighter, idx)
  );

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-0 z-40 bg-slate-950/92 text-slate-100 flex flex-col justify-between p-6 md:p-10 select-none"
    >
      {/* Top Minimalist Matchup Header */}
      <div className="flex items-center justify-between text-xs font-mono uppercase tracking-widest text-slate-400">
        <span>
          {mode === 'arcade'
            ? `ARCADE ELEMENTAL TOWER • STAGE ${arcadeStageIndex} OF ${ARCADE_TOTAL_STAGES}`
            : stage.name}
        </span>
        <span>60Hz Frame-Lock Simulation Ready</span>
      </div>

      {/* Center: Item 3 Visual 4-Floor Arcade Tower Progression OR Versus Crest */}
      <div className="my-auto w-full max-w-4xl mx-auto flex flex-col items-center justify-center gap-5">
        <div className="text-center space-y-1">
          <div className="text-xs font-mono uppercase tracking-widest text-amber-400">
            {stage.name}
          </div>
          <div className="font-display font-bold text-3xl md:text-4xl uppercase tracking-wider text-white">
            <span style={{ color: f1.primaryColor }}>{f1.name}</span>
            <span className="text-amber-400 px-3">VS</span>
            <span style={{ color: f2.primaryColor }}>{f2.name}</span>
          </div>
        </div>

        {mode === 'arcade' && (
          <div className="w-full max-w-2xl space-y-2">
            {towerSpecs.map((spec) => {
              const opp = FIGHTERS[spec.opponentId];
              const stg = STAGES[spec.stageId];
              const isCurrent = spec.stageIndex === arcadeStageIndex;
              const isCleared = spec.stageIndex < arcadeStageIndex;
              return (
                <div
                  key={spec.stageIndex}
                  className={`cel-border px-4 py-2.5 flex items-center justify-between transition-all ${
                    isCurrent
                      ? 'bg-slate-900 ring-2 ring-amber-400 scale-[1.02]'
                      : isCleared
                      ? 'bg-slate-950/75 opacity-60'
                      : 'bg-slate-950/85 opacity-80'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`font-mono font-bold text-xs px-2 py-1 ${
                        spec.isBoss
                          ? 'bg-rose-600 text-white'
                          : isCurrent
                          ? 'bg-amber-400 text-slate-950'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {spec.isBoss ? 'FINAL BOSS' : `FLOOR ${spec.stageIndex}`}
                    </span>
                    <DrawnMoveIcon
                      moveType={spec.isBoss ? 'ultimate' : 'elemental'}
                      element={opp.element}
                      size={32}
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-display font-bold text-base uppercase tracking-wider text-white">
                          {opp.name}
                        </span>
                        <span className="text-[10px] font-mono uppercase text-slate-400">
                          • {stg.name.split(' ')[0]} {stg.name.split(' ')[1]}
                        </span>
                      </div>
                      <div className="text-[11px] font-mono text-amber-300/90">
                        {spec.rivalryBanner}
                      </div>
                    </div>
                  </div>

                  <div className="font-mono text-xs font-bold uppercase">
                    {isCleared ? (
                      <span className="text-emerald-400 bg-emerald-950/80 border border-emerald-500/50 px-2 py-0.5">
                        DEFEATED ✓
                      </span>
                    ) : isCurrent ? (
                      <span className="text-amber-300 animate-pulse">
                        ▶ NEXT CLASH
                      </span>
                    ) : (
                      <span className="text-slate-500">LOCKED</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Bottom Tactical Counter-Tip Bar */}
      <div className="border-t border-slate-800/80 pt-4 flex items-center justify-between gap-4">
        <p className="text-xs md:text-sm text-amber-200 font-mono">{tip}</p>
        <span className="text-xs font-mono text-emerald-400 uppercase tracking-wider shrink-0">
          Entering Sanctuary...
        </span>
      </div>
    </div>
  );
};
