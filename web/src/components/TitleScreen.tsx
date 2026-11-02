import React from 'react';
import { FIGHTERS, STAGES } from '../game/fighters';
import { FighterId, GameMode, StageId } from '../game/types';
import { DrawnMoveIcon, StagePreviewCardArt } from './DrawnVisuals';

interface TitleScreenProps {
  selectedMode: GameMode;
  onSelectMode: (mode: GameMode) => void;
  p1Fighter: FighterId;
  p2Fighter: FighterId;
  selectedStage: StageId;
  onSelectStage: (stage: StageId) => void;
  onStartMatch: () => void;
  onOpenRosterSkills: () => void;
  onOpenSettings: () => void;
}

export const TitleScreen: React.FC<TitleScreenProps> = ({
  selectedMode,
  onSelectMode,
  p1Fighter,
  p2Fighter,
  selectedStage,
  onSelectStage,
  onStartMatch,
  onOpenRosterSkills,
  onOpenSettings,
}) => {
  const f1 = FIGHTERS[p1Fighter];
  const f2 = FIGHTERS[p2Fighter];
  const stage = STAGES[selectedStage];

  return (
    <div
      className="fixed inset-0 z-10 flex flex-col justify-between p-6 md:p-10 pointer-events-none select-none"
      style={{
        background:
          'linear-gradient(90deg, rgba(9,11,16,0.92) 0%, rgba(9,11,16,0.62) 40%, rgba(9,11,16,0.0) 75%)',
      }}
    >
      {/* Top Bar: Visual Fighter Matchup + Skill Tree & Options */}
      <div className="flex flex-wrap items-center justify-between gap-4 pointer-events-auto">
        <div className="flex items-center gap-2.5 cel-panel bg-slate-950/90 px-3.5 py-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-[10px] font-mono uppercase tracking-widest text-emerald-400">
            LIVE 3D SHOWCASE
          </span>
          <span className="text-slate-600">•</span>
          <DrawnMoveIcon moveType="light" element={f1.element} size={24} />
          <span className="font-display font-bold uppercase tracking-wider text-emerald-400">
            {f1.name.split(' ')[0]}
          </span>
          <span className="text-xs font-mono text-slate-400">VS</span>
          <DrawnMoveIcon moveType="heavy" element={f2.element} size={24} />
          <span className="font-display font-bold uppercase tracking-wider text-amber-400">
            {f2.name.split(' ')[0]}
          </span>
          <span className="text-slate-600">•</span>
          <span className="text-xs font-mono uppercase text-sky-300">{stage.name}</span>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onOpenRosterSkills}
            className="cel-border bg-slate-900 hover:bg-slate-800 text-amber-300 px-3.5 py-1.5 text-xs font-display font-bold uppercase tracking-wider transition-transform active:translate-y-0.5 cursor-pointer flex items-center gap-2"
          >
            <DrawnMoveIcon moveType="elemental" element={f1.element} size={22} />
            <span>Visual Skill Tree</span>
          </button>
          <button
            type="button"
            onClick={onOpenSettings}
            className="cel-border bg-slate-900 hover:bg-slate-800 text-slate-100 px-4 py-2 text-xs font-display font-bold uppercase tracking-wider transition-transform active:translate-y-0.5 cursor-pointer"
          >
            Options & Controls
          </button>
        </div>
      </div>

      {/* Left-Third Asymmetric Hero Lockup & Visual Mode/Stage Cards */}
      <div className="max-w-lg my-auto pointer-events-auto space-y-5">
        {/* Bespoke Inline SVG Title Emblem */}
        <div>
          <svg
            viewBox="0 0 540 120"
            className="w-full max-w-[460px] h-auto overflow-visible"
            role="img"
            aria-label="Gale Breaker: Elemental Clash"
          >
            <polygon
              points="10,14 518,6 502,104 4,112"
              fill="#0f172a"
              stroke="#090b10"
              strokeWidth="6"
            />
            <polygon
              points="18,20 508,12 494,94 12,102"
              fill="#1e293b"
              stroke="#f59e0b"
              strokeWidth="3"
            />
            <path
              d="M36 64 C48 30, 82 24, 96 42 C76 44, 66 58, 74 74 C54 74, 42 70, 36 64 Z"
              fill="#10b981"
              stroke="#090b10"
              strokeWidth="3"
            />
            <path
              d="M52 80 C68 54, 94 52, 106 68 C88 70, 78 82, 62 88 Z"
              fill="#f59e0b"
              stroke="#090b10"
              strokeWidth="3"
            />
            <text
              x="114"
              y="62"
              fill="#f8fafc"
              stroke="#090b10"
              strokeWidth="7"
              paintOrder="stroke fill"
              fontFamily="Chakra Petch, sans-serif"
              fontWeight="700"
              fontStyle="italic"
              fontSize="48"
              letterSpacing="2"
            >
              GALE BREAKER
            </text>
            <text
              x="116"
              y="90"
              fill="#f59e0b"
              stroke="#090b10"
              strokeWidth="5"
              paintOrder="stroke fill"
              fontFamily="Chakra Petch, sans-serif"
              fontWeight="700"
              fontSize="19"
              letterSpacing="5"
            >
              2.5D ELEMENTAL CLASH
            </text>
          </svg>
        </div>

        {/* Visual Combat Mode Selector Cards */}
        <div
          role="radiogroup"
          aria-label="Combat Mode"
          className="grid grid-cols-3 gap-2.5"
        >
          {(
            [
              {
                id: 'arcade',
                label: 'ARCADE',
                sub: 'Courtyard Lineup',
                move: 'ultimate' as const,
              },
              {
                id: 'training',
                label: 'TRAINING',
                sub: '2D Hitboxes',
                move: 'down_punch' as const,
              },
              {
                id: 'versus',
                label: '2P VERSUS',
                sub: 'Local Clash',
                move: 'air_punch' as const,
              },
            ] as const
          ).map((m) => {
            const active = selectedMode === m.id;
            return (
              <button
                key={m.id}
                type="button"
                role="radio"
                aria-checked={active}
                onClick={() => onSelectMode(m.id)}
                className={`p-2.5 flex items-center gap-2.5 transition-transform active:translate-y-0.5 cursor-pointer ${
                  active
                    ? 'cel-border-accent bg-slate-800 text-white'
                    : 'cel-border bg-slate-900/90 text-slate-300 hover:bg-slate-800/80'
                }`}
              >
                <DrawnMoveIcon moveType={m.move} element={f1.element} size={34} />
                <div className="text-left">
                  <div className="font-display font-bold text-sm uppercase tracking-wide leading-none">
                    {m.label}
                  </div>
                  <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                    {m.sub}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* 3 Visual Illustrated Stage Cards (Sanctuary / Crimson Anvil / Arabic Bazaar) */}
        <div className="grid grid-cols-3 gap-2.5">
          {(Object.keys(STAGES) as StageId[]).map((sId) => {
            const s = STAGES[sId];
            const active = selectedStage === sId;
            return (
              <button
                key={sId}
                type="button"
                onClick={() => onSelectStage(sId)}
                className={`relative h-20 overflow-hidden cursor-pointer transition-transform ${
                  active
                    ? 'cel-border-accent -translate-y-1'
                    : 'cel-border opacity-75 hover:opacity-100'
                }`}
              >
                <StagePreviewCardArt stageId={sId} className="w-full h-full" />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-transparent to-transparent flex items-end p-2">
                  <span className="font-display font-bold text-xs uppercase tracking-wider text-white leading-none">
                    {s.name.split(' ')[0]} {s.name.split(' ')[1]}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Primary Start Action */}
        <div className="pt-1 flex items-center gap-4">
          <button
            type="button"
            data-start="true"
            onClick={onStartMatch}
            className="cel-border-accent bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-display font-bold text-xl uppercase tracking-wider px-8 py-3.5 cursor-pointer transition-transform active:translate-y-0.5 whitespace-nowrap shrink-0"
          >
            CHOOSE FIGHTER & FIGHT
          </button>
          <span className="text-xs font-mono text-slate-300">
            [ENTER] / [SPACE]
          </span>
        </div>
      </div>

      {/* Bottom Visual Icon Legend + Right-Side 3D Diorama Badge */}
      <div className="flex flex-wrap items-center justify-between gap-4 text-xs text-slate-300 font-mono tracking-wide">
        <div className="flex flex-wrap items-center gap-4">
          <span>[J] PUNCH</span>
          <span>[S+J] LOW LAUNCHER ▲</span>
          <span>[W+J] AIR DRIBBLE</span>
          <span>[K] OVERHEAD ▼</span>
          <span>[L] ELEMENTAL</span>
          <span>[U] ULTIMATE ★</span>
          <span>[B] BREAKER</span>
        </div>
        <div className="hidden lg:flex items-center gap-2 cel-border bg-slate-950/85 px-3 py-1.5 text-[11px] font-mono text-amber-300">
          <span>SANCTUARY DIORAMA: {stage.subtitle.toUpperCase()}</span>
        </div>
      </div>
    </div>
  );
};
