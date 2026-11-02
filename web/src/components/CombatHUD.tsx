import React from 'react';
import { COMBO_BREAKER_COOLDOWN_SECONDS } from '../game/combatEngine';
import {
  FIGHTERS,
  getEffectiveMoveData,
  getPreFightDialogue,
  STAGES,
} from '../game/fighters';
import {
  CombatSnapshot,
  GameMode,
  GameSettings,
  MoveType,
  StageId,
} from '../game/types';
import { DrawnMoveIcon } from './DrawnVisuals';

interface CombatHUDProps {
  snapshot: CombatSnapshot;
  mode: GameMode;
  stageId: StageId;
  settings: GameSettings;
  onToggleMute: () => void;
  onPause: () => void;
  onRestart: () => void;
  onTriggerMove: (move: MoveType) => void;
  onTriggerBreaker?: () => void;
}

const HUD_MOVES: Array<{ type: MoveType; keyHint: string; shortLabel: string }> = [
  { type: 'light', keyHint: 'J', shortLabel: 'PUNCH' },
  { type: 'down_punch', keyHint: 'S+J', shortLabel: 'DOWN' },
  { type: 'air_punch', keyHint: 'W+J', shortLabel: 'AIR' },
  { type: 'heavy', keyHint: 'K', shortLabel: 'HEAVY' },
  { type: 'elemental', keyHint: 'L', shortLabel: 'SKILL' },
  { type: 'ultimate', keyHint: 'U', shortLabel: 'ULT' },
];

export const CombatHUD: React.FC<CombatHUDProps> = ({
  snapshot,
  mode,
  stageId,
  settings,
  onToggleMute,
  onPause,
  onRestart,
  onTriggerMove,
  onTriggerBreaker,
}) => {
  const { p1, p2 } = snapshot;
  const f1 = FIGHTERS[p1.id];
  const f2 = FIGHTERS[p2.id];
  const stage = STAGES[stageId];

  const p1HpPct = Math.max(0, Math.min(100, (p1.hp / p1.maxHp) * 100));
  const p1TrailPct = Math.max(0, Math.min(100, (p1.trailHp / p1.maxHp) * 100));

  const p2HpPct = Math.max(0, Math.min(100, (p2.hp / p2.maxHp) * 100));
  const p2TrailPct = Math.max(0, Math.min(100, (p2.trailHp / p2.maxHp) * 100));

  const breakerReady = p1.breakerCooldown <= 0;
  const breakerPct = breakerReady
    ? 100
    : Math.round(
        ((COMBO_BREAKER_COOLDOWN_SECONDS - p1.breakerCooldown) /
          COMBO_BREAKER_COOLDOWN_SECONDS) *
          100
      );

  const countdownNum =
    snapshot.countdownTimer > 0 ? Math.ceil(snapshot.countdownTimer) : 0;
  const preFightDialogue =
    snapshot.countdownTimer > 0.35 && snapshot.currentRound === 1
      ? getPreFightDialogue(p1.id, p2.id)
      : null;

  // Item 1: Reactive HUD Shake when either fighter takes a heavy hit, wall bounce, or impact frame!
  const p1ShakeActive = p1.hitFlashTimer > 0.04;
  const p2ShakeActive = p2.hitFlashTimer > 0.04;
  const globalShakeActive =
    snapshot.impactFrameTimer > 0 || snapshot.cinematicTimer > 0.28;

  return (
    <div className="fixed inset-0 z-10 pointer-events-none flex flex-col justify-between p-4 md:p-6 select-none">
      {/* TOP PERIMETER CLUSTER: P1 Vitality | Timer & Stage | P2 Vitality + Utility Controls */}
      <div
        className={`w-full max-w-7xl mx-auto grid grid-cols-12 items-start gap-4 transition-transform duration-75 ${
          globalShakeActive ? 'scale-[1.015] -translate-y-0.5' : ''
        }`}
      >
        {/* Player 1 Vitality, Meter & Anti-Stunlock / Breaker Status (5 cols) */}
        <div
          className={`col-span-5 space-y-1.5 transition-transform duration-75 ${
            p1ShakeActive ? '-translate-x-1.5 translate-y-1' : ''
          }`}
        >
          <div className="flex items-baseline justify-between">
            <div className="flex items-center gap-2">
              <span
                className="font-display font-bold text-base md:text-lg uppercase tracking-wider text-stroke-dark"
                style={{ color: f1.primaryColor }}
              >
                {f1.name}
              </span>
              {mode !== 'training' && (
                <div className="flex items-center gap-1 ml-1" title="Round Wins (Best of 3)">
                  {[0, 1].map((orbIdx) => (
                    <span
                      key={orbIdx}
                      className={`w-3 h-3 rounded-full border border-slate-950 transition-all ${
                        snapshot.p1RoundWins > orbIdx
                          ? 'bg-amber-400 shadow-[0_0_8px_#f59e0b] scale-110'
                          : 'bg-slate-800/90'
                      }`}
                    />
                  ))}
                </div>
              )}
              {p1.stunlockImmunityTimer > 0 && (
                <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold bg-amber-400 text-slate-950">
                  ANTI-STUN ARMOR {p1.stunlockImmunityTimer.toFixed(1)}S
                </span>
              )}
            </div>
            <div className="font-mono-tabular text-sm font-bold text-white text-stroke-dark">
              {Math.round(p1.hp)} / {p1.maxHp}
            </div>
          </div>

          {/* Cel-Shaded Vitality Bar with Delayed Red Combo Damage Trail */}
          <div
            className={`h-5 w-full bg-slate-950 cel-border relative overflow-hidden ${
              p1ShakeActive ? 'ring-2 ring-rose-500' : ''
            }`}
          >
            <div
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-rose-600 via-red-500 to-amber-400 transition-all duration-100"
              style={{ width: `${p1TrailPct}%` }}
            />
            <div
              className="absolute inset-y-0 left-0 bg-emerald-500 transition-all duration-75"
              style={{ width: `${p1HpPct}%` }}
            />
            {p1.trailHp - p1.hp >= 35 && (
              <span className="absolute right-2 top-0.5 text-[10px] font-mono font-bold text-rose-200 drop-shadow">
                -{Math.round(p1.trailHp - p1.hp)} DMG
              </span>
            )}
          </div>

          {/* Elemental Super Meter + Breaker Cooldown Pill */}
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-display font-bold uppercase tracking-wider text-amber-400">
              SUPER
            </span>
            <div className="h-2.5 flex-1 bg-slate-950 border border-slate-800 relative overflow-hidden">
              <div
                className="h-full bg-amber-400 transition-all duration-75"
                style={{ width: `${Math.round(p1.meter)}%` }}
              />
            </div>
            <span className="font-mono-tabular text-xs font-bold text-amber-300">
              {Math.round(p1.meter)}%
            </span>
          </div>
        </div>

        {/* Center Round Clock & Stage Name (2 cols) */}
        <div className="col-span-2 flex flex-col items-center">
          <div className="cel-border bg-slate-950 px-4 py-1.5 text-center">
            <div className="text-[10px] font-display font-bold uppercase tracking-widest text-amber-400">
              {mode === 'training' ? 'DOJO' : `STAGE ${snapshot.arcadeStageIndex}`}
            </div>
            <div className="font-mono-tabular font-bold text-2xl md:text-3xl text-white leading-none">
              {mode === 'training' ? '99' : Math.ceil(snapshot.roundTimer)}
            </div>
          </div>
          <div className="mt-1 text-[10px] font-mono uppercase text-slate-300 text-center">
            {mode === 'training'
              ? `${stage.name.split(' ')[0]} ${stage.name.split(' ')[1]}`
              : snapshot.currentRound >= 3
              ? 'FINAL ROUND'
              : `ROUND ${snapshot.currentRound}`}
          </div>
        </div>

        {/* Player 2 Vitality & Top-Right Utility Controls (5 cols) */}
        <div
          className={`col-span-5 space-y-1.5 transition-transform duration-75 ${
            p2ShakeActive ? 'translate-x-1.5 translate-y-1' : ''
          }`}
        >
          <div className="flex items-baseline justify-between">
            <div className="font-mono-tabular text-sm font-bold text-white text-stroke-dark">
              {Math.round(p2.hp)} / {p2.maxHp}
            </div>
            <div className="flex items-center gap-2">
              {p2.isOvercharged && (
                <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold bg-rose-500 text-white animate-pulse">
                  BOSS OVERCHARGED
                </span>
              )}
              {p2.stunlockImmunityTimer > 0 && (
                <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold bg-amber-400 text-slate-950">
                  ARMOR
                </span>
              )}
              {mode !== 'training' && (
                <div className="flex items-center gap-1 mr-1" title="Round Wins (Best of 3)">
                  {[1, 0].map((orbIdx) => (
                    <span
                      key={orbIdx}
                      className={`w-3 h-3 rounded-full border border-slate-950 transition-all ${
                        snapshot.p2RoundWins > orbIdx
                          ? 'bg-amber-400 shadow-[0_0_8px_#f59e0b] scale-110'
                          : 'bg-slate-800/90'
                      }`}
                    />
                  ))}
                </div>
              )}
              <span
                className="font-display font-bold text-base md:text-lg uppercase tracking-wider text-stroke-dark"
                style={{ color: f2.primaryColor }}
              >
                {f2.name}
              </span>
            </div>
          </div>

          <div
            className={`h-5 w-full bg-slate-950 cel-border relative overflow-hidden ${
              p2ShakeActive ? 'ring-2 ring-amber-400' : ''
            }`}
          >
            <div
              className="absolute inset-y-0 right-0 bg-gradient-to-l from-rose-600 via-orange-500 to-amber-300 transition-all duration-100"
              style={{ width: `${p2TrailPct}%` }}
            />
            <div
              className="absolute inset-y-0 right-0 bg-rose-500 transition-all duration-75"
              style={{ width: `${p2HpPct}%` }}
            />
            {p2.trailHp - p2.hp >= 35 && (
              <span className="absolute left-2 top-0.5 text-[10px] font-mono font-bold text-amber-200 drop-shadow">
                -{Math.round(p2.trailHp - p2.hp)} DMG
              </span>
            )}
          </div>

          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 flex-1">
              <span className="font-mono-tabular text-xs font-bold text-cyan-300">
                {Math.round(p2.meter)}%
              </span>
              <div className="h-2.5 flex-1 bg-slate-950 border border-slate-800 relative overflow-hidden">
                <div
                  className="h-full bg-cyan-400 ml-auto transition-all duration-75"
                  style={{ width: `${Math.round(p2.meter)}%` }}
                />
              </div>
            </div>

            {/* Compact Square SVG Utility Buttons (Mute [M], Restart [R], Pause [P]) */}
            <div className="flex items-center gap-1.5 pointer-events-auto">
              <button
                type="button"
                tabIndex={-1}
                aria-label={settings.muted ? 'Unmute Audio (M)' : 'Mute Audio (M)'}
                onClick={(e) => {
                  e.currentTarget.blur();
                  onToggleMute();
                }}
                className="cel-border bg-slate-900 hover:bg-slate-800 text-slate-100 w-8 h-8 flex items-center justify-center cursor-pointer"
              >
                <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
                  {settings.muted ? (
                    <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" />
                  ) : (
                    <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
                  )}
                </svg>
              </button>
              <button
                type="button"
                tabIndex={-1}
                aria-label="Restart Match (R)"
                onClick={(e) => {
                  e.currentTarget.blur();
                  onRestart();
                }}
                className="cel-border bg-slate-900 hover:bg-slate-800 text-slate-100 w-8 h-8 flex items-center justify-center cursor-pointer"
              >
                <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
                  <path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" />
                </svg>
              </button>
              <button
                type="button"
                tabIndex={-1}
                aria-label="Pause Game (Escape or P)"
                onClick={(e) => {
                  e.currentTarget.blur();
                  onPause();
                }}
                className="cel-border bg-slate-900 hover:bg-slate-800 text-slate-100 w-8 h-8 flex items-center justify-center cursor-pointer"
              >
                <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
                  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* CENTER CALLOUTS: VISUAL ATTACK TAGS, 3-2-1-FIGHT COUNTDOWN, AIR DRIBBLE, & COMBO COUNTER */}
      <div className="my-auto flex flex-col items-center justify-center relative">
        {/* Clear Visual Attack & Directional Block Indicator Badges for P1 & P2 in Signature Colors */}
        {countdownNum === 0 && (
          <div className="w-full max-w-5xl mx-auto flex items-center justify-between px-4 mb-4 pointer-events-none">
            <div className="min-h-[44px] flex items-center">
              {p1.attackVisualTimer > 0 && p1.attackVisualTag && (
                <div
                  className={`cel-border px-4 py-1.5 bg-slate-950/95 flex items-center gap-2 shadow-lg ${
                    p1.attackVisualTag === 'COUNTER HIT!' || p1.attackVisualTag === 'PUNISH!'
                      ? 'scale-110 ring-2 ring-amber-400'
                      : ''
                  }`}
                  style={{
                    borderColor:
                      p1.attackVisualTag === 'COUNTER HIT!'
                        ? '#f43f5e'
                        : p1.attackVisualTag === 'PUNISH!'
                        ? '#38bdf8'
                        : f1.primaryColor,
                  }}
                >
                  <span
                    className="w-2.5 h-2.5 inline-block"
                    style={{
                      backgroundColor:
                        p1.attackVisualTag === 'COUNTER HIT!'
                          ? '#f43f5e'
                          : p1.attackVisualTag === 'PUNISH!'
                          ? '#38bdf8'
                          : f1.primaryColor,
                    }}
                  />
                  <span
                    className="font-display font-bold text-sm md:text-base uppercase tracking-wider text-stroke-dark"
                    style={{
                      color:
                        p1.attackVisualTag === 'COUNTER HIT!'
                          ? '#fda4af'
                          : p1.attackVisualTag === 'PUNISH!'
                          ? '#7dd3fc'
                          : f1.primaryColor,
                    }}
                  >
                    {p1.attackVisualTag}
                  </span>
                </div>
              )}
            </div>

            <div className="min-h-[44px] flex items-center">
              {p2.attackVisualTimer > 0 && p2.attackVisualTag && (
                <div
                  className="cel-border px-4 py-1.5 bg-slate-950/95 flex items-center gap-2 shadow-lg"
                  style={{ borderColor: f2.primaryColor }}
                >
                  <span
                    className="font-display font-bold text-sm md:text-base uppercase tracking-wider text-stroke-dark"
                    style={{ color: f2.primaryColor }}
                  >
                    {p2.attackVisualTag}
                  </span>
                  <span
                    className="w-2.5 h-2.5 inline-block"
                    style={{ backgroundColor: f2.primaryColor }}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Dramatic 3 - 2 - 1 - FIGHT! Pre-Match Countdown & Pre-Fight Rivalry Dialogue */}
        {countdownNum > 0 && (
          <div className="flex flex-col items-center gap-3">
            <div className="cel-panel bg-slate-950/90 px-10 py-6 border-4 border-amber-400 text-center">
              <div className="text-xs font-mono uppercase tracking-widest text-emerald-400 mb-1">
                {snapshot.currentRound >= 3
                  ? 'FINAL ROUND'
                  : `ROUND ${snapshot.currentRound} • ${stage.name}`}
              </div>
              <div className="font-display font-bold text-7xl md:text-8xl italic text-amber-400 text-stroke-dark leading-none">
                {countdownNum}
              </div>
            </div>

            {preFightDialogue && (
              <div className="w-full max-w-3xl grid grid-cols-1 md:grid-cols-2 gap-3 px-4">
                <div
                  className="cel-border bg-slate-950/95 px-4 py-2.5 border-l-4 text-left"
                  style={{ borderLeftColor: f1.primaryColor }}
                >
                  <div
                    className="font-display font-bold text-xs uppercase tracking-wider"
                    style={{ color: f1.primaryColor }}
                  >
                    {f1.name}
                  </div>
                  <div className="text-xs md:text-sm font-medium text-slate-100 italic mt-0.5">
                    “{preFightDialogue.p1Line}”
                  </div>
                </div>
                <div
                  className="cel-border bg-slate-950/95 px-4 py-2.5 border-r-4 text-right"
                  style={{ borderRightColor: f2.primaryColor }}
                >
                  <div
                    className="font-display font-bold text-xs uppercase tracking-wider"
                    style={{ color: f2.primaryColor }}
                  >
                    {f2.name}
                  </div>
                  <div className="text-xs md:text-sm font-medium text-slate-100 italic mt-0.5">
                    “{preFightDialogue.p2Line}”
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Live Combo & Air Dribble Counter */}
        {p1.comboCount >= 2 && (
          <div className="fixed left-8 top-1/3 pointer-events-none">
            <div
              className="font-mono-tabular font-bold text-5xl italic text-stroke-dark"
              style={{ color: f1.primaryColor }}
            >
              {p1.comboCount} HITS
            </div>
            {p1.airDribbleCount > 0 && (
              <div className="font-display font-bold text-lg uppercase tracking-wider text-emerald-300 text-stroke-dark">
                AIR DRIBBLE x{p1.airDribbleCount}! (GRAVITY {p2.juggleGravityScale.toFixed(2)}x)
              </div>
            )}
            <div className="font-display font-bold text-xs uppercase tracking-widest text-white text-stroke-dark">
              {p1.comboDamage} DMG
            </div>
          </div>
        )}

        {/* Dynamic Event Callout Banner */}
        {countdownNum === 0 && snapshot.bannerTimer > 0 && snapshot.lastEventBanner && (
          <div className="mt-2 cel-border-accent bg-slate-950/95 px-6 py-2">
            <span className="font-display font-bold text-xl md:text-2xl uppercase tracking-wider text-amber-400">
              {snapshot.lastEventBanner}
            </span>
          </div>
        )}
      </div>

      {/* BOTTOM PERIMETER CLUSTER: Visual Drawn Icon Move Bar + Combo Breaker Slot */}
      <div className="w-full max-w-7xl mx-auto flex flex-col lg:flex-row items-end justify-between gap-3">
        {/* 6 Drawn Attack Icon Buttons + Combo Breaker Slot */}
        <div className="flex flex-wrap items-center gap-2 pointer-events-auto">
          {HUD_MOVES.map(({ type, keyHint, shortLabel }) => {
            const m = getEffectiveMoveData(p1.id, type, p1.unlockedSkills);
            const canUse = p1.meter >= m.meterCost;
            return (
              <button
                key={m.id}
                type="button"
                tabIndex={-1}
                onClick={(e) => {
                  e.currentTarget.blur();
                  onTriggerMove(type);
                }}
                className={`p-1.5 flex items-center gap-2 transition-transform active:translate-y-0.5 cursor-pointer ${
                  canUse
                    ? 'cel-border bg-slate-950/95 hover:bg-slate-900 text-slate-100'
                    : 'cel-border bg-slate-950/60 text-slate-500 opacity-60'
                }`}
              >
                <DrawnMoveIcon moveType={type} element={f1.element} size={36} />
                <div className="text-left pr-1">
                  <div className="flex items-center gap-1.5">
                    <span className="font-display font-bold text-xs uppercase tracking-wide text-white">
                      {shortLabel}
                    </span>
                    <span className="font-mono text-[10px] font-bold bg-slate-800 text-amber-300 px-1 py-0.5">
                      [{keyHint}]
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-emerald-400">
                    {m.startupFrames}F • {m.damage}
                  </div>
                </div>
              </button>
            );
          })}

          {/* Combo Breaker Visual Drawn Icon Slot with 6s Cooldown Bar */}
          <button
            type="button"
            tabIndex={-1}
            onClick={(e) => {
              e.currentTarget.blur();
              onTriggerBreaker?.();
            }}
            className={`p-1.5 flex items-center gap-2 transition-transform active:translate-y-0.5 cursor-pointer relative overflow-hidden ${
              breakerReady
                ? 'cel-border-accent bg-slate-950/95 hover:bg-slate-900 text-white'
                : 'cel-border bg-slate-950/70 text-slate-400'
            }`}
          >
            <DrawnMoveIcon moveType="breaker" element={f1.element} size={36} />
            <div className="text-left pr-1">
              <div className="flex items-center gap-1.5">
                <span className="font-display font-bold text-xs uppercase tracking-wide text-amber-300">
                  BREAKER
                </span>
                <span className="font-mono text-[10px] font-bold bg-slate-800 text-white px-1 py-0.5">
                  [B]
                </span>
              </div>
              <div className="text-[10px] font-mono">
                {breakerReady ? (
                  <span className="text-emerald-400 font-bold">READY</span>
                ) : (
                  <span className="text-rose-400">{p1.breakerCooldown.toFixed(1)}S CD</span>
                )}
              </div>
              <div className="w-full h-1 bg-slate-800 mt-0.5">
                <div
                  className="h-full bg-amber-400"
                  style={{ width: `${breakerPct}%` }}
                />
              </div>
            </div>
          </button>
        </div>

        {/* Compact Frame Advantage / Punch Chain / Directional Guard Badge */}
        <div className="cel-border bg-slate-950/95 px-3 py-2 text-xs font-mono-tabular flex flex-wrap items-center gap-3">
          <span>
            PUNCH:{' '}
            <strong style={{ color: f1.primaryColor }}>
              {p1.punchChainStep === 1
                ? '1:JAB'
                : p1.punchChainStep === 2
                ? '2:CROSS'
                : '3:FINISHER'}
            </strong>
          </span>
          <span>
            STATE: <strong className="text-white uppercase">{p1.action}</strong>
          </span>
          <span>
            ADV:{' '}
            <strong
              className={
                p1.lastFrameAdvantage >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }
            >
              {p1.lastFrameAdvantage >= 0
                ? `+${p1.lastFrameAdvantage}F`
                : `${p1.lastFrameAdvantage}F`}
            </strong>
          </span>
          <span>
            GRAV:{' '}
            <strong className="text-amber-300">
              {p2.juggleGravityScale.toFixed(1)}x
            </strong>
          </span>
        </div>
      </div>
    </div>
  );
};
