import React, { useEffect } from 'react';
import { FIGHTERS, FIGHTER_PALETTES, STAGES } from '../game/fighters';
import { FighterId, GameMode, MoveType, StageId } from '../game/types';
import { DrawnMoveIcon, StagePreviewCardArt } from './DrawnVisuals';

interface CharacterStageSelectScreenProps {
  mode: GameMode;
  selectedFighter: FighterId;
  selectedPalette: number;
  p2Fighter?: FighterId;
  p2Palette?: number;
  selectedStage: StageId;
  isFighterChosen: boolean;
  keyboardEnabled?: boolean;
  onSelectFighter: (id: FighterId) => void;
  onSelectPalette: (paletteIndex: number) => void;
  onSelectP2Fighter?: (id: FighterId) => void;
  onSelectP2Palette?: (paletteIndex: number) => void;
  onPreviewMove?: (moveType: MoveType) => void;
  onSelectStage: (id: StageId) => void;
  onConfirmSelection: () => void;
  onOpenSkillTree: () => void;
  onBackToTitle: () => void;
}

const FIGHTER_ORDER: FighterId[] = ['kaze', 'ignis', 'tophia', 'volt'];
const STAGE_ORDER: StageId[] = ['zephyr_dojo', 'molten_forge', 'storm_market'];
const PREVIEW_MOVES: MoveType[] = [
  'light',
  'down_punch',
  'air_punch',
  'heavy',
  'elemental',
  'ultimate',
];

export const CharacterStageSelectScreen: React.FC<CharacterStageSelectScreenProps> = ({
  mode,
  selectedFighter,
  selectedPalette,
  p2Fighter = 'ignis',
  p2Palette = 0,
  selectedStage,
  isFighterChosen,
  keyboardEnabled = true,
  onSelectFighter,
  onSelectPalette,
  onSelectP2Fighter,
  onSelectP2Palette,
  onPreviewMove,
  onSelectStage,
  onConfirmSelection,
  onOpenSkillTree,
  onBackToTitle,
}) => {
  // Full keyboard navigation for choosing fighter (A/D or Left/Right), stage (Q/E or Up/Down), palette (C), P2 Rival (V), and confirming (Enter/Space)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isFighterChosen || !keyboardEnabled || e.defaultPrevented || e.repeat) return;

      if (e.code === 'ArrowLeft' || e.code === 'KeyA') {
        e.preventDefault();
        const idx = FIGHTER_ORDER.indexOf(selectedFighter);
        const nextIdx = (idx - 1 + FIGHTER_ORDER.length) % FIGHTER_ORDER.length;
        onSelectFighter(FIGHTER_ORDER[nextIdx]);
      } else if (e.code === 'ArrowRight' || e.code === 'KeyD') {
        e.preventDefault();
        const idx = FIGHTER_ORDER.indexOf(selectedFighter);
        const nextIdx = (idx + 1) % FIGHTER_ORDER.length;
        onSelectFighter(FIGHTER_ORDER[nextIdx]);
      } else if (e.code === 'KeyC') {
        e.preventDefault();
        onSelectPalette((selectedPalette + 1) % 4);
      } else if (e.code === 'KeyV' && mode !== 'arcade' && onSelectP2Fighter) {
        e.preventDefault();
        const idx = FIGHTER_ORDER.indexOf(p2Fighter);
        const nextIdx = (idx + 1) % FIGHTER_ORDER.length;
        onSelectP2Fighter(FIGHTER_ORDER[nextIdx]);
      } else if (e.code === 'ArrowUp' || e.code === 'KeyW' || e.code === 'KeyQ') {
        e.preventDefault();
        const sIdx = STAGE_ORDER.indexOf(selectedStage);
        const nextSIdx = (sIdx - 1 + STAGE_ORDER.length) % STAGE_ORDER.length;
        onSelectStage(STAGE_ORDER[nextSIdx]);
      } else if (e.code === 'ArrowDown' || e.code === 'KeyS' || e.code === 'KeyE') {
        e.preventDefault();
        const sIdx = STAGE_ORDER.indexOf(selectedStage);
        const nextSIdx = (sIdx + 1) % STAGE_ORDER.length;
        onSelectStage(STAGE_ORDER[nextSIdx]);
      } else if (e.code === 'KeyT') {
        e.preventDefault();
        onOpenSkillTree();
      } else if (e.code === 'Enter' || e.code === 'Space') {
        e.preventDefault();
        onConfirmSelection();
      } else if (e.code === 'Escape') {
        e.preventDefault();
        onBackToTitle();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    mode,
    selectedFighter,
    selectedPalette,
    p2Fighter,
    selectedStage,
    isFighterChosen,
    keyboardEnabled,
    onSelectFighter,
    onSelectPalette,
    onSelectP2Fighter,
    onSelectStage,
    onConfirmSelection,
    onOpenSkillTree,
    onBackToTitle,
  ]);

  const activeFighter = FIGHTERS[selectedFighter];
  const fighterPalettes = FIGHTER_PALETTES[selectedFighter];
  const activePalette = fighterPalettes[selectedPalette] || fighterPalettes[0];
  const rivalFighter = FIGHTERS[p2Fighter];
  const rivalPalettes = FIGHTER_PALETTES[p2Fighter];
  const activeRivalPalette = rivalPalettes[p2Palette] || rivalPalettes[0];

  return (
    <div className="fixed inset-0 z-20 pointer-events-none flex flex-col justify-between p-5 md:p-7 select-none">
      {/* Top Bar: Back Button + Visual Stage Selector Cards (Sanctuary / Crimson Anvil / Arabic Bazaar) */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 pointer-events-auto">
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={onBackToTitle}
            className="cel-panel bg-slate-950/90 hover:bg-slate-900 text-slate-200 px-3.5 py-2 text-xs font-mono uppercase tracking-widest cursor-pointer"
          >
            [ESC] BACK
          </button>
          <div className="cel-panel bg-slate-950/90 px-4 py-2">
            <div className="text-[10px] font-mono uppercase tracking-widest text-amber-400">
              {mode.toUpperCase()} MODE • COURTYARD LINEUP
            </div>
            <h1 className="font-display text-2xl md:text-3xl tracking-wider text-white leading-none">
              CHOOSE FIGHTER & SANCTUARY
            </h1>
          </div>

          {/* Item 17: P2 Rival & Skin Selector for Versus / Training Mode */}
          {mode !== 'arcade' && (
            <div className="cel-panel bg-slate-950/90 px-3 py-1.5 flex items-center gap-2.5 border border-cyan-500/40">
              <div>
                <div className="text-[9px] font-mono uppercase tracking-widest text-cyan-400">
                  [V] P2 RIVAL ({mode === 'training' ? 'DUMMY' : 'PLAYER 2'})
                </div>
                <div className="font-display text-sm uppercase tracking-wider text-white">
                  {rivalFighter.name} • {activeRivalPalette.name}
                </div>
              </div>
              <div className="flex items-center gap-1">
                {FIGHTER_ORDER.map((rId) => (
                  <button
                    key={rId}
                    type="button"
                    onClick={() => !isFighterChosen && onSelectP2Fighter?.(rId)}
                    className={`px-1.5 py-0.5 text-[10px] font-mono uppercase cursor-pointer border ${
                      p2Fighter === rId
                        ? 'bg-cyan-400 text-slate-950 font-bold border-white'
                        : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800'
                    }`}
                  >
                    {FIGHTERS[rId].name.split(' ')[0]}
                  </button>
                ))}
              </div>
              <button
                type="button"
                title="Cycle P2 Skin"
                onClick={() =>
                  !isFighterChosen && onSelectP2Palette?.((p2Palette + 1) % 4)
                }
                className="w-5 h-5 border border-cyan-300 flex overflow-hidden cursor-pointer"
              >
                <span
                  className="w-1/2 h-full"
                  style={{ backgroundColor: activeRivalPalette.swatch[0] }}
                />
                <span
                  className="w-1/2 h-full"
                  style={{ backgroundColor: activeRivalPalette.swatch[2] }}
                />
              </button>
            </div>
          )}
        </div>

        {/* 3 Visual Stage Picture Cards */}
        <div className="flex items-center gap-2.5">
          {STAGE_ORDER.map((stageId) => {
            const st = STAGES[stageId];
            const active = selectedStage === stageId;
            return (
              <button
                key={stageId}
                onClick={() => !isFighterChosen && onSelectStage(stageId)}
                className={`cel-panel relative w-36 md:w-44 h-20 overflow-hidden transition-transform cursor-pointer ${
                  active
                    ? 'ring-2 ring-amber-400 -translate-y-1 scale-105'
                    : 'opacity-75 hover:opacity-100'
                }`}
              >
                <StagePreviewCardArt stageId={stageId} className="w-full h-full" />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/20 to-transparent flex flex-col justify-end p-2 text-left">
                  <div className="flex items-center justify-between">
                    <span className="font-display text-sm tracking-wider text-white leading-none">
                      {st.name.split(' ')[0]} {st.name.split(' ')[1]}
                    </span>
                    {active && (
                      <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold bg-amber-400 text-slate-950">
                        STAGE
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Center Viewport Left Open so All 4 3D Fighters Stand Together in Idle Pose & Chosen Animation */}
      <div className="flex-1 flex items-center justify-center pointer-events-none">
        {isFighterChosen && (
          <div className="cel-panel bg-slate-950/90 px-8 py-4 border-2 border-amber-400 animate-bounce">
            <div className="font-display text-4xl md:text-5xl tracking-wider text-amber-300 text-center">
              {activeFighter.name.toUpperCase()} CHOSEN!
            </div>
          </div>
        )}
      </div>

      {/* Bottom Dock: 4 Fighter Selection Cards + Drawn Attack Icons + Skill Tree & Confirm CTA */}
      <div className="flex flex-col gap-3 pointer-events-auto">
        {/* Selected Fighter Drawn Move Icon Strip */}
        <div className="flex flex-wrap items-center justify-between gap-3 cel-panel bg-slate-950/90 px-4 py-2.5">
          <div className="flex items-center gap-3">
            <div
              className="w-3 h-10"
              style={{
                backgroundColor: activePalette.swatch[0],
              }}
            />
            <div>
              <div className="flex items-center gap-2">
                <div className="font-display text-2xl tracking-wider text-white leading-none">
                  {activeFighter.name}
                </div>
                <span className="px-1.5 py-0.5 text-[10px] font-mono uppercase bg-emerald-950/90 border border-emerald-500/50 text-emerald-300">
                  {activeFighter.martialStyle}
                </span>
                <span className="px-1.5 py-0.5 text-[10px] font-mono uppercase bg-slate-800 border border-slate-700 text-amber-300">
                  SKIN: {activePalette.name}
                </span>
              </div>
              <div className="text-[11px] font-mono uppercase tracking-widest text-emerald-400">
                {activeFighter.title} • [A / D] FIGHTER • [C] SKIN • [W / S] STAGE
              </div>
            </div>

            {/* Item 17: Compact Martial Stats Radar Bars */}
            <div className="hidden xl:grid grid-cols-2 gap-x-3 gap-y-1 bg-slate-900/90 border border-slate-800 px-2.5 py-1 text-[10px] font-mono">
              {(
                [
                  ['SPD', activeFighter.stats.speed],
                  ['RNG', activeFighter.stats.range],
                  ['PWR', activeFighter.stats.power],
                  ['DEF', activeFighter.stats.defense],
                ] as const
              ).map(([label, val]) => (
                <div key={label} className="flex items-center gap-1.5">
                  <span className="text-slate-400 w-6">{label}</span>
                  <div className="flex gap-0.5">
                    {[1, 2, 3, 4, 5].map((dot) => (
                      <span
                        key={dot}
                        className={`w-2 h-2 ${
                          dot <= val ? 'bg-amber-400' : 'bg-slate-800'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
            {/* 4 Palette Color Swatches */}
            <div className="flex items-center gap-1.5 ml-2 bg-slate-900/90 border border-slate-800 px-2 py-1.5">
              <span className="text-[10px] font-mono text-slate-400 uppercase mr-1">
                [C]
              </span>
              {fighterPalettes.map((pal, pIdx) => {
                const isPalActive = selectedPalette === pIdx;
                const pHex = pal.swatch[0];
                const aHex = pal.swatch[2];
                return (
                  <button
                    key={pal.id}
                    type="button"
                    title={`${pal.name} (Palette ${pIdx + 1})`}
                    onClick={() => !isFighterChosen && onSelectPalette(pIdx)}
                    className={`w-5 h-5 border transition-transform cursor-pointer flex overflow-hidden ${
                      isPalActive
                        ? 'border-white scale-115 ring-1 ring-amber-400'
                        : 'border-slate-700 opacity-70 hover:opacity-100'
                    }`}
                  >
                    <span className="w-1/2 h-full" style={{ backgroundColor: pHex }} />
                    <span className="w-1/2 h-full" style={{ backgroundColor: aHex }} />
                  </button>
                );
              })}
            </div>
          </div>

          {/* 6 Drawn Attack Icons for Selected Fighter (Click or Hover triggers 3D Live Move Preview!) */}
          <div className="flex items-center gap-2">
            {PREVIEW_MOVES.map((mType) => {
              const mv = activeFighter.moves[mType];
              return (
                <button
                  key={mType}
                  type="button"
                  onClick={() => !isFighterChosen && onPreviewMove?.(mType)}
                  onMouseEnter={() => !isFighterChosen && onPreviewMove?.(mType)}
                  className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-amber-400 px-2 py-1 transition-colors cursor-pointer text-left"
                  title={`${mv.name} — Click to preview in 3D`}
                >
                  <DrawnMoveIcon
                    moveType={mType}
                    element={activeFighter.element}
                    size={30}
                  />
                  <div className="hidden sm:block">
                    <div className="text-[9px] font-mono uppercase text-slate-400 leading-none">
                      {mType === 'light'
                        ? 'PUNCH [J]'
                        : mType === 'down_punch'
                        ? 'DOWN [S+J]'
                        : mType === 'air_punch'
                        ? 'AIR [W+J]'
                        : mType === 'heavy'
                        ? 'HEAVY [K]'
                        : mType === 'elemental'
                        ? 'SKILL [L]'
                        : 'ULT [U]'}
                    </div>
                    <div className="font-display text-xs tracking-wider text-white leading-tight">
                      {mv.name.split(' ')[0]}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Visual Skill Tree & Confirm Buttons */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={onOpenSkillTree}
              className="cel-panel bg-slate-900 hover:bg-slate-800 text-amber-300 px-3.5 py-2.5 font-display text-lg tracking-wider cursor-pointer flex items-center gap-2"
            >
              <DrawnMoveIcon
                moveType="elemental"
                element={activeFighter.element}
                size={24}
              />
              <span>[T] SKILL TREE</span>
            </button>

            <button
              onClick={onConfirmSelection}
              disabled={isFighterChosen}
              className="cel-button bg-emerald-400 hover:bg-emerald-300 text-slate-950 font-display text-2xl tracking-wider px-6 py-2.5 cursor-pointer"
            >
              {isFighterChosen ? 'ENTERING ARENA...' : '[ENTER] FIGHT!'}
            </button>
          </div>
        </div>

        {/* 4 Pedestal Cards aligned under the 4 3D Fighters */}
        <div className="grid grid-cols-4 gap-3">
          {FIGHTER_ORDER.map((id, idx) => {
            const f = FIGHTERS[id];
            const isSelected = selectedFighter === id;
            return (
              <button
                key={id}
                onClick={() => !isFighterChosen && onSelectFighter(id)}
                className={`cel-panel p-2.5 flex items-center justify-between transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-slate-900 ring-2 ring-emerald-400 -translate-y-1.5'
                    : 'bg-slate-950/85 opacity-75 hover:opacity-100'
                }`}
              >
                <div className="flex items-center gap-2.5 text-left">
                  <DrawnMoveIcon moveType="ultimate" element={f.element} size={36} />
                  <div>
                    <div className="text-[10px] font-mono text-slate-400 uppercase">
                      P1 • [{idx + 1}]
                    </div>
                    <div className="font-display text-xl tracking-wider text-white leading-none">
                      {f.name.split(' ')[0]}
                    </div>
                  </div>
                </div>
                <span
                  className="w-3 h-8 border border-slate-950"
                  style={{ backgroundColor: f.primaryColor }}
                />
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
