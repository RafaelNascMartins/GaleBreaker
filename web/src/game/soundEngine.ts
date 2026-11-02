import { ElementType, FighterId, GameSettings, StageId, VoiceIntensity } from './types';

class ProceduralSoundEngine {
  private ctx: AudioContext | null = null;
  private bgmInterval: number | null = null;
  private bgmStep = 0;
  private currentBgmStage: StageId | null = null;
  private currentStagePhase: 1 | 2 | 3 = 1;
  private isBgmPlaying = false;
  private bgmSettings: GameSettings | null = null;

  private getContext(settings: GameSettings): AudioContext | null {
    if (settings.muted || settings.masterVolume <= 0) return null;
    if (typeof window === 'undefined') return null;
    if (!this.ctx) {
      const AudioCtx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  private pitchJitter(baseFreq: number): number {
    return baseFreq * (0.94 + Math.random() * 0.12);
  }

  public syncBackgroundMusic(
    stageId: StageId,
    stagePhase: 1 | 2 | 3,
    isPlaying: boolean,
    settings: GameSettings
  ) {
    this.bgmSettings = settings;
    this.currentStagePhase = stagePhase;
    if (!isPlaying || settings.muted || settings.masterVolume <= 0) {
      this.stopBackgroundMusic();
      return;
    }

    if (this.isBgmPlaying && this.currentBgmStage === stageId) {
      return;
    }

    this.stopBackgroundMusic();
    this.currentBgmStage = stageId;
    this.isBgmPlaying = true;
    this.bgmStep = 0;

    // Scales per stage:
    // zephyr_dojo: Japanese Hirajoshi pentatonic (E, F#, G, B, C, E)
    // molten_forge: Heavy Phrygian Dominant / industrial (D, Eb, F#, G, A, Bb)
    // storm_market: Arabic Hijaz scale (E, F, G#, A, B, C, D#)
    const scales: Record<StageId, number[]> = {
      zephyr_dojo: [164.81, 185.0, 196.0, 246.94, 261.63, 329.63, 370.0, 392.0],
      molten_forge: [146.83, 155.56, 185.0, 196.0, 220.0, 233.08, 293.66, 311.13],
      storm_market: [164.81, 174.61, 207.65, 220.0, 246.94, 261.63, 311.13, 329.63],
    };

    const bassRoots: Record<StageId, number> = {
      zephyr_dojo: 82.41,
      molten_forge: 73.42,
      storm_market: 82.41,
    };

    const patterns: Record<StageId, number[]> = {
      zephyr_dojo: [0, 2, 3, 5, 4, 3, 2, 1, 0, 3, 4, 7, 5, 4, 3, 2],
      molten_forge: [0, 0, 1, 0, 3, 2, 1, 0, 0, 0, 4, 3, 2, 1, 4, 1],
      storm_market: [0, 1, 2, 3, 4, 2, 3, 1, 0, 2, 4, 6, 5, 4, 2, 1],
    };

    const stepIntervalMs = 155;
    this.bgmInterval = window.setInterval(() => {
      const settings = this.bgmSettings;
      if (!settings) return;
      const ctx = this.getContext(settings);
      if (!ctx || settings.muted) return;

      const scale = scales[stageId];
      const pattern = patterns[stageId];
      const idx = this.bgmStep % pattern.length;
      const noteFreq = scale[pattern[idx]];
      const now = ctx.currentTime;
      const bgmVol = settings.masterVolume * 0.055 * (1 + (this.currentStagePhase - 1) * 0.2);

      // Lead synth pluck
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type =
        stageId === 'zephyr_dojo'
          ? 'triangle'
          : stageId === 'molten_forge'
          ? 'sawtooth'
          : 'sine';
      const phaseTranspose = this.currentStagePhase === 3 ? 1.12246 : 1.0; // +2 semitones at climax!
      osc.frequency.setValueAtTime(noteFreq * phaseTranspose, now);

      gain.gain.setValueAtTime(bgmVol, now);
      gain.gain.exponentialRampToValueAtTime(0.0008, now + 0.14);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.15);

      // Driving bass pulse on even steps (or every step in Climax Phase 3)
      if (idx % 2 === 0 || this.currentStagePhase >= 2) {
        const bassOsc = ctx.createOscillator();
        const bassGain = ctx.createGain();
        bassOsc.type = 'triangle';
        const root = bassRoots[stageId] * phaseTranspose;
        bassOsc.frequency.setValueAtTime(idx % 4 === 0 ? root : root * 1.5, now);
        bassGain.gain.setValueAtTime(bgmVol * 1.35, now);
        bassGain.gain.exponentialRampToValueAtTime(0.001, now + 0.13);
        bassOsc.connect(bassGain);
        bassGain.connect(ctx.destination);
        bassOsc.start(now);
        bassOsc.stop(now + 0.14);
      }

      this.bgmStep++;
    }, stepIntervalMs);
  }

  public stopBackgroundMusic() {
    if (this.bgmInterval !== null) {
      clearInterval(this.bgmInterval);
      this.bgmInterval = null;
    }
    this.isBgmPlaying = false;
    this.currentBgmStage = null;
  }

  public playUiClick(settings: GameSettings) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(520, now);
    osc.frequency.exponentialRampToValueAtTime(780, now + 0.045);

    const vol = settings.masterVolume * settings.sfxVolume * 0.14;
    gain.gain.setValueAtTime(vol, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.055);
  }

  public playCountdownTick(settings: GameSettings, isFight: boolean) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = isFight ? 'sawtooth' : 'triangle';
    osc.frequency.setValueAtTime(isFight ? 587.33 : 440, now);
    if (isFight) {
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.22);
    }

    const vol = settings.masterVolume * settings.announcerVolume * (isFight ? 0.28 : 0.18);
    gain.gain.setValueAtTime(vol, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + (isFight ? 0.28 : 0.14));

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + (isFight ? 0.3 : 0.15));
  }

  public playWhiff(settings: GameSettings) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(this.pitchJitter(240), now);
    osc.frequency.exponentialRampToValueAtTime(95, now + 0.08);

    const vol = settings.masterVolume * settings.sfxVolume * 0.16;
    gain.gain.setValueAtTime(vol, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.085);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.09);
  }

  public playImpact(settings: GameSettings, heavy: boolean) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;

    // Punch sub-bass thump
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = heavy ? 'sawtooth' : 'triangle';
    osc.frequency.setValueAtTime(this.pitchJitter(heavy ? 145 : 210), now);
    osc.frequency.exponentialRampToValueAtTime(
      heavy ? 36 : 55,
      now + (heavy ? 0.19 : 0.11)
    );

    const vol = settings.masterVolume * settings.sfxVolume * (heavy ? 0.36 : 0.24);
    gain.gain.setValueAtTime(vol, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + (heavy ? 0.2 : 0.12));

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + (heavy ? 0.21 : 0.13));

    // Crisp martial arts snap harmonic on heavy hits
    if (heavy) {
      const snap = ctx.createOscillator();
      const snapGain = ctx.createGain();
      snap.type = 'square';
      snap.frequency.setValueAtTime(this.pitchJitter(520), now);
      snap.frequency.exponentialRampToValueAtTime(110, now + 0.065);
      snapGain.gain.setValueAtTime(vol * 0.45, now);
      snapGain.gain.exponentialRampToValueAtTime(0.001, now + 0.07);
      snap.connect(snapGain);
      snapGain.connect(ctx.destination);
      snap.start(now);
      snap.stop(now + 0.075);
    }
  }

  public playLauncherBurst(settings: GameSettings) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(150, now);
    osc.frequency.exponentialRampToValueAtTime(680, now + 0.18);

    const vol = settings.masterVolume * settings.sfxVolume * 0.26;
    gain.gain.setValueAtTime(vol, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.21);
  }

  public playBlockThud(settings: GameSettings) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'square';
    osc.frequency.setValueAtTime(320, now);
    osc.frequency.exponentialRampToValueAtTime(135, now + 0.08);

    const vol = settings.masterVolume * settings.sfxVolume * 0.2;
    gain.gain.setValueAtTime(vol, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.095);
  }

  public playElementalSignature(settings: GameSettings, element: ElementType) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;
    const vol = settings.masterVolume * settings.sfxVolume * 0.24;

    if (element === 'wind') {
      this.playGustSwirl(settings);
    } else if (element === 'fire') {
      // Deep volcanic roar
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(130, now);
      osc.frequency.exponentialRampToValueAtTime(42, now + 0.28);
      gain.gain.setValueAtTime(vol, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.31);
    } else if (element === 'earth') {
      // Tectonic double-thud
      for (const offset of [0, 0.06]) {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(110, now + offset);
        osc.frequency.exponentialRampToValueAtTime(35, now + offset + 0.16);
        gain.gain.setValueAtTime(vol * 1.1, now + offset);
        gain.gain.exponentialRampToValueAtTime(0.001, now + offset + 0.18);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + offset);
        osc.stop(now + offset + 0.19);
      }
    } else {
      // High-frequency electric cyan zap
      const freqs = [920, 480, 1280, 640];
      freqs.forEach((f, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(f, now + idx * 0.03);
        gain.gain.setValueAtTime(vol * 0.75, now + idx * 0.03);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.03 + 0.05);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + idx * 0.03);
        osc.stop(now + idx * 0.03 + 0.055);
      });
    }
  }

  public playParryClang(settings: GameSettings) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;

    const freqs = [880, 1320, 1760];
    for (const f of freqs) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(this.pitchJitter(f), now);
      gain.gain.setValueAtTime(settings.masterVolume * settings.sfxVolume * 0.14, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.26);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.27);
    }
  }

  public playGustSwirl(settings: GameSettings) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(190, now);
    osc.frequency.exponentialRampToValueAtTime(540, now + 0.14);
    osc.frequency.exponentialRampToValueAtTime(140, now + 0.28);

    const vol = settings.masterVolume * settings.sfxVolume * 0.22;
    gain.gain.setValueAtTime(vol, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.29);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.3);
  }

  public playHazardShatter(settings: GameSettings) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;

    const freqs = [110, 165, 290, 410];
    freqs.forEach((f, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = idx % 2 === 0 ? 'square' : 'sawtooth';
      osc.frequency.setValueAtTime(this.pitchJitter(f), now + idx * 0.015);
      osc.frequency.exponentialRampToValueAtTime(42, now + 0.22);

      gain.gain.setValueAtTime(
        settings.masterVolume * settings.sfxVolume * 0.16,
        now + idx * 0.015
      );
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.24);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + idx * 0.015);
      osc.stop(now + 0.25);
    });
  }

  public playKoFanfare(settings: GameSettings, victory: boolean) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;
    const notes = victory ? [330, 440, 554.37, 659.25] : [311.13, 277.18, 246.94, 196];
    notes.forEach((freq, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, now + i * 0.09);
      gain.gain.setValueAtTime(
        settings.masterVolume * settings.announcerVolume * 0.22,
        now + i * 0.09
      );
      gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.09 + 0.32);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + i * 0.09);
      osc.stop(now + i * 0.09 + 0.34);
    });
  }

  public playFighterVoice(
    settings: GameSettings,
    fighterId: FighterId,
    intensity: VoiceIntensity
  ) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;

    // Distinct vocal fundamental + vowel formant filter frequencies (F1, F2) per martial artist
    const voiceProfiles: Record<
      FighterId,
      { f0: number; f1: number; f2: number; wave: OscillatorType }
    > = {
      kaze: { f0: 168, f1: 760, f2: 1340, wave: 'sawtooth' },
      ignis: { f0: 112, f1: 560, f2: 1020, wave: 'sawtooth' },
      tophia: { f0: 248, f1: 860, f2: 1720, wave: 'triangle' },
      volt: { f0: 196, f1: 720, f2: 1560, wave: 'sawtooth' },
    };

    const profile = voiceProfiles[fighterId];
    const baseF0 = this.pitchJitter(profile.f0);
    const dur =
      intensity === 'ultimate'
        ? 0.34
        : intensity === 'ko'
        ? 0.48
        : intensity === 'heavy'
        ? 0.21
        : intensity === 'hurt'
        ? 0.19
        : 0.12;

    const osc = ctx.createOscillator();
    const subOsc = ctx.createOscillator();
    osc.type = profile.wave;
    subOsc.type = 'triangle';

    if (intensity === 'light') {
      // Sharp martial arts Kiai ("Ha!" / "Sei!")
      osc.frequency.setValueAtTime(baseF0 * 1.05, now);
      osc.frequency.exponentialRampToValueAtTime(baseF0 * 1.28, now + 0.045);
      osc.frequency.exponentialRampToValueAtTime(baseF0 * 0.92, now + dur);
    } else if (intensity === 'heavy') {
      // Power strike shout ("Torya!" / "Oraa!")
      osc.frequency.setValueAtTime(baseF0 * 0.95, now);
      osc.frequency.exponentialRampToValueAtTime(baseF0 * 1.42, now + 0.08);
      osc.frequency.exponentialRampToValueAtTime(baseF0 * 1.05, now + dur);
    } else if (intensity === 'ultimate') {
      // Rising heroic battle cry
      osc.frequency.setValueAtTime(baseF0 * 0.9, now);
      osc.frequency.exponentialRampToValueAtTime(baseF0 * 1.65, now + 0.16);
      osc.frequency.exponentialRampToValueAtTime(baseF0 * 1.32, now + dur);
    } else if (intensity === 'hurt') {
      // Impact grunt ("Ugh!")
      osc.frequency.setValueAtTime(baseF0 * 1.15, now);
      osc.frequency.exponentialRampToValueAtTime(baseF0 * 0.72, now + dur);
    } else {
      // Dramatic K.O. echo cry
      osc.frequency.setValueAtTime(baseF0 * 1.35, now);
      osc.frequency.exponentialRampToValueAtTime(baseF0 * 0.58, now + dur);
    }

    subOsc.frequency.setValueAtTime(baseF0 * 0.5, now);
    subOsc.frequency.exponentialRampToValueAtTime(baseF0 * 0.45, now + dur);

    // Parallel Formant Filters (F1 & F2) to shape realistic vowel resonance
    const formant1 = ctx.createBiquadFilter();
    formant1.type = 'bandpass';
    formant1.frequency.setValueAtTime(profile.f1, now);
    formant1.frequency.exponentialRampToValueAtTime(
      intensity === 'hurt' || intensity === 'ko' ? profile.f1 * 0.78 : profile.f1 * 1.15,
      now + dur
    );
    formant1.Q.value = 5.5;

    const formant2 = ctx.createBiquadFilter();
    formant2.type = 'bandpass';
    formant2.frequency.setValueAtTime(profile.f2, now);
    formant2.Q.value = 6.5;

    const masterGain = ctx.createGain();
    const vol =
      settings.masterVolume *
      settings.announcerVolume *
      (intensity === 'ultimate' || intensity === 'ko' ? 0.28 : 0.2);
    masterGain.gain.setValueAtTime(0.001, now);
    masterGain.gain.linearRampToValueAtTime(vol, now + 0.018);
    masterGain.gain.exponentialRampToValueAtTime(0.001, now + dur);

    osc.connect(formant1);
    osc.connect(formant2);
    subOsc.connect(formant1);
    formant1.connect(masterGain);
    formant2.connect(masterGain);
    masterGain.connect(ctx.destination);

    osc.start(now);
    subOsc.start(now);
    osc.stop(now + dur + 0.02);
    subOsc.stop(now + dur + 0.02);
  }

  public playClashThunder(settings: GameSettings) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;
    const vol = settings.masterVolume * settings.sfxVolume * 0.32;

    // High-energy dual weapon/fist harmonic ring
    const ringFreqs = [660, 990, 1480, 1980];
    ringFreqs.forEach((f, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = idx % 2 === 0 ? 'sawtooth' : 'triangle';
      osc.frequency.setValueAtTime(this.pitchJitter(f), now);
      osc.frequency.exponentialRampToValueAtTime(f * 0.86, now + 0.32);
      gain.gain.setValueAtTime(vol * 0.45, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.34);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.35);
    });

    // Sub-bass thunder shockwave
    const sub = ctx.createOscillator();
    const subGain = ctx.createGain();
    sub.type = 'sawtooth';
    sub.frequency.setValueAtTime(160, now);
    sub.frequency.exponentialRampToValueAtTime(32, now + 0.28);
    subGain.gain.setValueAtTime(vol, now);
    subGain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
    sub.connect(subGain);
    subGain.connect(ctx.destination);
    sub.start(now);
    sub.stop(now + 0.31);
  }

  public playWallBounceSlam(settings: GameSettings) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;
    const vol = settings.masterVolume * settings.sfxVolume * 0.34;

    // Deep arena wall acoustic slam + rebound echo
    for (const [delay, pitchMult, gainMult] of [
      [0, 1.0, 1.0],
      [0.055, 0.78, 0.65],
    ] as const) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(135 * pitchMult, now + delay);
      osc.frequency.exponentialRampToValueAtTime(34, now + delay + 0.22);
      gain.gain.setValueAtTime(vol * gainMult, now + delay);
      gain.gain.exponentialRampToValueAtTime(0.001, now + delay + 0.24);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + delay);
      osc.stop(now + delay + 0.25);
    }
  }

  public playSuperFlashChord(settings: GameSettings) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;
    const vol = settings.masterVolume * settings.sfxVolume * 0.26;

    // Dramatic anime Super Freeze power chord + ascending shimmer
    const chord = [220, 329.63, 440, 659.25, 880];
    chord.forEach((f, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = idx < 2 ? 'sawtooth' : 'triangle';
      osc.frequency.setValueAtTime(f * 0.5, now);
      osc.frequency.exponentialRampToValueAtTime(f, now + 0.06);
      osc.frequency.exponentialRampToValueAtTime(f * 1.04, now + 0.38);
      gain.gain.setValueAtTime(vol * 0.55, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.41);
    });
  }

  public playCancelConfirmClick(settings: GameSettings) {
    const ctx = this.getContext(settings);
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, now);
    osc.frequency.exponentialRampToValueAtTime(1320, now + 0.04);

    const vol = settings.masterVolume * settings.sfxVolume * 0.14;
    gain.gain.setValueAtTime(vol, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.045);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.05);
  }
}

export const soundEngine = new ProceduralSoundEngine();
