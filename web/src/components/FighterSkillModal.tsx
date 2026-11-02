import React, { useState } from 'react';
import { X, RotateCcw, Check } from 'lucide-react';
import { FIGHTERS, getEffectiveMaxHp, getEffectiveMoveData } from '../game/fighters';
import { FighterId, MoveType } from '../game/types';
import { CharacterAttackIllustration, DrawnMoveIcon } from './DrawnVisuals';

interface FighterSkillModalProps {
  selectedFighter: FighterId;
  unlockedSkillsByFighter: Record<FighterId, string[]>;
  maxSkillPoints: number;
  onSelectFighter: (id: FighterId) => void;
  onToggleSkill: (fighterId: FighterId, skillId: string) => void;
  onResetSkills: (fighterId: FighterId) => void;
  onClose: () => void;
}

const MOVE_ORDER: MoveType[] = [
  'light',
  'down_punch',
  'air_punch',
  'heavy',
  'elemental',
  'ultimate',
];

const MOVE_SHORT_LABELS: Record<MoveType, string> = {
  light: 'PUNCH [J]',
  down_punch: 'DOWN PUNCH [S+J]',
  air_punch: 'AIR PUNCH [W+J]',
  heavy: 'HEAVY [K]',
  elemental: 'SKILL [L]',
  ultimate: 'ULTIMATE [U]',
};

export const FighterSkillModal: React.FC<FighterSkillModalProps> = ({
  selectedFighter,
  unlockedSkillsByFighter,
  maxSkillPoints,
  onSelectFighter,
  onToggleSkill,
  onResetSkills,
  onClose,
}) => {
  const fighter = FIGHTERS[selectedFighter];
  const unlocked = unlockedSkillsByFighter[selectedFighter] || [];
  const [previewMove, setPreviewMove] = useState<MoveType>('down_punch');

  const pointsSpent = fighter.skillTree
    .filter((node) => unlocked.includes(node.id))
    .reduce((acc, node) => acc + node.cost, 0);
  const pointsRemaining = maxSkillPoints - pointsSpent;

  const effectiveHp = getEffectiveMaxHp(selectedFighter, unlocked);
  const activeMoveData = getEffectiveMoveData(selectedFighter, previewMove, unlocked);

  const branches: Array<{
    key: 'combo' | 'elemental' | 'defense';
    label: string;
    color: string;
  }> = [
    { key: 'combo', label: 'COMBO & AIR DRIBBLE', color: '#10b981' },
    { key: 'elemental', label: 'ELEMENTAL & GUST', color: '#38bdf8' },
    { key: 'defense', label: 'ARMOR & GUARD CRUSH', color: '#f59e0b' },
  ];

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/90 p-3 md:p-6 select-none">
      <div className="cel-panel w-full max-w-6xl bg-slate-900 text-slate-50 flex flex-col max-h-[94vh] overflow-hidden">
        {/* Minimal Visual Header: Fighter Portrait Tabs + Skill Points */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5 bg-slate-950 border-b-4 border-slate-950">
          <div className="flex items-center gap-2">
            {(Object.keys(FIGHTERS) as FighterId[]).map((id) => {
              const f = FIGHTERS[id];
              const isSelected = id === selectedFighter;
              return (
                <button
                  key={id}
                  onClick={() => onSelectFighter(id)}
                  className={`cel-panel px-3 py-1.5 flex items-center gap-2 cursor-pointer transition-transform ${
                    isSelected
                      ? 'bg-slate-800 ring-2 ring-emerald-400 -translate-y-0.5'
                      : 'bg-slate-900 opacity-70 hover:opacity-100'
                  }`}
                >
                  <DrawnMoveIcon moveType="ultimate" element={f.element} size={28} />
                  <span className="font-display text-lg tracking-wider text-white">
                    {f.name.split(' ')[0]}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-900 border-2 border-amber-400/80 px-3 py-1">
              <span className="text-xs font-mono uppercase text-amber-300">POINTS</span>
              <span className="font-display text-2xl text-amber-400 leading-none">
                {pointsRemaining} / {maxSkillPoints}
              </span>
            </div>

            <button
              onClick={() => onResetSkills(selectedFighter)}
              className="cel-panel px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-mono uppercase flex items-center gap-1.5 cursor-pointer"
              title="Reset Points"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              RESET
            </button>

            <button
              onClick={onClose}
              className="cel-button bg-emerald-400 hover:bg-emerald-300 text-slate-950 px-4 py-1.5 font-display text-xl tracking-wider flex items-center gap-1.5 cursor-pointer"
            >
              <X className="w-5 h-5" />
              DONE
            </button>
          </div>
        </div>

        {/* Body: Left = Drawn Character & Attack Preview + 6 Drawn Move Icons; Right = Visual Skill Tree Diagram */}
        <div className="p-4 md:p-5 overflow-y-auto grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* LEFT 6 COLS: Visual Character & Attack Drawing Preview + 6 Move Icon Buttons */}
          <div className="lg:col-span-6 flex flex-col gap-3">
            {/* Large Drawn Illustration of the Character Executing the Selected Attack + Hitbox/Hurtbox */}
            <div className="relative">
              <CharacterAttackIllustration
                fighterId={selectedFighter}
                moveType={previewMove}
                className="w-full h-60 md:h-64"
              />
              {/* Compact Visual Stat Badges Overlaid on Corner */}
              <div className="absolute bottom-3 right-3 flex items-center gap-2 bg-slate-950/90 border-2 border-slate-800 px-3 py-1.5">
                <div className="text-center px-2 border-r border-slate-800">
                  <div className="text-[9px] font-mono text-slate-400">STARTUP</div>
                  <div className="font-mono text-sm font-bold text-emerald-400">
                    {activeMoveData.startupFrames}F
                  </div>
                </div>
                <div className="text-center px-2 border-r border-slate-800">
                  <div className="text-[9px] font-mono text-slate-400">DMG</div>
                  <div className="font-mono text-sm font-bold text-amber-300">
                    {activeMoveData.damage}
                  </div>
                </div>
                <div className="text-center px-2">
                  <div className="text-[9px] font-mono text-slate-400">HP</div>
                  <div className="font-mono text-sm font-bold text-white">
                    {effectiveHp}
                  </div>
                </div>
              </div>
            </div>

            {/* 6 Visual Drawn Attack Icon Selector Grid */}
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              {MOVE_ORDER.map((mType) => {
                const mv = getEffectiveMoveData(selectedFighter, mType, unlocked);
                const isSelected = previewMove === mType;
                return (
                  <button
                    key={mType}
                    onClick={() => setPreviewMove(mType)}
                    className={`cel-panel p-2 flex flex-col items-center gap-1.5 cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-slate-800 ring-2 ring-amber-400 -translate-y-1'
                        : 'bg-slate-950/80 opacity-75 hover:opacity-100'
                    }`}
                  >
                    <DrawnMoveIcon
                      moveType={mType}
                      element={fighter.element}
                      size={42}
                    />
                    <div className="text-[9px] font-mono font-bold text-amber-300 uppercase text-center leading-none">
                      {MOVE_SHORT_LABELS[mType]}
                    </div>
                    <div className="font-mono text-[10px] text-emerald-400 font-bold">
                      {mv.startupFrames}F • {mv.damage}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* RIGHT 6 COLS: Visual Skill Tree Nodes (Icon-Driven, Connected Tiers, Minimal Text) */}
          <div className="lg:col-span-6 flex flex-col justify-between gap-3">
            <div className="grid grid-cols-3 gap-3 h-full">
              {branches.map((branch) => {
                const nodes = fighter.skillTree
                  .filter((n) => n.branch === branch.key)
                  .sort((a, b) => a.tier - b.tier);

                return (
                  <div
                    key={branch.key}
                    className="cel-panel bg-slate-950/80 p-3 flex flex-col items-center justify-between relative"
                  >
                    {/* Branch Header */}
                    <div
                      className="w-full text-center py-1 mb-2 font-display text-sm tracking-wider text-slate-950 font-bold"
                      style={{ backgroundColor: branch.color }}
                    >
                      {branch.label}
                    </div>

                    {/* Visual Connector Line Between Tier 1 and Tier 2 */}
                    <div className="flex-1 flex flex-col items-center justify-around w-full relative">
                      {nodes.map((node, idx) => {
                        const isUnlocked = unlocked.includes(node.id);
                        const tier1Node = nodes.find((n) => n.tier === 1);
                        const tier1Unlocked = tier1Node
                          ? unlocked.includes(tier1Node.id)
                          : true;
                        const canAfford = pointsRemaining >= node.cost;
                        const canUnlock =
                          isUnlocked ||
                          (canAfford && (node.tier === 1 || tier1Unlocked));

                        return (
                          <React.Fragment key={node.id}>
                            {idx === 1 && (
                              <div
                                className={`w-1.5 h-6 transition-colors ${
                                  isUnlocked
                                    ? 'bg-emerald-400'
                                    : tier1Unlocked
                                    ? 'bg-amber-400/60'
                                    : 'bg-slate-800'
                                }`}
                              />
                            )}
                            <button
                              onClick={() => {
                                setPreviewMove(node.previewMove);
                                if (canUnlock) {
                                  onToggleSkill(selectedFighter, node.id);
                                }
                              }}
                              className={`w-full cel-panel p-2.5 flex flex-col items-center gap-1.5 transition-all cursor-pointer relative ${
                                isUnlocked
                                  ? 'bg-emerald-950/70 ring-2 ring-emerald-400'
                                  : canUnlock
                                  ? 'bg-slate-900 hover:bg-slate-800'
                                  : 'bg-slate-950 opacity-50'
                              }`}
                            >
                              {/* Cost / Unlocked Badge */}
                              <div className="w-full flex items-center justify-between text-[10px] font-mono">
                                <span className="text-slate-400">T{node.tier}</span>
                                <span
                                  className={`px-1.5 py-0.5 font-bold ${
                                    isUnlocked
                                      ? 'bg-emerald-400 text-slate-950'
                                      : 'bg-slate-800 text-amber-300'
                                  }`}
                                >
                                  {isUnlocked ? (
                                    <span className="flex items-center gap-0.5">
                                      <Check className="w-3 h-3" /> ON
                                    </span>
                                  ) : (
                                    `${node.cost} PT`
                                  )}
                                </span>
                              </div>

                              {/* Large Drawn Icon for the Move this Node Upgrades */}
                              <DrawnMoveIcon
                                moveType={node.previewMove}
                                element={fighter.element}
                                size={52}
                              />

                              <div className="font-display text-base tracking-wider text-white text-center leading-none mt-0.5">
                                {node.name}
                              </div>

                              {/* High-Contrast Visual Stat Tag */}
                              <div
                                className="px-2 py-0.5 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-950"
                                style={{ backgroundColor: branch.color }}
                              >
                                {node.statTag}
                              </div>
                            </button>
                          </React.Fragment>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
