import React from 'react';
import { ARCADE_TOTAL_STAGES, getArcadeStageSpec } from '../game/arcadeTower';
import { FIGHTERS, getEffectiveMoveData } from '../game/fighters';
import { CombatSnapshot, GameMode, MoveType } from '../game/types';
import { DrawnMoveIcon } from './DrawnVisuals';

interface PauseAndOutcomeModalProps {
  kind: 'paused' | 'gameover';
  snapshot: CombatSnapshot;
  mode: GameMode;
  onResume: () => void;
  onRestart: () => void;
  onNextStage: () => void;
  onOpenSettings: () => void;
  onReturnSelect?: () => void;
  onReturnTitle: () => void;
}

const COMMAND_LIST_MOVES: Array<{ type: MoveType; keyInput: string }> = [
  { type: 'light', keyInput: '[J] x3' },
  { type: 'down_punch', keyInput: '[S + J]' },
  { type: 'air_punch', keyInput: '[W + J]' },
  { type: 'heavy', keyInput: '[K]' },
  { type: 'elemental', keyInput: '[L]' },
  { type: 'ultimate', keyInput: '[U] (50%)' },
];

export const PauseAndOutcomeModal: React.FC<PauseAndOutcomeModalProps> = ({
  kind,
  snapshot,
  mode,
  onResume,
  onRestart,
  onNextStage,
  onOpenSettings,
  onReturnSelect,
  onReturnTitle,
}) => {
  const f1 = FIGHTERS[snapshot.p1.id];
  const f2 = FIGHTERS[snapshot.p2.id];
  const isVictory = snapshot.winner === 1;
  const clearTimeSec = Math.max(1, Math.round(99 - snapshot.roundTimer));

  if (kind === 'paused') {
    return (
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Match Paused"
        className="fixed inset-0 z-30 flex items-center justify-center p-4 bg-slate-950/88 pointer-events-auto"
      >
        <div className="cel-border bg-slate-900 text-slate-100 w-full max-w-3xl p-5 md:p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-display font-bold text-2xl uppercase tracking-wider text-white">
                  Match Paused — Command List
                </h2>
                <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-emerald-950 border border-emerald-500/40 text-emerald-300">
                  {f1.martialStyle}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {f1.name} Complete Move List, Guard Heights & Tactical Mechanics
              </p>
            </div>
            <span className="font-mono-tabular text-xs text-amber-400 uppercase">
              {mode} Mode
            </span>
          </div>

          {/* Item 18: Interactive 6-Move Command List with Color-Coded Frame Data & Guard Heights */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {COMMAND_LIST_MOVES.map(({ type, keyInput }) => {
              const m = getEffectiveMoveData(
                snapshot.p1.id,
                type,
                snapshot.p1.unlockedSkills
              );
              const heightBadge =
                m.hitHeight === 'low'
                  ? { label: 'LOW ▲ (Crouch Guard)', cls: 'bg-rose-950 text-rose-300 border-rose-500/50' }
                  : m.hitHeight === 'overhead'
                  ? { label: 'OVERHEAD ▼ (Stand Guard)', cls: 'bg-amber-950 text-amber-300 border-amber-500/50' }
                  : { label: 'MID (Any Guard)', cls: 'bg-slate-800 text-slate-300 border-slate-700' };

              const speedColor =
                m.startupFrames <= 5
                  ? 'text-emerald-400'
                  : m.startupFrames <= 9
                  ? 'text-amber-300'
                  : 'text-orange-400';

              return (
                <div
                  key={m.id}
                  className="cel-border bg-slate-950 p-2.5 flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <DrawnMoveIcon moveType={type} element={f1.element} size={34} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-display font-bold text-xs uppercase text-white">
                          {m.name}
                        </span>
                        <span className="font-mono text-[10px] font-bold bg-slate-800 text-amber-300 px-1.5 py-0.5">
                          {keyInput}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 mt-1">
                        <span
                          className={`text-[9px] font-mono uppercase px-1.5 py-0.5 border ${heightBadge.cls}`}
                        >
                          {heightBadge.label}
                        </span>
                        {m.armorHits && (
                          <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 bg-yellow-950 text-yellow-300 border border-yellow-500/50">
                            ARMOR 🛡️
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right font-mono-tabular text-xs shrink-0">
                    <div className={`font-bold ${speedColor}`}>
                      {m.startupFrames}f Start
                    </div>
                    <div className="text-slate-300">{m.damage} Dmg</div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Tactical Defense & Counter Mechanics Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px] font-mono bg-slate-950/90 border border-slate-800 p-2.5">
            <div>
              <span className="text-sky-400 font-bold block">JUST PARRY [SHIFT/I]</span>
              <span className="text-slate-400">Tap on impact for +22% Meter & +10f</span>
            </div>
            <div>
              <span className="text-rose-400 font-bold block">COUNTER HIT!</span>
              <span className="text-slate-400">Strike foe in Startup for +20% Dmg & +5f</span>
            </div>
            <div>
              <span className="text-cyan-300 font-bold block">WHIFF PUNISH!</span>
              <span className="text-slate-400">Hit a missed strike for +18% Bonus Meter</span>
            </div>
            <div>
              <span className="text-amber-300 font-bold block">BREAKER [B]</span>
              <span className="text-slate-400">Escape combos cleanly (6s cooldown)</span>
            </div>
          </div>

          {/* Pause Action Buttons (including Direct Character Select Shortcut!) */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-1">
            <button
              type="button"
              onClick={onResume}
              className="cel-border-accent bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-display font-bold text-xs uppercase py-2.5 px-3 cursor-pointer whitespace-nowrap"
            >
              Resume
            </button>
            <button
              type="button"
              onClick={onRestart}
              className="cel-border bg-slate-800 hover:bg-slate-700 text-white font-display font-bold text-xs uppercase py-2.5 px-3 cursor-pointer whitespace-nowrap"
            >
              Rematch
            </button>
            {onReturnSelect && (
              <button
                type="button"
                onClick={onReturnSelect}
                className="cel-border bg-slate-800 hover:bg-slate-700 text-amber-300 font-display font-bold text-xs uppercase py-2.5 px-3 cursor-pointer whitespace-nowrap"
              >
                Fighter Select
              </button>
            )}
            <button
              type="button"
              onClick={onOpenSettings}
              className="cel-border bg-slate-800 hover:bg-slate-700 text-white font-display font-bold text-xs uppercase py-2.5 px-3 cursor-pointer whitespace-nowrap"
            >
              Options
            </button>
            <button
              type="button"
              onClick={onReturnTitle}
              className="cel-border bg-slate-950 hover:bg-slate-800 text-slate-300 font-display font-bold text-xs uppercase py-2.5 px-3 cursor-pointer whitespace-nowrap"
            >
              Main Menu
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Item 10: Post-Match Podium Layout — Align Result Card to the Right so the 3D Winner Pose shines on the Left!
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={isVictory ? 'Victory' : 'Defeat'}
      className="fixed inset-0 z-30 flex items-center justify-end p-6 md:p-12 pointer-events-auto"
      style={{
        background:
          'linear-gradient(270deg, rgba(9,11,16,0.94) 0%, rgba(9,11,16,0.72) 48%, rgba(9,11,16,0.08) 100%)',
      }}
    >
      <div className="cel-border bg-slate-900/95 text-slate-100 w-full max-w-lg p-6 space-y-6">
        <div className="text-left space-y-1 border-b border-slate-800 pb-3">
          <div className="text-xs font-mono uppercase tracking-widest text-amber-400">
            {mode === 'arcade'
              ? `${getArcadeStageSpec(snapshot.p1.id, snapshot.arcadeStageIndex).title} (${snapshot.arcadeStageIndex}/${ARCADE_TOTAL_STAGES})`
              : 'Arena Clash Result'}
          </div>
          <h2
            className={`font-display font-bold text-4xl uppercase tracking-wider ${
              isVictory ? 'text-emerald-400' : 'text-rose-500'
            }`}
          >
            {isVictory
              ? mode === 'arcade' && snapshot.arcadeStageIndex >= ARCADE_TOTAL_STAGES
                ? 'Grand Champion — Tower Cleared!'
                : 'Victory — K.O.!'
              : 'Defeat — Down!'}
          </h2>
          <p className="text-xs text-slate-300">
            {isVictory
              ? `${f1.name} overwhelmed ${f2.name}${snapshot.isBossFight ? ' (Overcharged Sovereign)' : ''} in ${clearTimeSec} seconds!`
              : `${f2.name} claimed the arena. Watch for Overhead/Low telegraphs and punish whiffs!`}
          </p>
        </div>

        {/* 3 Tabular Mastery / Progress Metric Tiles */}
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="cel-border bg-slate-950 p-3">
            <div className="text-[10px] font-display font-bold uppercase text-slate-400">
              Max Combo
            </div>
            <div className="font-mono-tabular font-bold text-2xl text-amber-400 mt-0.5">
              {snapshot.maxComboReached} Hits
            </div>
          </div>
          <div className="cel-border bg-slate-950 p-3">
            <div className="text-[10px] font-display font-bold uppercase text-slate-400">
              Props Shattered
            </div>
            <div className="font-mono-tabular font-bold text-2xl text-emerald-400 mt-0.5">
              {snapshot.totalPropsBroken}
            </div>
          </div>
          <div className="cel-border bg-slate-950 p-3">
            <div className="text-[10px] font-display font-bold uppercase text-slate-400">
              {isVictory ? 'Clear Time' : 'Rival HP Left'}
            </div>
            <div className="font-mono-tabular font-bold text-2xl text-white mt-0.5">
              {isVictory ? `${clearTimeSec}s` : `${Math.round(snapshot.p2.hp)}`}
            </div>
          </div>
        </div>

        {/* Primary Action CTAs */}
        <div className="flex flex-wrap items-center justify-end gap-2.5">
          {isVictory &&
          mode === 'arcade' &&
          snapshot.arcadeStageIndex < ARCADE_TOTAL_STAGES ? (
            <button
              type="button"
              data-start="true"
              onClick={onNextStage}
              className="cel-border-accent bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-display font-bold text-sm uppercase px-6 py-3 cursor-pointer whitespace-nowrap"
            >
              {snapshot.arcadeStageIndex + 1 === ARCADE_TOTAL_STAGES
                ? 'Challenge Final Boss (Stage 4)'
                : `Next Challenger (Stage ${snapshot.arcadeStageIndex + 1})`}
            </button>
          ) : (
            <button
              type="button"
              data-start="true"
              onClick={onRestart}
              className="cel-border-accent bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-display font-bold text-sm uppercase px-6 py-3 cursor-pointer whitespace-nowrap"
            >
              {isVictory ? 'Play Again' : 'Try Again'}
            </button>
          )}
          {onReturnSelect && (
            <button
              type="button"
              onClick={onReturnSelect}
              className="cel-border bg-slate-800 hover:bg-slate-700 text-amber-300 font-display font-bold text-sm uppercase px-4 py-3 cursor-pointer whitespace-nowrap"
            >
              Fighter Select
            </button>
          )}
          <button
            type="button"
            onClick={onReturnTitle}
            className="cel-border bg-slate-800 hover:bg-slate-700 text-slate-200 font-display font-bold text-sm uppercase px-4 py-3 cursor-pointer whitespace-nowrap"
          >
            Main Menu
          </button>
        </div>
      </div>
    </div>
  );
};
