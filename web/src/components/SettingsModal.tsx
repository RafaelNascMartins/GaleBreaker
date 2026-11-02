import React, { useEffect, useState } from 'react';
import { DEFAULT_SETTINGS } from '../game/fighters';
import { GameSettings, KeyBindingMap } from '../game/types';
import { bindingConflict } from '../game/preferences';

interface SettingsModalProps {
  settings: GameSettings;
  onUpdateSettings: (next: GameSettings) => void;
  onClose: () => void;
}

const KEY_LABELS: Record<keyof KeyBindingMap, string> = {
  jump: 'Jump / Air Punch Modifier',
  crouch: 'Crouch / Down Punch Modifier',
  moveLeft: 'Move Left',
  moveRight: 'Move Right',
  lightAttack: 'Punch / Down Punch / Air Punch',
  heavyAttack: 'Heavy Kick (Launcher)',
  elementalSkill: 'Elemental Gust (Hazard Push)',
  ultimateArt: 'Ultimate Art (50% Gauge)',
  guardParry: 'Guard / Perfect Parry',
  dashStep: 'Slipstream Dash',
  comboBreaker: 'Combo Breaker (Escape Stun)',
};

export const SettingsModal: React.FC<SettingsModalProps> = ({
  settings,
  onUpdateSettings,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'controls' | 'audio' | 'graphics'>('controls');
  const [bindingError, setBindingError] = useState('');
  const [listeningBind, setListeningBind] = useState<{
    player: 1 | 2;
    action: keyof KeyBindingMap;
  } | null>(null);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.code === 'Escape' && !listeningBind) {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [listeningBind, onClose]);

  useEffect(() => {
    if (!listeningBind) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      e.preventDefault();
      e.stopImmediatePropagation();
      if (e.code === 'Escape') {
        setListeningBind(null);
        return;
      }
      const error = bindingConflict(settings, listeningBind.player, listeningBind.action, e.code);
      if (error) {
        setBindingError(error);
        return;
      }
      setBindingError('');
      const keyProp = listeningBind.player === 1 ? 'p1Keys' : 'p2Keys';
      onUpdateSettings({
        ...settings,
        [keyProp]: {
          ...settings[keyProp],
          [listeningBind.action]: e.code,
        },
      });
      setListeningBind(null);
    };
    window.addEventListener('keydown', handleKeyDown, { capture: true });
    return () => window.removeEventListener('keydown', handleKeyDown, { capture: true });
  }, [listeningBind, settings, onUpdateSettings]);

  const formatKeyCode = (code: string) =>
    code.replace(/^Key/, '').replace(/^Digit/, '').replace(/^Arrow/, 'Arrow ');

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Options and Controls"
      className="fixed inset-0 z-30 flex items-center justify-center p-4 md:p-8 bg-slate-950/88 pointer-events-auto"
    >
      <div className="cel-border bg-slate-900 text-slate-100 w-full max-w-4xl max-h-[88vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 bg-slate-950 border-b-2 border-slate-800">
          <div>
            <h2 className="font-display font-bold text-xl uppercase tracking-wider text-white">
              Options, Keybindings & Hitboxes
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => onUpdateSettings(DEFAULT_SETTINGS)}
              className="cel-border bg-slate-800 hover:bg-slate-700 text-slate-200 font-display font-bold text-xs uppercase px-3.5 py-2 cursor-pointer whitespace-nowrap"
            >
              Reset Defaults
            </button>
            <button
              type="button"
              onClick={onClose}
              className="cel-border bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-display font-bold text-xs uppercase px-4 py-2 cursor-pointer whitespace-nowrap"
            >
              Save & Close
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 px-6 pt-4 border-b border-slate-800 bg-slate-900">
          {(
            [
              { id: 'controls', label: 'Keybindings (P1 & P2)' },
              { id: 'audio', label: 'Sound & Synthesizer' },
              { id: 'graphics', label: 'Hitboxes & Graphics' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-xs font-display font-bold uppercase tracking-wider cursor-pointer whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-amber-500 text-slate-950 cel-border-accent'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 cel-border'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6 overflow-y-auto space-y-6">
          {bindingError && <p role="alert" className="text-sm text-amber-300">{bindingError}</p>}
          {activeTab === 'controls' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {([1, 2] as const).map((playerNum) => {
                const map = playerNum === 1 ? settings.p1Keys : settings.p2Keys;
                return (
                  <div key={playerNum} className="cel-border bg-slate-950 p-4 space-y-2.5">
                    <h3 className="font-display font-bold text-sm uppercase tracking-wider text-emerald-400 pb-1 border-b border-slate-800">
                      Player {playerNum} Controls
                    </h3>
                    {(Object.keys(KEY_LABELS) as (keyof KeyBindingMap)[]).map((actionKey) => {
                      const isListening =
                        listeningBind?.player === playerNum &&
                        listeningBind?.action === actionKey;
                      return (
                        <div
                          key={actionKey}
                          className="flex items-center justify-between gap-2 text-xs py-1"
                        >
                          <span className="text-slate-300">{KEY_LABELS[actionKey]}</span>
                          <button
                            type="button"
                            onClick={() =>
                              setListeningBind({ player: playerNum, action: actionKey })
                            }
                            className={`px-3 py-1 font-mono-tabular text-xs font-bold uppercase cursor-pointer whitespace-nowrap ${
                              isListening
                                ? 'bg-amber-500 text-slate-950 cel-border-accent'
                                : 'bg-slate-800 hover:bg-slate-700 text-slate-100 cel-border'
                            }`}
                          >
                            {isListening ? 'Press Key...' : formatKeyCode(map[actionKey])}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          )}

          {activeTab === 'audio' && (
            <div className="max-w-xl space-y-5 cel-border bg-slate-950 p-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-display font-bold text-sm uppercase text-white">
                    Mute All Audio
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    onUpdateSettings({ ...settings, muted: !settings.muted })
                  }
                  className={`px-4 py-2 text-xs font-display font-bold uppercase cursor-pointer ${
                    settings.muted
                      ? 'bg-rose-500 text-white cel-border'
                      : 'bg-emerald-500 text-slate-950 cel-border-accent'
                  }`}
                >
                  {settings.muted ? 'Muted' : 'Audio Active'}
                </button>
              </div>

              <label className="block space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span>Master Volume</span>
                  <span className="font-mono-tabular text-amber-400">
                    {Math.round(settings.masterVolume * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={settings.masterVolume}
                  onChange={(e) =>
                    onUpdateSettings({
                      ...settings,
                      masterVolume: parseFloat(e.target.value),
                    })
                  }
                  className="w-full accent-emerald-500 cursor-pointer"
                />
              </label>
            </div>
          )}

          {activeTab === 'graphics' && (
            <div className="max-w-xl space-y-5 cel-border bg-slate-950 p-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-display font-bold text-sm uppercase text-white">
                    2D Hitbox & Hurtbox Overlays
                  </div>
                  <div className="text-xs text-slate-400">
                    Show live 2D bounding boxes on fighters and active strikes
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    onUpdateSettings({
                      ...settings,
                      showHitboxes: !settings.showHitboxes,
                    })
                  }
                  className={`px-4 py-2 text-xs font-display font-bold uppercase cursor-pointer ${
                    settings.showHitboxes
                      ? 'bg-emerald-500 text-slate-950 cel-border-accent'
                      : 'bg-slate-800 text-slate-300 cel-border'
                  }`}
                >
                  {settings.showHitboxes ? 'Visible' : 'Hidden'}
                </button>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                <div>
                  <div className="font-display font-bold text-sm uppercase text-white">
                    Cel-Shaded Ink Outlines
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    onUpdateSettings({
                      ...settings,
                      celOutlines: !settings.celOutlines,
                    })
                  }
                  className={`px-4 py-2 text-xs font-display font-bold uppercase cursor-pointer ${
                    settings.celOutlines
                      ? 'bg-emerald-500 text-slate-950 cel-border-accent'
                      : 'bg-slate-800 text-slate-300 cel-border'
                  }`}
                >
                  {settings.celOutlines ? 'Enabled' : 'Disabled'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
