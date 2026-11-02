/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { CharacterStageSelectScreen } from './components/CharacterStageSelectScreen';
import { CombatHUD } from './components/CombatHUD';
import { FighterSkillModal } from './components/FighterSkillModal';
import { LoadingScreen } from './components/LoadingScreen';
import { PauseAndOutcomeModal } from './components/PauseAndOutcomeModal';
import { SettingsModal } from './components/SettingsModal';
import { TitleScreen } from './components/TitleScreen';
import {
  computeAiInput,
  createInitialCombatSnapshot,
  PlayerFrameInput,
  stepCombatSimulation,
} from './game/combatEngine';
import { getArcadeStageSpec } from './game/arcadeTower';
import {
  COMBAT_TIPS,
  FIGHTERS,
  getFighterPalette,
} from './game/fighters';
import { FixedStepClock } from './game/fixedStep';
import { loadPreferences, savePreferences, toggleSkill, MAX_SKILL_POINTS } from './game/preferences';
import { TransitionTimers } from './game/transitionTimers';
import { soundEngine } from './game/soundEngine';
import { CelArenaRenderer, isSoftwareGl } from './game/threeScene';
import {
  CombatSnapshot,
  FighterId,
  GameMode,
  GameScreenState,
  GameSettings,
  MoveType,
  StageId,
} from './game/types';

export default function App() {
  const initialAutostart =
    typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).get('autostart') === '1';

  const [screenState, setScreenState] = useState<GameScreenState>(
    initialAutostart ? 'playing' : 'title'
  );
  const [selectedMode, setSelectedMode] = useState<GameMode>('arcade');
  const [p1Fighter, setP1Fighter] = useState<FighterId>('kaze');
  const [p1Palette, setP1Palette] = useState<number>(0);
  const [p2Fighter, setP2Fighter] = useState<FighterId>('ignis');
  const [p2Palette, setP2Palette] = useState<number>(0);
  const [selectedStage, setSelectedStage] = useState<StageId>('zephyr_dojo');
  const [isFighterChosen, setIsFighterChosen] = useState(false);
  const [blackCurtain, setBlackCurtain] = useState(false);
  const [rivalryBannerText, setRivalryBannerText] = useState<string>('');

  const [preferences] = useState(() => loadPreferences());
  const [p1Skills, setP1Skills] = useState(preferences.skills);
  const [settings, setSettings] = useState<GameSettings>(preferences.settings);
  const transitionTimers = useRef(new TransitionTimers());
  const simulationClock = useRef(new FixedStepClock());
  const koTransitionPending = useRef(false);
  const scheduleTransition = useCallback((callback: () => void, delay: number) =>
    transitionTimers.current.schedule(callback, delay), []);
  const cancelTransitions = useCallback(() => {
    transitionTimers.current.cancel();
    koTransitionPending.current = false;
    simulationClock.current.reset();
  }, []);

  useEffect(() => { savePreferences(settings, p1Skills); }, [settings, p1Skills]);
  useEffect(() => () => transitionTimers.current.cancel(), []);
  const [showRosterModal, setShowRosterModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [tipIndex, setTipIndex] = useState(0);
  const [introBannerVisible, setIntroBannerVisible] = useState(false);

  const [hudSnapshot, setHudSnapshot] = useState<CombatSnapshot>(() =>
    createInitialCombatSnapshot(
      'kaze',
      'ignis',
      'zephyr_dojo',
      preferences.skills.kaze,
      [],
      'arcade',
      1,
      0
    )
  );

  // Refs for decoupled 60Hz simulation & Three.js renderer
  const canvasMountRef = useRef<HTMLDivElement | null>(null);
  const arenaRendererRef = useRef<CelArenaRenderer | null>(null);
  const simRef = useRef<CombatSnapshot>(hudSnapshot);
  const screenStateRef = useRef<GameScreenState>(screenState);
  const modeRef = useRef<GameMode>(selectedMode);
  const settingsRef = useRef<GameSettings>(settings);
  const stageRef = useRef<StageId>(selectedStage);
  const p1FighterRef = useRef<FighterId>(p1Fighter);
  const p1PaletteRef = useRef<number>(p1Palette);
  const p2FighterRef = useRef<FighterId>(p2Fighter);
  const p2PaletteRef = useRef<number>(p2Palette);
  const p1SkillsRef = useRef<Record<FighterId, string[]>>(p1Skills);
  const modalOpenRef = useRef<boolean>(false);

  // Unified Input Hub
  const keysHeldRef = useRef<Set<string>>(new Set());
  const keysJustPressedRef = useRef<Set<string>>(new Set());
  const uiQueuedMoveP1Ref = useRef<MoveType | null>(null);
  const uiQueuedBreakerP1Ref = useRef<boolean>(false);

  useEffect(() => {
    screenStateRef.current = screenState;
    const bodyState =
      screenState === 'loading' || screenState === 'select' ? 'playing' : screenState;
    document.body.dataset.state = bodyState;
    simulationClock.current.reset();
  }, [screenState]);

  useEffect(() => {
    modeRef.current = selectedMode;
  }, [selectedMode]);

  useEffect(() => {
    settingsRef.current = settings;
  }, [settings]);

  useEffect(() => {
    stageRef.current = selectedStage;
  }, [selectedStage]);

  useEffect(() => {
    p1FighterRef.current = p1Fighter;
    p1PaletteRef.current = p1Palette;
    if (arenaRendererRef.current) {
      arenaRendererRef.current.setLineupSelection(
        p1Fighter,
        isFighterChosen,
        p1Palette
      );
    }
  }, [p1Fighter, p1Palette, isFighterChosen]);

  useEffect(() => {
    p2FighterRef.current = p2Fighter;
    p2PaletteRef.current = p2Palette;
  }, [p2Fighter, p2Palette]);

  useEffect(() => {
    p1SkillsRef.current = p1Skills;
  }, [p1Skills]);

  useEffect(() => {
    modalOpenRef.current = showRosterModal || showSettingsModal;
    keysHeldRef.current.clear();
    keysJustPressedRef.current.clear();
  }, [showRosterModal, showSettingsModal]);

  const resetCombatMatch = useCallback(
    (
      nextMode: GameMode,
      nextP1: FighterId,
      nextP2: FighterId,
      nextStage: StageId,
      arcadeStageIdx = 1,
      initialCountdown = 3.0,
      p2Skills: string[] = [],
      p1Pal = p1PaletteRef.current,
      p2Pal = 0
    ) => {
      const fresh = createInitialCombatSnapshot(
        nextP1,
        nextP2,
        nextStage,
        p1SkillsRef.current[nextP1] || [],
        p2Skills,
        nextMode,
        arcadeStageIdx,
        initialCountdown,
        p1Pal,
        p2Pal
      );
      koTransitionPending.current = false;
      simulationClock.current.reset();
      keysHeldRef.current.clear();
      keysJustPressedRef.current.clear();
      uiQueuedMoveP1Ref.current = null;
      uiQueuedBreakerP1Ref.current = false;
      simRef.current = fresh;
      setHudSnapshot(structuredClone(fresh));
      if (arenaRendererRef.current) {
        arenaRendererRef.current.syncStageAndFighters(
          nextStage,
          nextP1,
          nextP2,
          fresh.hazards,
          fresh.p1.paletteIndex,
          fresh.p2.paletteIndex
        );
      }
    },
    []
  );

  // Transition from Title -> Fade to Black -> Outdoor Courtyard 3D Lineup Select Screen
  const openCourtyardSelect = useCallback(() => {
    cancelTransitions();
    soundEngine.playUiClick(settingsRef.current);
    setIsFighterChosen(false);
    setBlackCurtain(true);
    scheduleTransition(() => {
      setScreenState('select');
      scheduleTransition(() => {
        setBlackCurtain(false);
      }, 140);
    }, 220);
  }, [cancelTransitions, scheduleTransition]);

  // Confirm Fighter & Stage in Courtyard -> Play Chosen Animation -> Fade to Black -> Loading -> 3-2-1 Countdown -> Battle!
  const handleConfirmCharacterAndStage = useCallback(() => {
    if (isFighterChosen) return;
    soundEngine.playKoFanfare(settingsRef.current, true);
    soundEngine.playFighterVoice(
      settingsRef.current,
      p1FighterRef.current,
      'ultimate'
    );
    setIsFighterChosen(true);
    if (arenaRendererRef.current) {
      arenaRendererRef.current.setLineupSelection(
        p1FighterRef.current,
        true,
        p1PaletteRef.current
      );
    }

    // Play the 3D Chosen Victory Animation for 750ms, then fade to black -> loading -> arena with 3-2-1 countdown
    scheduleTransition(() => {
      setBlackCurtain(true);
      scheduleTransition(() => {
        const arcadeSpec = getArcadeStageSpec(p1FighterRef.current, 1);
        const opp =
          modeRef.current === 'arcade'
            ? arcadeSpec.opponentId
            : p2FighterRef.current;
        if (modeRef.current === 'arcade') {
          setP2Fighter(opp);
        }
        setRivalryBannerText(
          modeRef.current === 'arcade'
            ? `${arcadeSpec.title} • ${arcadeSpec.rivalryBanner}`
            : ''
        );
        setTipIndex((prev) => prev + 1);
        resetCombatMatch(
          modeRef.current,
          p1FighterRef.current,
          opp,
          stageRef.current,
          1,
          3.0,
          modeRef.current === 'arcade' ? arcadeSpec.unlockedSkills : [],
          p1PaletteRef.current,
          modeRef.current === 'arcade'
            ? arcadeSpec.opponentPalette
            : p2PaletteRef.current
        );
        setScreenState('loading');
        setBlackCurtain(false);

        scheduleTransition(() => {
          setBlackCurtain(true);
          scheduleTransition(() => {
            setIsFighterChosen(false);
            setScreenState('playing');
            setBlackCurtain(false);
            setIntroBannerVisible(true);
            scheduleTransition(() => {
              setIntroBannerVisible(false);
            }, 2800);
          }, 160);
        }, 420);
      }, 220);
    }, 750);
  }, [isFighterChosen, resetCombatMatch, scheduleTransition]);

  const startNewMatch = useCallback(
    (arcadeStageIdx = 1, useFullLoadingCurtain = false, withCountdown = false) => {
      cancelTransitions();
      let opp = p2FighterRef.current;
      let stg = stageRef.current;
      let oppSkills: string[] = [];
      let oppPal = p2PaletteRef.current;

      if (modeRef.current === 'arcade') {
        const arcadeSpec = getArcadeStageSpec(
          p1FighterRef.current,
          arcadeStageIdx
        );
        opp = arcadeSpec.opponentId;
        oppSkills = arcadeSpec.unlockedSkills;
        oppPal = arcadeSpec.opponentPalette;
        setRivalryBannerText(`${arcadeSpec.title} • ${arcadeSpec.rivalryBanner}`);
        if (arcadeStageIdx > 1) {
          stg = arcadeSpec.stageId;
          setSelectedStage(stg);
        }
        setP2Fighter(opp);
      } else {
        setRivalryBannerText('');
      }

      keysHeldRef.current.clear();
      keysJustPressedRef.current.clear();
      if (document.activeElement instanceof HTMLElement) {
        document.activeElement.blur();
      }

      setTipIndex((prev) => prev + 1);
      resetCombatMatch(
        modeRef.current,
        p1FighterRef.current,
        opp,
        stg,
        arcadeStageIdx,
        withCountdown ? 3.0 : 0,
        oppSkills,
        p1PaletteRef.current,
        oppPal
      );

      if (useFullLoadingCurtain) {
        setBlackCurtain(true);
        scheduleTransition(() => {
          setScreenState('loading');
          setBlackCurtain(false);
          scheduleTransition(() => {
            setScreenState('playing');
          }, 380);
        }, 180);
      } else {
        setScreenState('playing');
        setIntroBannerVisible(true);
        scheduleTransition(() => {
          setIntroBannerVisible(false);
        }, 2600);
      }
      soundEngine.playUiClick(settingsRef.current);
    },
    [resetCombatMatch, cancelTransitions, scheduleTransition]
  );

  // Initialize Three.js WebGLRenderer & 60Hz Simulation Loop once on mount
  useEffect(() => {
    const container = canvasMountRef.current;
    if (!container) return;

    const arena = new CelArenaRenderer(container);
    arenaRendererRef.current = arena;
    arena.syncStageAndFighters(
      stageRef.current,
      p1FighterRef.current,
      p2FighterRef.current,
      simRef.current.hazards,
      simRef.current.p1.paletteIndex,
      simRef.current.p2.paletteIndex
    );
    arena.setLineupSelection(
      p1FighterRef.current,
      false,
      p1PaletteRef.current
    );

    if (!isSoftwareGl) {
      arena.renderer.compile(arena.scene, arena.cameraP1);
    }

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          arena.handleResize(width, height);
        }
      }
    });
    resizeObserver.observe(container);

    let frameId = 0;
    let lastTime = performance.now();
    let elapsed = 0;
    let hudSyncAccumulator = 0;
    let lastCountdownSec = 0;

    const afterDraw = (cb: () => void) => {
      const gl = arena.renderer.getContext() as WebGL2RenderingContext;
      const sync = gl.fenceSync ? gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE, 0) : null;
      gl.flush();
      const poll = () => {
        const state = sync && gl.getSyncParameter(sync, gl.SYNC_STATUS);
        if (state === gl.UNSIGNALED) {
          frameId = window.setTimeout(poll, 5);
        } else {
          if (sync) gl.deleteSync(sync);
          frameId = window.setTimeout(cb, 80);
        }
      };
      frameId = window.setTimeout(poll, 5);
    };

    const extractPlayerInput = (
      playerNum: 1 | 2,
      dt: number
    ): PlayerFrameInput => {
      const held = keysHeldRef.current;
      const just = keysJustPressedRef.current;
      const binds =
        playerNum === 1 ? settingsRef.current.p1Keys : settingsRef.current.p2Keys;

      if (playerNum === 2 && modeRef.current !== 'versus') {
        return computeAiInput(
          simRef.current.p2,
          simRef.current.p1,
          simRef.current.hazards,
          dt
        );
      }

      let moveX = 0;
      if (held.has(binds.moveRight)) moveX += 1;
      if (held.has(binds.moveLeft)) moveX -= 1;

      let attackJustPressed: MoveType | null = null;
      if (playerNum === 1 && uiQueuedMoveP1Ref.current) {
        attackJustPressed = uiQueuedMoveP1Ref.current;
        uiQueuedMoveP1Ref.current = null;
      } else if (just.has(binds.ultimateArt)) {
        attackJustPressed = 'ultimate';
      } else if (just.has(binds.elementalSkill)) {
        attackJustPressed = 'elemental';
      } else if (just.has(binds.heavyAttack)) {
        attackJustPressed = 'heavy';
      } else if (just.has(binds.lightAttack)) {
        attackJustPressed = 'light';
      }

      let breakerJustPressed = just.has(binds.comboBreaker);
      if (playerNum === 1 && uiQueuedBreakerP1Ref.current) {
        breakerJustPressed = true;
        uiQueuedBreakerP1Ref.current = false;
      }

      return {
        moveX,
        jumpJustPressed: just.has(binds.jump),
        crouchHeld: held.has(binds.crouch),
        guardHeld: held.has(binds.guardParry),
        guardJustPressed: just.has(binds.guardParry),
        dashJustPressed: just.has(binds.dashStep),
        breakerJustPressed,
        attackJustPressed,
      };
    };

    const tick = () => {
      const now = performance.now();
      const rawDt = (now - lastTime) / 1000;
      lastTime = now;
      const dt = Math.min(Math.max(rawDt, 0.001), 0.05);
      elapsed += dt;

      arena.syncStageAndFighters(
        stageRef.current,
        p1FighterRef.current,
        p2FighterRef.current,
        simRef.current.hazards,
        simRef.current.p1.paletteIndex,
        simRef.current.p2.paletteIndex
      );

      soundEngine.syncBackgroundMusic(
        stageRef.current,
        simRef.current.stagePhase,
        screenStateRef.current === 'playing' && simRef.current.winner === 0,
        settingsRef.current
      );

      if (screenStateRef.current === 'playing') {
        simulationClock.current.advance(rawDt, (dt) => {
          const prevCountdownSec = Math.ceil(simRef.current.countdownTimer);
          const p1In = extractPlayerInput(1, dt);
          const p2In = extractPlayerInput(2, dt);
          keysJustPressedRef.current.clear();

          const ev = stepCombatSimulation(
            simRef.current,
            p1In,
            p2In,
            dt,
            modeRef.current
          );

          const nextCountdownSec = Math.ceil(simRef.current.countdownTimer);
          if (nextCountdownSec !== lastCountdownSec && nextCountdownSec > 0) {
            lastCountdownSec = nextCountdownSec;
            soundEngine.playCountdownTick(settingsRef.current, false);
          } else if (prevCountdownSec > 0 && nextCountdownSec === 0) {
            lastCountdownSec = 0;
            soundEngine.playCountdownTick(settingsRef.current, true);
          }

          if (ev.whiffTriggered) {
            soundEngine.playWhiff(settingsRef.current);
          }
          if (ev.voiceTriggered && ev.voiceFighterId) {
            soundEngine.playFighterVoice(
              settingsRef.current,
              ev.voiceFighterId,
              ev.voiceTriggered
            );
          }
          if (ev.superFreezeTriggered) {
            soundEngine.playSuperFlashChord(settingsRef.current);
            arena.addCameraTrauma(0.45);
          }
          if (ev.clashTriggered) {
            soundEngine.playClashThunder(settingsRef.current);
            arena.addCameraTrauma(0.65);
            arena.spawnBurstParticles(ev.impactX, ev.impactY, ev.impactZ, 0xffffff, 24);
            arena.spawnBurstParticles(ev.impactX, ev.impactY, ev.impactZ, 0xfacc15, 18);
          }
          if (ev.wallBounceTriggered) {
            soundEngine.playWallBounceSlam(settingsRef.current);
            arena.addCameraTrauma(0.55);
            arena.spawnBurstParticles(ev.impactX, ev.impactY, ev.impactZ, 0xf97316, 20);
          }
          if (ev.cancelConfirmTriggered) {
            soundEngine.playCancelConfirmClick(settingsRef.current);
          }
          if (ev.blockTriggered) {
            soundEngine.playBlockThud(settingsRef.current);
            arena.addCameraTrauma(0.18);
            arena.spawnBurstParticles(ev.impactX, 1.25, ev.impactZ, 0x38bdf8, 8);
          }
          if (ev.parryTriggered || ev.breakerTriggered || ev.stunlockEscapeTriggered) {
            soundEngine.playParryClang(settingsRef.current);
            arena.addCameraTrauma(0.55);
            arena.spawnBurstParticles(ev.impactX, 1.35, ev.impactZ, 0xfacc15, 22);
          }
          const activeAttackerId = ev.attackerId ?? simRef.current.p1.id;
          const attackerDef = FIGHTERS[activeAttackerId];
          const attackerState =
            simRef.current.p1.id === activeAttackerId
              ? simRef.current.p1
              : simRef.current.p2;
          const activePalette = getFighterPalette(
            activeAttackerId,
            attackerState.paletteIndex
          );
          const primaryHex =
            Number(activePalette.swatch[0].replace('#', '0x')) || 0x10b981;
          const accentHex =
            Number(activePalette.swatch[2].replace('#', '0x')) || 0xf59e0b;

          if (ev.impactSparkType) {
            arena.spawnImpactSpark(
              ev.impactX,
              ev.impactY,
              ev.impactZ,
              ev.impactSparkType,
              primaryHex
            );
          }
          if (ev.floorCrackTriggered) {
            arena.spawnFloorCrack(ev.impactX, ev.impactZ, primaryHex, ev.heavyHit ? 1.35 : 1.05);
          }
          if (ev.counterHitTriggered) {
            arena.addCameraTrauma(0.55);
            arena.spawnBurstParticles(ev.impactX, ev.impactY, ev.impactZ, 0xf43f5e, 18);
          }
          if (ev.punishTriggered) {
            soundEngine.playCancelConfirmClick(settingsRef.current);
            arena.spawnBurstParticles(ev.impactX, ev.impactY, ev.impactZ, 0x38bdf8, 14);
          }

          if (ev.launcherTriggered) {
            soundEngine.playLauncherBurst(settingsRef.current);
            arena.spawnBurstParticles(ev.impactX, 1.05, ev.impactZ, primaryHex, 14);
            arena.spawnBurstParticles(ev.impactX, 1.25, ev.impactZ, accentHex, 10);
          }
          if (ev.gustTriggered) {
            soundEngine.playElementalSignature(
              settingsRef.current,
              attackerDef.element
            );
            arena.spawnBurstParticles(
              ev.impactX,
              ev.impactY,
              ev.impactZ,
              primaryHex,
              14
            );
            arena.spawnBurstParticles(
              ev.impactX,
              ev.impactY + 0.15,
              ev.impactZ,
              accentHex,
              10
            );
          }
          if (ev.hitTriggered) {
            soundEngine.playImpact(settingsRef.current, ev.heavyHit);
            arena.addCameraTrauma(ev.heavyHit ? 0.65 : 0.28);
            arena.spawnBurstParticles(
              ev.impactX,
              ev.impactY,
              ev.impactZ,
              primaryHex,
              ev.heavyHit ? 16 : 8
            );
            arena.spawnBurstParticles(
              ev.impactX,
              ev.impactY + 0.1,
              ev.impactZ,
              accentHex,
              ev.heavyHit ? 12 : 6
            );
          }
          if (ev.hazardShattered) {
            soundEngine.playHazardShatter(settingsRef.current);
            arena.addCameraTrauma(0.75);
            arena.spawnBurstParticles(ev.impactX, 0.9, ev.impactZ, 0xf97316, 26);
          }
          if (ev.koTriggered && !koTransitionPending.current) {
            koTransitionPending.current = true;
            const finishedMatch = simRef.current;
            soundEngine.playKoFanfare(
              settingsRef.current,
              simRef.current.winner === 1
            );
            arena.addCameraTrauma(0.95);
            scheduleTransition(() => {
              if (simRef.current !== finishedMatch) return;
              koTransitionPending.current = false;
              setHudSnapshot(structuredClone(simRef.current));
              setScreenState('gameover');
            }, 520);
          }

          hudSyncAccumulator += dt;
          if (hudSyncAccumulator >= 0.08) {
            hudSyncAccumulator = 0;
            setHudSnapshot(structuredClone(simRef.current));
          }
        });
      } else {
        simulationClock.current.reset();
        keysJustPressedRef.current.clear();
      }

      arena.updateAndRender(
        simRef.current,
        screenStateRef.current,
        settingsRef.current,
        dt,
        elapsed
      );

      if (isSoftwareGl) {
        afterDraw(tick);
      } else {
        frameId = requestAnimationFrame(tick);
      }
    };

    frameId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frameId);
      clearTimeout(frameId);
      resizeObserver.disconnect();
      soundEngine.stopBackgroundMusic();
      arena.dispose();
    };
  }, []);

  // Global Keyboard & Focus-Loss Listeners
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (modalOpenRef.current || e.defaultPrevented) return;
      if (e.repeat && ['KeyM', 'KeyP', 'KeyR', 'Escape', 'Enter', 'Space'].includes(e.code)) return;

      if (e.code === 'KeyM') {
        setSettings((prev) => ({ ...prev, muted: !prev.muted }));
        return;
      }

      if (screenStateRef.current === 'title') {
        if (e.code === 'Enter' || e.code === 'Space') {
          e.preventDefault();
          openCourtyardSelect();
        }
        return;
      }

      if (screenStateRef.current === 'select') {
        return; // Handled by CharacterStageSelectScreen keyboard listener
      }

      if (screenStateRef.current === 'playing') {
        if (e.code === 'Escape' || e.code === 'KeyP') {
          e.preventDefault();
          keysHeldRef.current.clear();
          setHudSnapshot(structuredClone(simRef.current));
          setScreenState('paused');
          return;
        }
        if (e.code === 'KeyR') {
          e.preventDefault();
          startNewMatch(simRef.current.arcadeStageIndex, false, false);
          return;
        }
      } else if (screenStateRef.current === 'paused') {
        if (e.code === 'Escape' || e.code === 'KeyP') {
          e.preventDefault();
          setScreenState('playing');
          return;
        }
      } else if (screenStateRef.current === 'gameover') {
        if (e.code === 'Enter' || e.code === 'Space') {
          e.preventDefault();
          startNewMatch(simRef.current.arcadeStageIndex, false, true);
          return;
        }
      }

      if (screenStateRef.current !== 'playing') return;
      if ([...Object.values(settingsRef.current.p1Keys), ...Object.values(settingsRef.current.p2Keys)].includes(e.code)) {
        e.preventDefault();
      }
      if (!keysHeldRef.current.has(e.code)) {
        keysJustPressedRef.current.add(e.code);
      }
      keysHeldRef.current.add(e.code);
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      keysHeldRef.current.delete(e.code);
    };

    const handleBlurOrVisibility = () => {
      keysHeldRef.current.clear();
      keysJustPressedRef.current.clear();
      uiQueuedMoveP1Ref.current = null;
      uiQueuedBreakerP1Ref.current = false;
      simulationClock.current.reset();
      if (screenStateRef.current === 'playing') {
        screenStateRef.current = 'paused';
        setHudSnapshot(structuredClone(simRef.current));
        setScreenState('paused');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    window.addEventListener('blur', handleBlurOrVisibility);
    document.addEventListener('visibilitychange', handleBlurOrVisibility);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('blur', handleBlurOrVisibility);
      document.removeEventListener('visibilitychange', handleBlurOrVisibility);
    };
  }, [openCourtyardSelect, startNewMatch]);

  const handleToggleSkill = (fighterId: FighterId, skillId: string) => {
    soundEngine.playUiClick(settings);
    setP1Skills((prev) => {
      const next = toggleSkill(fighterId, prev[fighterId] || [], skillId);
      return { ...prev, [fighterId]: next };
    });
  };

  const handleResetSkills = (fighterId: FighterId) => {
    soundEngine.playUiClick(settings);
    setP1Skills((prev) => ({ ...prev, [fighterId]: [] }));
  };

  return (
    <main className="relative w-full h-full overflow-hidden bg-slate-950 select-none">
      {/* Isolated WebGL Canvas Container */}
      <div
        ref={canvasMountRef}
        data-testid="arena-canvas-container"
        className="fixed inset-0 w-full h-full z-0"
      />

      {/* Fade-to-Black Transition Curtain */}
      <div
        className={`fixed inset-0 z-50 bg-black pointer-events-none transition-opacity duration-200 ${
          blackCurtain ? 'opacity-100' : 'opacity-0'
        }`}
      />

      {/* Screen 1: Main Title Screen */}
      {screenState === 'title' && (
        <TitleScreen
          selectedMode={selectedMode}
          onSelectMode={(m) => {
            soundEngine.playUiClick(settings);
            setSelectedMode(m);
          }}
          p1Fighter={p1Fighter}
          p2Fighter={p2Fighter}
          selectedStage={selectedStage}
          onSelectStage={(s) => {
            soundEngine.playUiClick(settings);
            setSelectedStage(s);
          }}
          onStartMatch={openCourtyardSelect}
          onOpenRosterSkills={() => {
            soundEngine.playUiClick(settings);
            setShowRosterModal(true);
          }}
          onOpenSettings={() => {
            soundEngine.playUiClick(settings);
            setShowSettingsModal(true);
          }}
        />
      )}

      {/* Screen 2: Outdoor Courtyard 3D Lineup Character & Stage Select */}
      {screenState === 'select' && (
        <CharacterStageSelectScreen
          mode={selectedMode}
          selectedFighter={p1Fighter}
          selectedPalette={p1Palette}
          p2Fighter={p2Fighter}
          p2Palette={p2Palette}
          selectedStage={selectedStage}
          isFighterChosen={isFighterChosen}
          keyboardEnabled={!showRosterModal && !showSettingsModal && !blackCurtain}
          onSelectFighter={(id) => {
            soundEngine.playUiClick(settings);
            setP1Fighter(id);
          }}
          onSelectPalette={(palIdx) => {
            soundEngine.playUiClick(settings);
            setP1Palette(palIdx);
          }}
          onSelectP2Fighter={(id) => {
            soundEngine.playUiClick(settings);
            setP2Fighter(id);
          }}
          onSelectP2Palette={(palIdx) => {
            soundEngine.playUiClick(settings);
            setP2Palette(palIdx);
          }}
          onPreviewMove={(moveType) => {
            arenaRendererRef.current?.triggerLineupMovePreview(moveType);
          }}
          onSelectStage={(stg) => {
            soundEngine.playUiClick(settings);
            setSelectedStage(stg);
          }}
          onConfirmSelection={handleConfirmCharacterAndStage}
          onOpenSkillTree={() => {
            soundEngine.playUiClick(settings);
            setShowRosterModal(true);
          }}
          onBackToTitle={() => {
            cancelTransitions();
            soundEngine.playUiClick(settings);
            setBlackCurtain(true);
            scheduleTransition(() => {
              setScreenState('title');
              setBlackCurtain(false);
            }, 180);
          }}
        />
      )}

      {/* Screen 3: Arcade Tower & Matchup Loading Transition Screen */}
      {screenState === 'loading' && (
        <LoadingScreen
          p1Fighter={p1Fighter}
          p2Fighter={p2Fighter}
          stageId={selectedStage}
          tipIndex={tipIndex}
          mode={selectedMode}
          arcadeStageIndex={hudSnapshot.arcadeStageIndex}
        />
      )}

      {/* Screen 4: Active Combat HUD */}
      {(screenState === 'playing' || screenState === 'paused' || screenState === 'gameover') && (
        <CombatHUD
          snapshot={hudSnapshot}
          mode={selectedMode}
          stageId={selectedStage}
          settings={settings}
          onToggleMute={() =>
            setSettings((prev) => ({ ...prev, muted: !prev.muted }))
          }
          onPause={() => {
            keysHeldRef.current.clear();
            setHudSnapshot(structuredClone(simRef.current));
            setScreenState((prev) => (prev === 'paused' ? 'playing' : 'paused'));
          }}
          onRestart={() => startNewMatch(simRef.current.arcadeStageIndex, false, false)}
          onTriggerMove={(move) => {
            uiQueuedMoveP1Ref.current = move;
          }}
          onTriggerBreaker={() => {
            uiQueuedBreakerP1Ref.current = true;
          }}
        />
      )}

      {/* Subtle Minimalist Black Combat Tip / Rivalry Banner Bar on Match Entry */}
      {screenState === 'playing' && introBannerVisible && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-20 bg-black border border-slate-800 px-5 py-2 flex items-center gap-3 pointer-events-none">
          <span className="w-2 h-2 bg-amber-400 rotate-45 shrink-0" />
          <span className="text-xs font-mono text-slate-200 whitespace-nowrap">
            {rivalryBannerText || COMBAT_TIPS[tipIndex % COMBAT_TIPS.length]}
          </span>
        </div>
      )}

      {/* Screen 5 & 6: Pause Modal & Victory/Defeat Outcome Modal */}
      {(screenState === 'paused' || screenState === 'gameover') && (
        <PauseAndOutcomeModal
          kind={screenState}
          snapshot={hudSnapshot}
          mode={selectedMode}
          onResume={() => {
            soundEngine.playUiClick(settings);
            setScreenState('playing');
          }}
          onRestart={() => startNewMatch(simRef.current.arcadeStageIndex, false, true)}
          onNextStage={() =>
            startNewMatch(simRef.current.arcadeStageIndex + 1, true, true)
          }
          onOpenSettings={() => {
            soundEngine.playUiClick(settings);
            setShowSettingsModal(true);
          }}
          onReturnSelect={openCourtyardSelect}
          onReturnTitle={() => {
            cancelTransitions();
            soundEngine.playUiClick(settings);
            setBlackCurtain(true);
            scheduleTransition(() => {
              setScreenState('title');
              setBlackCurtain(false);
            }, 180);
          }}
        />
      )}

      {/* Visual Roster & Skill Tree Customizer */}
      {showRosterModal && (
        <FighterSkillModal
          selectedFighter={p1Fighter}
          unlockedSkillsByFighter={p1Skills}
          maxSkillPoints={MAX_SKILL_POINTS}
          onSelectFighter={(id) => {
            soundEngine.playUiClick(settings);
            setP1Fighter(id);
          }}
          onToggleSkill={handleToggleSkill}
          onResetSkills={handleResetSkills}
          onClose={() => {
            soundEngine.playUiClick(settings);
            setShowRosterModal(false);
          }}
        />
      )}

      {/* Options, Keybindings, Audio & Hitboxes Modal */}
      {showSettingsModal && (
        <SettingsModal
          settings={settings}
          onUpdateSettings={(next) => {
            setSettings(next);
          }}
          onClose={() => {
            soundEngine.playUiClick(settings);
            setShowSettingsModal(false);
          }}
        />
      )}
    </main>
  );
}
