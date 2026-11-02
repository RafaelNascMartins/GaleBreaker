import * as THREE from 'three';
import { FighterRuntimeState } from '../types';
import { applyPaletteToMesh } from './fighterBuilder';
import { RiggedFighterMesh } from './renderTypes';

export function updateFighterMesh(
  mesh: RiggedFighterMesh,
  fighter: FighterRuntimeState,
  elapsed: number,
  showOutlines: boolean
) {
  if (mesh.paletteIndex !== fighter.paletteIndex) {
    applyPaletteToMesh(mesh, fighter.paletteIndex);
  }

  mesh.root.position.set(fighter.x, 0, fighter.z);
  const baseYaw = fighter.facingRight ? Math.PI * 0.38 : -Math.PI * 0.38;
  mesh.root.rotation.y = baseYaw;

  mesh.shadowDisc.scale.setScalar(Math.max(0.45, 1 - fighter.y * 0.18));
  // Floor circle stays completely fixed on the ground (no automatic spinning or pulsing!)
  mesh.auraRing.rotation.z = 0;
  mesh.auraRing.position.y = 0.012;
  mesh.auraRing.scale.setScalar(1.0);

  for (const om of mesh.outlineMeshes) {
    om.visible = showOutlines;
  }

  const hasArmorGlow = fighter.armorHitsRemaining > 0;
  const hasWakeupInvuln = fighter.wakeupInvulnTimer > 0;
  for (let i = 0; i < mesh.hitFlashMaterials.length; i++) {
    mesh.hitFlashMaterials[i].color.setHex(
      fighter.hitFlashTimer > 0
        ? 0xffffff
        : hasWakeupInvuln && Math.floor(elapsed * 30) % 2 === 0
        ? 0xe0f2fe
        : (fighter.stunlockImmunityTimer > 0 || hasArmorGlow) &&
          Math.floor(elapsed * 20) % 2 === 0
        ? 0xfde047
        : mesh.baseColors[i]
    );
  }

  mesh.hipsGroup.position.set(0, 0.92 + fighter.y, 0);
  mesh.hipsGroup.rotation.set(0, 0, 0);
  mesh.hipsGroup.scale.set(1, 1, 1);

  mesh.torsoGroup.position.set(0, 0.14, 0);
  mesh.torsoGroup.rotation.set(0, 0, 0);
  mesh.torsoGroup.scale.set(1, 1, 1);

  mesh.headGroup.rotation.set(0, fighter.facingRight ? 0.22 : -0.22, 0);

  const windWave = Math.sin(elapsed * 8.5 + fighter.playerIndex) * 0.28;
  mesh.hairTailGroup.rotation.set(
    0.38 + Math.abs(fighter.vx) * 0.08 + windWave,
    0,
    windWave * 0.65
  );
  mesh.capeOrCoatGroup.rotation.set(
    0.22 + Math.abs(fighter.vx) * 0.09 + windWave * 0.9,
    0,
    windWave * 0.3
  );
  mesh.backAccessoryGroup.rotation.z = elapsed * 1.8;

  // Reset all limb upper, lower, and extremity (wrists/hands & ankles/feet) transforms
  mesh.leftArm.upper.rotation.set(0, 0, 0.22);
  mesh.leftArm.lower.rotation.set(-0.65, 0, 0);
  mesh.leftArm.lower.scale.set(1, 1, 1);
  mesh.leftArm.extremity.rotation.set(0, 0, 0);
  mesh.leftArm.extremity.scale.set(1, 1, 1);

  mesh.rightArm.upper.rotation.set(0, 0, -0.22);
  mesh.rightArm.lower.rotation.set(-0.65, 0, 0);
  mesh.rightArm.lower.scale.set(1, 1, 1);
  mesh.rightArm.extremity.rotation.set(0, 0, 0);
  mesh.rightArm.extremity.scale.set(1, 1, 1);

  mesh.leftLeg.upper.rotation.set(0, 0, 0.06);
  mesh.leftLeg.lower.rotation.set(0, 0, 0);
  mesh.leftLeg.lower.scale.set(1, 1, 1);
  mesh.leftLeg.extremity.rotation.set(0, 0, 0);
  mesh.leftLeg.extremity.scale.set(1, 1, 1);

  mesh.rightLeg.upper.rotation.set(0, 0, -0.06);
  mesh.rightLeg.lower.rotation.set(0, 0, 0);
  mesh.rightLeg.lower.scale.set(1, 1, 1);
  mesh.rightLeg.extremity.rotation.set(0, 0, 0);
  mesh.rightLeg.extremity.scale.set(1, 1, 1);

  const setBucketOpacity = (bucket: THREE.MeshBasicMaterial[], op: number) => {
    for (let i = 0; i < bucket.length; i++) {
      bucket[i].opacity = op;
    }
  };

  const shieldMat = mesh.guardShieldMesh.material as THREE.MeshBasicMaterial;
  const shockMat = mesh.groundShockRingMesh.material as THREE.MeshBasicMaterial;
  const superCylMat = mesh.superAuraCylMesh.material as THREE.MeshBasicMaterial;

  setBucketOpacity(mesh.slashVfxMats, 0);
  setBucketOpacity(mesh.blastVfxMats, 0);
  setBucketOpacity(mesh.launcherVfxMats, 0);
  setBucketOpacity(
    mesh.handAuraMats,
    fighter.action === 'ko'
      ? 0
      : fighter.cancelFlashTimer > 0
      ? 0.98
      : fighter.isOvercharged
      ? 0.48
      : fighter.meter >= 50
      ? 0.34
      : 0.16
  );
  setBucketOpacity(mesh.footAuraMats, 0);

  shieldMat.opacity = 0;
  shockMat.opacity = 0;
  mesh.slashEffectGroup.scale.setScalar(1);
  mesh.slashEffectGroup.rotation.set(0, 0, 0);
  mesh.slashEffectGroup.position.set(0, 0.35, 0.55);
  mesh.blastEffectGroup.scale.set(1, 1, 1);
  mesh.blastEffectGroup.rotation.set(0, 0, 0);
  mesh.blastEffectGroup.position.set(0, 0.32, 1.35);
  mesh.launcherEffectGroup.scale.set(1, 1, 1);
  mesh.launcherEffectGroup.rotation.set(0, 0, 0);
  mesh.launcherEffectGroup.position.set(0, 1.25, 0.95);

  const auraSpin = elapsed * 14.5;
  mesh.leftHandAura.rotation.set(auraSpin * 0.7, auraSpin, 0);
  mesh.rightHandAura.rotation.set(-auraSpin * 0.7, -auraSpin, 0);
  mesh.kickFootAura.rotation.set(0, auraSpin * 1.2, auraSpin * 0.8);

  const cancelScaleBoost = fighter.cancelFlashTimer > 0 ? 1.52 : 1.0;
  mesh.leftHandAura.scale.setScalar(cancelScaleBoost);
  mesh.rightHandAura.scale.setScalar(cancelScaleBoost);
  mesh.kickFootAura.scale.setScalar(1.0);

  // Pulse Super Aura Cylinder when Fighter has >= 50% Meter or is Overcharged Boss (floor auraRing stays fixed!)
  if ((fighter.meter >= 50 || fighter.isOvercharged) && fighter.action !== 'ko') {
    const baseOp = fighter.isOvercharged ? 0.26 : 0.16;
    superCylMat.opacity = baseOp + Math.sin(elapsed * 10 + fighter.playerIndex) * 0.08;
    mesh.superAuraCylMesh.rotation.y = elapsed * (fighter.isOvercharged ? 4.8 : 3.2);
    mesh.superAuraCylMesh.position.y = 0.92 + fighter.y;
  } else {
    superCylMat.opacity = 0;
  }

  const totalF = Math.max(1, fighter.actionTotalFrames);
  const progress = Math.max(0, Math.min(1, 1 - fighter.actionTimerFrames / totalF));
  // Item 14: Quantized "Anime Step" timing (15fps stepped holds on 60fps physics) for crisp hand-drawn keyframe feel!
  const steppedElapsed = Math.floor(elapsed * 15) / 15;

  if (fighter.action === 'idle') {
    const t = steppedElapsed * (fighter.id === 'volt' ? 9.2 : fighter.id === 'kaze' ? 6.0 : 4.8);
    const s = Math.sin(t);
    const c = Math.cos(t);

    if (fighter.id === 'kaze') {
      const breath = s * 0.065;
      mesh.hipsGroup.position.y += breath;
      mesh.hipsGroup.rotation.y = -0.35 + c * 0.08;
      mesh.torsoGroup.scale.set(1 - s * 0.04, 1 + s * 0.06, 1 - s * 0.04);
      mesh.torsoGroup.rotation.set(0.08 + s * 0.06, -0.32 + c * 0.1, s * 0.05);
      mesh.headGroup.rotation.set(
        -s * 0.06,
        (fighter.facingRight ? 0.35 : -0.35) - c * 0.08,
        0
      );

      mesh.leftArm.upper.rotation.set(-0.55 + c * 0.18, 0.25, 0.42 + s * 0.1);
      mesh.leftArm.lower.rotation.set(-1.15 + s * 0.15, 0, 0);
      mesh.leftArm.extremity.rotation.set(0.45 + c * 0.25, 0, -0.3);

      mesh.rightArm.upper.rotation.set(-0.95 + s * 0.2, -0.2, -0.35 - c * 0.1);
      mesh.rightArm.lower.rotation.set(-0.75 + c * 0.18, 0, 0);
      mesh.rightArm.extremity.rotation.set(-0.35 + s * 0.25, 0, 0.25);

      mesh.leftLeg.upper.rotation.set(-0.38 - s * 0.08, 0, 0.16);
      mesh.leftLeg.lower.rotation.set(0.62 + s * 0.14, 0, 0);
      mesh.leftLeg.extremity.rotation.set(-0.24 - s * 0.1, 0, 0);

      mesh.rightLeg.upper.rotation.set(0.34 + s * 0.08, 0, -0.14);
      mesh.rightLeg.lower.rotation.set(0.38 + c * 0.1, 0, 0);
      mesh.rightLeg.extremity.rotation.set(-0.18, 0, 0);
    } else if (fighter.id === 'ignis') {
      const weave = Math.sin(t * 1.15);
      const drop = Math.abs(c) * 0.09;
      mesh.hipsGroup.position.y -= drop;
      mesh.hipsGroup.rotation.y = weave * 0.22;
      mesh.torsoGroup.scale.set(1.06 + s * 0.05, 0.95 - s * 0.04, 1.06 + s * 0.05);
      mesh.torsoGroup.rotation.set(
        0.24 + Math.abs(s) * 0.08,
        weave * 0.28,
        -weave * 0.12
      );
      mesh.headGroup.rotation.set(
        -0.14,
        fighter.facingRight ? 0.18 : -0.18,
        weave * 0.1
      );

      mesh.leftArm.upper.rotation.set(-1.15 + weave * 0.25, 0.38, 0.28);
      mesh.leftArm.lower.rotation.set(-1.58 + c * 0.15, 0, 0);
      mesh.leftArm.extremity.rotation.set(0.35, weave * 0.4, 0);
      mesh.leftArm.extremity.scale.setScalar(1.08 + Math.max(0, s) * 0.12);

      mesh.rightArm.upper.rotation.set(-1.05 - weave * 0.25, -0.38, -0.28);
      mesh.rightArm.lower.rotation.set(-1.55 - c * 0.15, 0, 0);
      mesh.rightArm.extremity.rotation.set(0.35, -weave * 0.4, 0);
      mesh.rightArm.extremity.scale.setScalar(1.08 + Math.max(0, -s) * 0.12);

      mesh.leftLeg.upper.rotation.set(-0.42 - drop * 1.5, 0, 0.2);
      mesh.leftLeg.lower.rotation.set(0.68 + drop * 2.2, 0, 0);
      mesh.leftLeg.extremity.rotation.set(-0.26 + weave * 0.15, 0, 0);

      mesh.rightLeg.upper.rotation.set(0.32 - drop * 1.2, 0, -0.2);
      mesh.rightLeg.lower.rotation.set(0.45 + drop * 1.8, 0, 0);
      mesh.rightLeg.extremity.rotation.set(-0.22 - weave * 0.15, 0, 0);
    } else if (fighter.id === 'tophia') {
      const horsePulse = s * 0.05;
      mesh.hipsGroup.position.y -= 0.16 - horsePulse;
      mesh.hipsGroup.rotation.y = c * 0.12;
      mesh.torsoGroup.scale.set(1.04 - s * 0.03, 0.96 + s * 0.04, 1.04);
      mesh.torsoGroup.rotation.set(0.06, -0.22 + s * 0.12, c * 0.06);

      mesh.leftLeg.upper.rotation.set(-0.62 + horsePulse, 0, 0.36);
      mesh.leftLeg.lower.rotation.set(0.88 - horsePulse, 0, 0);
      mesh.leftLeg.extremity.rotation.set(-0.26, 0, -0.18);

      mesh.rightLeg.upper.rotation.set(0.52 - horsePulse, 0, -0.36);
      mesh.rightLeg.lower.rotation.set(0.76 + horsePulse, 0, 0);
      mesh.rightLeg.extremity.rotation.set(-0.24, 0, 0.18);

      mesh.leftArm.upper.rotation.set(-0.55 + s * 0.14, 0.32, 0.58);
      mesh.leftArm.lower.rotation.set(-0.95 + c * 0.14, 0, 0);
      mesh.leftArm.extremity.rotation.set(-0.65 + s * 0.25, 0, -0.35);

      mesh.rightArm.upper.rotation.set(-0.85 - s * 0.14, -0.28, -0.52);
      mesh.rightArm.lower.rotation.set(-0.72 - c * 0.14, 0, 0);
      mesh.rightArm.extremity.rotation.set(-0.68 - s * 0.25, 0, 0.35);
    } else {
      const hop = Math.abs(s) * 0.11;
      mesh.hipsGroup.position.y += hop - 0.04;
      mesh.hipsGroup.rotation.y = 0.38 + c * 0.16;
      mesh.torsoGroup.scale.set(
        0.96 + Math.abs(s) * 0.06,
        1.06 - Math.abs(s) * 0.08,
        1
      );
      mesh.torsoGroup.rotation.set(0.32 + c * 0.08, 0.35 + s * 0.15, c * 0.08);
      mesh.headGroup.rotation.set(
        -0.18,
        fighter.facingRight ? 0.12 : -0.12,
        -c * 0.08
      );

      mesh.rightArm.upper.rotation.set(-0.78 + s * 0.24, -0.25, -0.45);
      mesh.rightArm.lower.rotation.set(-1.25 + c * 0.2, 0, 0);
      mesh.rightArm.extremity.rotation.set(0.35, s * 0.65, 0.2);

      mesh.leftArm.upper.rotation.set(0.48 - s * 0.24, 0.2, 0.48);
      mesh.leftArm.lower.rotation.set(-1.05 - c * 0.2, 0, 0);
      mesh.leftArm.extremity.rotation.set(-0.25, -s * 0.65, -0.2);

      mesh.leftLeg.upper.rotation.set(-0.48 - hop * 1.4, 0, 0.16);
      mesh.leftLeg.lower.rotation.set(0.75 + hop * 1.8, 0, 0);
      mesh.leftLeg.extremity.rotation.set(0.32 - hop * 2.2, 0, 0);

      mesh.rightLeg.upper.rotation.set(0.42 + hop * 1.2, 0, -0.16);
      mesh.rightLeg.lower.rotation.set(0.52 + hop * 1.4, 0, 0);
      mesh.rightLeg.extremity.rotation.set(0.28 - hop * 2.0, 0, 0);
    }
  } else if (fighter.action === 'walk') {
    // Item 14: Quantize walk cycle into discrete anime keyframe steps
    const p = Math.floor(fighter.walkCyclePhase * 3.6) / 3.6;
    const swing = Math.sin(p) * 0.96;
    const cosP = Math.cos(p);
    const kneeL = Math.max(0, -cosP) * 1.05;
    const kneeR = Math.max(0, cosP) * 1.05;

    const forwardLean =
      fighter.id === 'volt'
        ? 0.36
        : fighter.id === 'ignis'
        ? 0.25
        : fighter.id === 'tophia'
        ? 0.1
        : 0.18;
    const bounce = Math.abs(cosP) * (fighter.id === 'volt' ? 0.12 : 0.08);
    mesh.hipsGroup.position.y += bounce;
    mesh.hipsGroup.rotation.y = -swing * 0.28;
    mesh.hipsGroup.rotation.z = cosP * 0.08;
    mesh.torsoGroup.rotation.set(forwardLean, -swing * 0.48, -cosP * 0.1);
    mesh.torsoGroup.scale.set(1 - bounce * 0.3, 1 + bounce * 0.4, 1);

    mesh.leftLeg.upper.rotation.set(swing, 0, 0.08);
    mesh.leftLeg.lower.rotation.set(kneeL, 0, 0);
    mesh.leftLeg.extremity.rotation.set(-swing * 0.45 + kneeL * 0.3, 0, 0);

    mesh.rightLeg.upper.rotation.set(-swing, 0, -0.08);
    mesh.rightLeg.lower.rotation.set(kneeR, 0, 0);
    mesh.rightLeg.extremity.rotation.set(swing * 0.45 + kneeR * 0.3, 0, 0);

    mesh.leftArm.upper.rotation.set(-0.48 - swing * 0.85, 0, 0.28);
    mesh.leftArm.lower.rotation.set(-1.15 - Math.max(0, swing) * 0.35, 0, 0);
    mesh.leftArm.extremity.rotation.set(swing * 0.5, 0, 0);

    mesh.rightArm.upper.rotation.set(-0.48 + swing * 0.85, 0, -0.28);
    mesh.rightArm.lower.rotation.set(-1.15 - Math.max(0, -swing) * 0.35, 0, 0);
    mesh.rightArm.extremity.rotation.set(-swing * 0.5, 0, 0);
  } else if (fighter.action === 'crouch') {
    const breathe = Math.sin(elapsed * 7) * 0.04;
    mesh.hipsGroup.position.y = 0.48 + breathe;
    mesh.hipsGroup.scale.set(1.08, 0.9, 1.08);
    mesh.torsoGroup.rotation.set(0.38, -0.22, 0);
    mesh.headGroup.rotation.set(-0.22, fighter.facingRight ? 0.25 : -0.25, 0);

    mesh.leftLeg.upper.rotation.set(-1.38, 0, 0.26);
    mesh.leftLeg.lower.rotation.set(1.72, 0, 0);
    mesh.leftLeg.extremity.rotation.set(-0.38, 0, 0);

    mesh.rightLeg.upper.rotation.set(-1.12, 0, -0.26);
    mesh.rightLeg.lower.rotation.set(1.55, 0, 0);
    mesh.rightLeg.extremity.rotation.set(-0.42, 0, 0);

    mesh.leftArm.upper.rotation.set(-0.95, 0.25, 0.32);
    mesh.leftArm.lower.rotation.set(-1.35, 0, 0);
    mesh.leftArm.extremity.rotation.set(0.35, 0, 0);

    mesh.rightArm.upper.rotation.set(-1.05, -0.25, -0.32);
    mesh.rightArm.lower.rotation.set(-1.35, 0, 0);
    mesh.rightArm.extremity.rotation.set(0.35, 0, 0);
  } else if (fighter.action === 'jump') {
    const airStretch = Math.max(-0.15, Math.min(0.18, fighter.vy * 0.018));
    mesh.torsoGroup.scale.set(
      1 - airStretch * 0.5,
      1 + airStretch,
      1 - airStretch * 0.5
    );
    mesh.torsoGroup.rotation.set(0.28 - fighter.vy * 0.02, -0.2, 0);

    mesh.leftLeg.upper.rotation.set(-1.25, 0, 0.16);
    mesh.leftLeg.lower.rotation.set(1.55, 0, 0);
    mesh.leftLeg.extremity.rotation.set(0.55, 0, 0);

    mesh.rightLeg.upper.rotation.set(-0.68, 0, -0.16);
    mesh.rightLeg.lower.rotation.set(0.72, 0, 0);
    mesh.rightLeg.extremity.rotation.set(0.48, 0, 0);

    mesh.leftArm.upper.rotation.set(-1.35, 0, 0.58);
    mesh.leftArm.lower.rotation.set(-0.75, 0, 0);
    mesh.leftArm.extremity.rotation.set(-0.4, 0, 0);

    mesh.rightArm.upper.rotation.set(-0.92, 0, -0.58);
    mesh.rightArm.lower.rotation.set(-0.85, 0, 0);
    mesh.rightArm.extremity.rotation.set(-0.4, 0, 0);
  } else if (fighter.action === 'dash') {
    mesh.hipsGroup.position.y = 0.72;
    mesh.torsoGroup.scale.set(0.9, 1.14, 1.12);
    mesh.torsoGroup.rotation.set(0.68, 0, 0);
    mesh.headGroup.rotation.set(-0.38, fighter.facingRight ? 0.2 : -0.2, 0);

    mesh.leftArm.upper.rotation.set(0.95, 0, 0.38);
    mesh.leftArm.lower.rotation.set(-0.35, 0, 0);
    mesh.leftArm.extremity.rotation.set(0.45, 0, 0);

    mesh.rightArm.upper.rotation.set(-1.35, 0, -0.25);
    mesh.rightArm.lower.rotation.set(-0.95, 0, 0);
    mesh.rightArm.extremity.rotation.set(0.35, 0, 0);

    mesh.leftLeg.upper.rotation.set(-0.98, 0, 0);
    mesh.leftLeg.lower.rotation.set(1.18, 0, 0);
    mesh.leftLeg.extremity.rotation.set(-0.35, 0, 0);

    mesh.rightLeg.upper.rotation.set(0.88, 0, 0);
    mesh.rightLeg.lower.rotation.set(0.25, 0, 0);
    mesh.rightLeg.extremity.rotation.set(0.65, 0, 0);
  } else if (fighter.action === 'breaker') {
    mesh.torsoGroup.scale.set(1.18, 1.12, 1.18);
    mesh.torsoGroup.rotation.x = -0.48;
    mesh.headGroup.rotation.x = -0.35;
    mesh.leftArm.upper.rotation.set(-1.55, 0, 1.48);
    mesh.leftArm.lower.rotation.set(-0.1, 0, 0);
    mesh.leftArm.extremity.rotation.set(-0.65, 0, 0);
    mesh.leftArm.extremity.scale.setScalar(1.3);

    mesh.rightArm.upper.rotation.set(-1.55, 0, -1.48);
    mesh.rightArm.lower.rotation.set(-0.1, 0, 0);
    mesh.rightArm.extremity.rotation.set(-0.65, 0, 0);
    mesh.rightArm.extremity.scale.setScalar(1.3);

    mesh.leftLeg.upper.rotation.set(-0.55, 0, 0.35);
    mesh.rightLeg.upper.rotation.set(0.45, 0, -0.35);
    setBucketOpacity(mesh.handAuraMats, 0.96);
    setBucketOpacity(mesh.slashVfxMats, 0.95);
    setBucketOpacity(mesh.blastVfxMats, 0.88);
    setBucketOpacity(mesh.launcherVfxMats, 0.85);
    mesh.slashEffectGroup.scale.setScalar(1.8);
    mesh.slashEffectGroup.rotation.z = elapsed * 18;
  } else if (fighter.action === 'guard' || fighter.action === 'parry') {
    if (fighter.crouching) {
      mesh.hipsGroup.position.y = 0.52;
      mesh.leftLeg.upper.rotation.set(-1.25, 0, 0.2);
      mesh.leftLeg.lower.rotation.set(1.52, 0, 0);
      mesh.leftLeg.extremity.rotation.set(-0.3, 0, 0);
      mesh.rightLeg.upper.rotation.set(-1.02, 0, -0.2);
      mesh.rightLeg.lower.rotation.set(1.4, 0, 0);
      mesh.rightLeg.extremity.rotation.set(-0.35, 0, 0);
      mesh.guardShieldMesh.position.set(0, 0.18, 0.65);
    } else {
      mesh.leftLeg.upper.rotation.set(-0.38, 0, 0.18);
      mesh.leftLeg.lower.rotation.set(0.55, 0, 0);
      mesh.leftLeg.extremity.rotation.set(-0.2, 0, 0);
      mesh.rightLeg.upper.rotation.set(0.42, 0, -0.18);
      mesh.rightLeg.lower.rotation.set(0.48, 0, 0);
      mesh.rightLeg.extremity.rotation.set(-0.25, 0, 0);
      mesh.guardShieldMesh.position.set(0, 0.42, 0.65);
    }
    mesh.torsoGroup.rotation.set(-0.14, -0.18, 0);
    mesh.leftArm.upper.rotation.set(-1.25, 0.62, 0.25);
    mesh.leftArm.lower.rotation.set(-1.52, 0, 0);
    mesh.leftArm.extremity.rotation.set(-0.45, 0, 0);
    mesh.rightArm.upper.rotation.set(-1.25, -0.62, -0.25);
    mesh.rightArm.lower.rotation.set(-1.52, 0, 0);
    mesh.rightArm.extremity.rotation.set(-0.45, 0, 0);
    shieldMat.opacity = 0.72;
    mesh.guardShieldMesh.rotation.z = elapsed * 4.5;
    if (fighter.action === 'parry') {
      setBucketOpacity(mesh.slashVfxMats, 0.72);
      setBucketOpacity(mesh.handAuraMats, 0.85);
      mesh.slashEffectGroup.rotation.set(0, 0, elapsed * 14);
    }
  } else if (
    fighter.action === 'startup' ||
    fighter.action === 'active' ||
    fighter.action === 'recovery'
  ) {
    const style = fighter.currentMove?.animStyle || 'jab';
    const isStartup = fighter.action === 'startup';
    const isActive = fighter.action === 'active';
    // Item 11: "3-Keyframes Snap" — lock immediately into full coiled windup on frame 1 of startup (with muscular tension tremor),
    // jump in 1 frame to full impact extension on active, and return in 2 discrete stepped recovery keyframes!
    const tension = Math.sin(elapsed * 58) * 0.04;
    const isSmearFrame = isActive && fighter.actionTotalFrames - fighter.actionTimerFrames <= 3;
    const smearBoost = isSmearFrame ? 1.42 : 1.0;
    const stepR = progress < 0.52 ? 0.76 : 0.24;

    if (isStartup) {
      mesh.torsoGroup.scale.set(1.16, 0.84, 1.14);
      setBucketOpacity(mesh.handAuraMats, 0.85);
      mesh.leftHandAura.scale.setScalar(1.25);
      mesh.rightHandAura.scale.setScalar(1.25);

      // Item 14: 3D Intention Telegraph Glow during Startup
      const hitHeight = fighter.currentMove?.hitHeight;
      if (hitHeight === 'low') {
        // Low Launcher / Sweep Telegraph: Coral-red ground sweep ring warns player to Crouch-Block!
        shockMat.color.setHex(0xf43f5e);
        shockMat.opacity = 0.78;
        mesh.groundShockRingMesh.scale.setScalar(0.95);
      } else if (hitHeight === 'overhead') {
        // Overhead Telegraph: Golden-amber high halo & foot/hand flare warns player to Stand-Block!
        shockMat.color.setHex(0xf59e0b);
        setBucketOpacity(mesh.footAuraMats, 0.9);
        mesh.kickFootAura.scale.setScalar(1.48);
      }
    } else if (isActive) {
      mesh.torsoGroup.scale.set(0.84, 1.24, 1.2);
      setBucketOpacity(mesh.handAuraMats, 0.98);
      mesh.leftHandAura.scale.setScalar(
        fighter.cancelFlashTimer > 0 ? 1.72 : 1.48
      );
      mesh.rightHandAura.scale.setScalar(
        fighter.cancelFlashTimer > 0 ? 1.72 : 1.48
      );
    } else {
      mesh.torsoGroup.scale.set(1 - stepR * 0.08, 1 + stepR * 0.1, 1);
      setBucketOpacity(
        mesh.handAuraMats,
        fighter.cancelFlashTimer > 0 ? 0.98 : 0.25 + stepR * 0.55
      );
      // Item 11: Off-balance posture during Whiff Recovery so player visually sees the Punish window!
      if (fighter.whiffRecoveryActive) {
        mesh.torsoGroup.rotation.x += 0.34 * stepR;
        mesh.headGroup.rotation.x += 0.28 * stepR;
      }
    }

    if (style === 'low_sweep') {
      // Item 3: Crouch Heavy Sweep [S + K] — deep coiled low crouch snapping into a wide 1.68x leg sweep!
      if (isStartup) {
        mesh.hipsGroup.position.y = 0.38;
        mesh.hipsGroup.rotation.y = -0.95 + tension;
        mesh.torsoGroup.rotation.set(0.64, -0.88 + tension, 0.24);
        mesh.rightLeg.upper.rotation.set(0.75, 0, -0.45);
        mesh.rightLeg.lower.rotation.set(1.55, 0, 0);
        mesh.leftLeg.upper.rotation.set(-1.48, 0, 0.35);
        mesh.leftLeg.lower.rotation.set(1.82, 0, 0);
        mesh.leftArm.upper.rotation.set(-0.85, 0.35, 0.55);
        mesh.rightArm.upper.rotation.set(0.95, -0.35, -0.55);
        setBucketOpacity(mesh.footAuraMats, 0.88);
      } else if (isActive) {
        mesh.hipsGroup.position.y = 0.32;
        mesh.hipsGroup.rotation.y = 0.92;
        mesh.torsoGroup.rotation.set(-0.38, 1.05, -0.32);
        mesh.rightLeg.upper.rotation.set(-1.52, 0.38, -0.68);
        mesh.rightLeg.lower.rotation.set(0.02, 0, 0);
        mesh.rightLeg.lower.scale.set(1.2, 1.32, 1.2);
        mesh.rightLeg.extremity.rotation.set(0.55, 0, -0.35);
        mesh.rightLeg.extremity.scale.setScalar(1.68);
        mesh.leftLeg.upper.rotation.set(-1.42, 0, 0.38);
        mesh.leftLeg.lower.rotation.set(1.75, 0, 0);
        mesh.leftArm.upper.rotation.set(0.85, 0, 0.72);
        mesh.rightArm.upper.rotation.set(-1.15, 0, -0.65);

        setBucketOpacity(mesh.footAuraMats, 0.98);
        mesh.kickFootAura.scale.setScalar(1.68);
        setBucketOpacity(mesh.slashVfxMats, 0.98);
        mesh.slashEffectGroup.position.set(0, 0.18, 0.72);
        mesh.slashEffectGroup.rotation.set(Math.PI * 0.48, 0, progress * 3.8);
        mesh.slashEffectGroup.scale.setScalar(1.45 * smearBoost);
        shockMat.color.setHex(0xf43f5e);
        shockMat.opacity = 0.92 * (1 - progress * 0.5);
        mesh.groundShockRingMesh.scale.setScalar(1.1 + progress * 1.4);
      } else {
        mesh.hipsGroup.position.y = 0.42;
        mesh.hipsGroup.rotation.y = 0.92 * stepR;
        mesh.torsoGroup.rotation.set(-0.28 * stepR, 0.85 * stepR, 0);
        mesh.rightLeg.upper.rotation.x = -1.35 * stepR;
        mesh.rightLeg.extremity.scale.setScalar(1 + 0.45 * stepR);
      }
    } else if (style === 'low_punch') {
      if (isStartup) {
        mesh.hipsGroup.position.y = 0.42;
        mesh.hipsGroup.rotation.y = -0.88 + tension;
        mesh.torsoGroup.rotation.set(0.64, -0.78 + tension, 0.22);
        mesh.rightArm.upper.rotation.set(0.98, -0.42, -0.58);
        mesh.rightArm.lower.rotation.set(-1.82, 0, 0);
        mesh.rightArm.extremity.rotation.set(0.72, 0, 0);
        mesh.leftArm.upper.rotation.set(-0.72, 0.35, 0.52);
        mesh.leftLeg.upper.rotation.set(-1.46, 0, 0.28);
        mesh.leftLeg.lower.rotation.set(1.82, 0, 0);
        mesh.leftLeg.extremity.rotation.set(-0.4, 0, 0);
        mesh.rightLeg.upper.rotation.set(-1.12, 0, -0.28);
        mesh.rightLeg.lower.rotation.set(1.56, 0, 0);
        mesh.rightLeg.extremity.rotation.set(0.35, 0, 0);
      } else if (isActive) {
        mesh.hipsGroup.position.y = 0.82;
        mesh.hipsGroup.rotation.y = 0.78;
        mesh.torsoGroup.rotation.set(-0.42, 0.98, -0.26);
        mesh.headGroup.rotation.set(-0.36, 0.28, 0);
        mesh.rightArm.upper.rotation.set(-2.65, -0.24, 0.14);
        mesh.rightArm.lower.rotation.set(-0.04, 0, 0);
        mesh.rightArm.lower.scale.set(1.18, 1.28, 1.18);
        mesh.rightArm.extremity.rotation.set(-0.55, 0.45, 0);
        mesh.rightArm.extremity.scale.setScalar(1.62);
        mesh.leftArm.upper.rotation.set(0.82, 0, 0.58);
        mesh.leftArm.lower.rotation.set(-0.95, 0, 0);
        mesh.leftLeg.upper.rotation.set(-0.68, 0, 0.22);
        mesh.leftLeg.lower.rotation.set(0.85, 0, 0);
        mesh.leftLeg.extremity.rotation.set(0.52, 0, 0);
        mesh.rightLeg.upper.rotation.set(0.55, 0, -0.22);
        mesh.rightLeg.lower.rotation.set(0.42, 0, 0);
        mesh.rightLeg.extremity.rotation.set(0.62, 0, 0);

        setBucketOpacity(mesh.slashVfxMats, 0.98);
        mesh.slashEffectGroup.rotation.set(0.55, 0, progress * 3.2);
        mesh.slashEffectGroup.scale.setScalar(1.32 * smearBoost);

        setBucketOpacity(mesh.launcherVfxMats, 0.92 * (1 - progress * 0.3));
        mesh.launcherEffectGroup.scale.set(
          0.92 + progress * 0.48,
          0.72 + progress * 1.15,
          0.92 + progress * 0.48
        );
        mesh.launcherEffectGroup.position.y = 1.0 + progress * 0.65;
        mesh.launcherEffectGroup.rotation.y = progress * 4.5;

        shockMat.opacity = 0.9 * (1 - progress);
        mesh.groundShockRingMesh.scale.setScalar(0.85 + progress * 1.65);
      } else {
        mesh.hipsGroup.rotation.y = 0.78 * stepR;
        mesh.torsoGroup.rotation.set(-0.34 * stepR, 0.88 * stepR, 0);
        mesh.rightArm.upper.rotation.x = -2.2 * stepR;
        mesh.rightArm.extremity.scale.setScalar(1 + 0.42 * stepR);
        setBucketOpacity(mesh.launcherVfxMats, 0.45 * stepR);
      }
    } else if (style === 'air_spike') {
      if (isStartup) {
        mesh.hipsGroup.rotation.set(-0.32, -0.82 + tension, 0);
        mesh.torsoGroup.rotation.set(-0.36, -0.88 + tension, 0.26);
        mesh.rightArm.upper.rotation.set(0.98, 0, -0.72);
        mesh.rightArm.lower.rotation.set(-1.65, 0, 0);
        mesh.rightArm.extremity.rotation.set(0.62, 0, 0);
        mesh.leftLeg.upper.rotation.set(-1.45, 0, 0.22);
        mesh.leftLeg.lower.rotation.set(1.75, 0, 0);
        mesh.leftLeg.extremity.rotation.set(0.65, 0, 0);
        mesh.rightLeg.upper.rotation.set(-0.75, 0, -0.22);
        mesh.rightLeg.lower.rotation.set(0.95, 0, 0);
        mesh.rightLeg.extremity.rotation.set(0.55, 0, 0);
      } else if (isActive) {
        mesh.hipsGroup.rotation.set(0.34, 0.65, -0.22);
        mesh.torsoGroup.rotation.set(0.54, 0.92, -0.28);
        mesh.rightArm.upper.rotation.set(-1.88, -0.18, 0);
        mesh.rightArm.lower.rotation.set(-0.02, 0, 0);
        mesh.rightArm.lower.scale.set(1.18, 1.26, 1.18);
        mesh.rightArm.extremity.rotation.set(-0.48, 0.35, 0);
        mesh.rightArm.extremity.scale.setScalar(1.6);
        mesh.leftArm.upper.rotation.set(0.85, 0, 0.55);
        mesh.leftLeg.upper.rotation.set(-1.35, 0, 0.2);
        mesh.leftLeg.lower.rotation.set(1.55, 0, 0);
        mesh.leftLeg.extremity.rotation.set(0.7, 0, 0);
        mesh.rightLeg.upper.rotation.set(0.65, 0, -0.2);
        mesh.rightLeg.lower.rotation.set(0.35, 0, 0);
        mesh.rightLeg.extremity.rotation.set(0.75, 0, 0);

        setBucketOpacity(mesh.slashVfxMats, 0.98);
        setBucketOpacity(mesh.footAuraMats, 0.92);
        mesh.slashEffectGroup.rotation.set(0.25, 0, progress * 3.4);
        mesh.slashEffectGroup.scale.setScalar(1.28 * smearBoost);
      } else {
        mesh.torsoGroup.rotation.set(0.45 * stepR, 0.82 * stepR, 0);
        mesh.rightArm.upper.rotation.x = -1.6 * stepR;
      }
    } else if (style === 'jab' || style === 'tonfa_slash') {
      const isKaze = fighter.id === 'kaze';
      const isIgnis = fighter.id === 'ignis';
      const isTophia = fighter.id === 'tophia';
      if (isStartup) {
        mesh.hipsGroup.rotation.y = 0.65 + tension;
        mesh.torsoGroup.rotation.set(0.16, 0.78 + tension, -0.16);
        mesh.leftArm.upper.rotation.set(0.72, 0.32, 0.55);
        mesh.leftArm.lower.rotation.set(-1.72, 0, 0);
        mesh.leftArm.extremity.rotation.set(0.62, 0, 0);
        mesh.leftLeg.upper.rotation.set(-0.68, 0, 0.16);
        mesh.leftLeg.lower.rotation.set(0.88, 0, 0);
        mesh.leftLeg.extremity.rotation.set(0.38, 0, 0);
      } else if (isActive) {
        mesh.hipsGroup.rotation.y = -0.62;
        mesh.torsoGroup.rotation.set(
          isIgnis ? 0.38 : isTophia ? 0.12 : 0.26,
          -0.98,
          isKaze ? 0.22 : -0.18
        );
        mesh.headGroup.rotation.set(-0.14, 0.72, 0);

        mesh.leftArm.upper.rotation.set(-1.72, 0.24, 0);
        mesh.leftArm.lower.rotation.set(-0.01, 0, 0);
        mesh.leftArm.lower.scale.set(1.16, 1.26, 1.16);
        mesh.leftArm.extremity.rotation.set(
          isTophia ? -0.85 : isKaze ? 0.15 : 0.35,
          isIgnis ? 0.78 : -0.45,
          isKaze ? -0.65 : 0
        );
        mesh.leftArm.extremity.scale.setScalar(1.56);

        mesh.rightArm.upper.rotation.set(0.75, -0.25, -0.52);
        mesh.rightArm.lower.rotation.set(-1.48, 0, 0);
        mesh.rightArm.extremity.rotation.set(0.4, 0, 0);

        mesh.leftLeg.upper.rotation.set(-0.82, 0, 0.22);
        mesh.leftLeg.lower.rotation.set(0.96, 0, 0);
        mesh.leftLeg.extremity.rotation.set(-0.35, 0, 0);
        mesh.rightLeg.upper.rotation.set(0.72, 0, -0.22);
        mesh.rightLeg.lower.rotation.set(0.38, 0, 0);
        mesh.rightLeg.extremity.rotation.set(0.58, 0, 0);

        setBucketOpacity(mesh.slashVfxMats, 0.96);
        mesh.slashEffectGroup.scale.setScalar(1.15 * smearBoost);
        mesh.slashEffectGroup.rotation.set(-0.2, 0.25, progress * 2.6);
      } else {
        mesh.hipsGroup.rotation.y = -0.52 * stepR;
        mesh.torsoGroup.rotation.y = -0.88 * stepR;
        mesh.leftArm.upper.rotation.set(-1.68 * stepR, 0, 0.22);
        mesh.leftArm.extremity.scale.setScalar(1 + 0.34 * stepR);
        setBucketOpacity(mesh.slashVfxMats, 0.35 * stepR);
      }
    } else if (style === 'cross_punch') {
      const isKaze = fighter.id === 'kaze';
      const isIgnis = fighter.id === 'ignis';
      const isTophia = fighter.id === 'tophia';
      if (isStartup) {
        mesh.hipsGroup.rotation.y = -0.85 + tension;
        mesh.torsoGroup.rotation.set(0.22, -1.05 + tension, 0.25);
        mesh.rightArm.upper.rotation.set(0.92, -0.42, -0.68);
        mesh.rightArm.lower.rotation.set(-1.74, 0, 0);
        mesh.rightArm.extremity.rotation.set(0.68, 0, 0);
        mesh.leftArm.upper.rotation.set(-0.92, 0.25, 0.38);
        mesh.rightLeg.upper.rotation.set(0.64, 0, -0.2);
        mesh.rightLeg.lower.rotation.set(0.82, 0, 0);
      } else if (isActive) {
        mesh.hipsGroup.rotation.y = 0.78;
        mesh.torsoGroup.rotation.set(
          isIgnis ? 0.44 : 0.28,
          1.16,
          isIgnis ? -0.32 : isKaze ? 0.24 : -0.18
        );
        mesh.headGroup.rotation.set(-0.18, -0.68, 0);

        mesh.rightArm.upper.rotation.set(-1.76, -0.28, isIgnis ? -0.35 : 0);
        mesh.rightArm.lower.rotation.set(-0.01, 0, 0);
        mesh.rightArm.lower.scale.set(1.18, 1.28, 1.18);
        mesh.rightArm.extremity.rotation.set(
          isTophia ? -0.9 : 0.38,
          isIgnis ? -0.85 : 0.55,
          isKaze ? 0.65 : 0
        );
        mesh.rightArm.extremity.scale.setScalar(1.62);

        mesh.leftArm.upper.rotation.set(0.86, 0.3, 0.55);
        mesh.leftArm.lower.rotation.set(-1.28, 0, 0);

        mesh.leftLeg.upper.rotation.set(-0.92, 0, 0.26);
        mesh.leftLeg.lower.rotation.set(1.08, 0, 0);
        mesh.leftLeg.extremity.rotation.set(-0.42, 0, 0);
        mesh.rightLeg.upper.rotation.set(0.82, 0, -0.26);
        mesh.rightLeg.lower.rotation.set(0.32, 0, 0);
        mesh.rightLeg.extremity.rotation.set(0.68, 0.35, 0);

        setBucketOpacity(mesh.slashVfxMats, 0.98);
        mesh.slashEffectGroup.scale.setScalar(1.36 * smearBoost);
        mesh.slashEffectGroup.rotation.set(0.25, -0.22, -progress * 3.1);
      } else {
        mesh.hipsGroup.rotation.y = 0.68 * stepR;
        mesh.torsoGroup.rotation.y = 1.08 * stepR;
        mesh.rightArm.upper.rotation.set(-1.74 * stepR, 0, -0.22);
        mesh.rightArm.extremity.scale.setScalar(1 + 0.4 * stepR);
        setBucketOpacity(mesh.slashVfxMats, 0.45 * stepR);
      }
    } else if (style === 'finisher_punch') {
      const isTophia = fighter.id === 'tophia';
      const isIgnis = fighter.id === 'ignis';
      if (isStartup) {
        mesh.hipsGroup.position.y = 0.64;
        mesh.torsoGroup.rotation.set(-0.52 + tension, 0, 0);
        mesh.leftArm.upper.rotation.set(0.95, 0, 0.85);
        mesh.leftArm.lower.rotation.set(-1.68, 0, 0);
        mesh.leftArm.extremity.rotation.set(0.72, 0, 0);
        mesh.rightArm.upper.rotation.set(0.95, 0, -0.85);
        mesh.rightArm.lower.rotation.set(-1.68, 0, 0);
        mesh.rightArm.extremity.rotation.set(0.72, 0, 0);
        if (isTophia || isIgnis) {
          mesh.leftLeg.upper.rotation.set(-1.42, 0, 0.25);
          mesh.leftLeg.lower.rotation.set(1.52, 0, 0);
          mesh.leftLeg.extremity.rotation.set(-0.45, 0, 0);
        }
      } else if (isActive) {
        mesh.hipsGroup.position.y = 0.72;
        mesh.torsoGroup.rotation.set(0.62, 0, 0);
        mesh.headGroup.rotation.set(-0.42, 0, 0);

        mesh.leftArm.upper.rotation.set(-1.72, 0.28, 0);
        mesh.leftArm.lower.rotation.set(-0.01, 0, 0);
        mesh.leftArm.lower.scale.set(1.2, 1.3, 1.2);
        mesh.leftArm.extremity.rotation.set(-0.78, 0.35, -0.35);
        mesh.leftArm.extremity.scale.setScalar(1.66);

        mesh.rightArm.upper.rotation.set(-1.72, -0.28, 0);
        mesh.rightArm.lower.rotation.set(-0.01, 0, 0);
        mesh.rightArm.lower.scale.set(1.2, 1.3, 1.2);
        mesh.rightArm.extremity.rotation.set(-0.78, -0.35, 0.35);
        mesh.rightArm.extremity.scale.setScalar(1.66);

        mesh.leftLeg.upper.rotation.set(-0.96, 0, 0.28);
        mesh.leftLeg.lower.rotation.set(1.16, 0, 0);
        mesh.leftLeg.extremity.rotation.set(-0.45, 0, 0);
        mesh.rightLeg.upper.rotation.set(0.86, 0, -0.28);
        mesh.rightLeg.lower.rotation.set(0.35, 0, 0);
        mesh.rightLeg.extremity.rotation.set(0.65, 0, 0);

        setBucketOpacity(mesh.slashVfxMats, 0.98);
        setBucketOpacity(mesh.blastVfxMats, 0.94 * (1 - progress * 0.3));
        mesh.slashEffectGroup.scale.setScalar(1.45 * smearBoost);
        mesh.slashEffectGroup.rotation.z = progress * 3.6;

        mesh.blastEffectGroup.scale.set(
          1.05 + progress * 1.25,
          1.05 + progress * 1.25,
          1.05 + progress * 1.65
        );
        mesh.blastEffectGroup.position.z = 1.05 + progress * 1.35;
        mesh.blastEffectGroup.rotation.z = elapsed * 16;

        shockMat.opacity = 0.85 * (1 - progress);
        mesh.groundShockRingMesh.scale.setScalar(0.8 + progress * 1.5);
      } else {
        mesh.torsoGroup.rotation.x = 0.52 * stepR;
        mesh.leftArm.upper.rotation.x = -1.68 * stepR;
        mesh.rightArm.upper.rotation.x = -1.68 * stepR;
        mesh.leftArm.extremity.scale.setScalar(1 + 0.45 * stepR);
        mesh.rightArm.extremity.scale.setScalar(1 + 0.45 * stepR);
        setBucketOpacity(mesh.blastVfxMats, 0.42 * stepR);
      }
    } else if (style === 'spin_kick') {
      if (isStartup) {
        mesh.hipsGroup.position.y = 0.74;
        mesh.hipsGroup.rotation.y = -1.15 + tension;
        mesh.torsoGroup.rotation.set(0.32, -1.05 + tension, 0.28);
        mesh.rightLeg.upper.rotation.set(-1.35, 0, -0.28);
        mesh.rightLeg.lower.rotation.set(1.58, 0, 0);
        mesh.rightLeg.extremity.rotation.set(0.62, 0, 0);
        setBucketOpacity(mesh.footAuraMats, 0.85);
      } else if (isActive) {
        mesh.hipsGroup.rotation.y = progress * Math.PI * 2;
        mesh.torsoGroup.rotation.set(-0.38, 0, -0.52);
        mesh.rightLeg.upper.rotation.set(-1.68, 0, -0.62);
        mesh.rightLeg.lower.rotation.set(0.01, 0, 0);
        mesh.rightLeg.lower.scale.set(1.2, 1.32, 1.2);
        mesh.rightLeg.extremity.rotation.set(0.68, 0, -0.35);
        mesh.rightLeg.extremity.scale.setScalar(1.68);

        mesh.leftLeg.upper.rotation.set(0.48, 0, 0.25);
        mesh.leftLeg.lower.rotation.set(0.65, 0, 0);
        mesh.leftLeg.extremity.rotation.set(0.55, 0, 0);

        mesh.leftArm.upper.rotation.set(-1.35, 0, 0.95);
        mesh.rightArm.upper.rotation.set(-1.35, 0, -0.95);

        setBucketOpacity(mesh.footAuraMats, 0.98);
        mesh.kickFootAura.scale.setScalar(1.65);
        setBucketOpacity(mesh.slashVfxMats, 0.98);
        mesh.slashEffectGroup.scale.setScalar(1.42 * smearBoost);
        mesh.slashEffectGroup.rotation.set(
          Math.PI * 0.45,
          0,
          progress * Math.PI * 2.2
        );
        setBucketOpacity(mesh.launcherVfxMats, 0.75 * (1 - progress * 0.4));
        mesh.launcherEffectGroup.rotation.y = progress * Math.PI * 3;
      } else {
        mesh.rightLeg.upper.rotation.x = -1.35 * stepR;
        mesh.rightLeg.extremity.scale.setScalar(1 + 0.48 * stepR);
        setBucketOpacity(mesh.footAuraMats, 0.45 * stepR);
      }
    } else if (style === 'axe_kick') {
      if (isStartup) {
        mesh.torsoGroup.rotation.set(-0.48 + tension, -0.38, 0.25);
        mesh.rightLeg.upper.rotation.set(-2.55, 0, -0.22);
        mesh.rightLeg.lower.rotation.set(0.1, 0, 0);
        mesh.rightLeg.extremity.rotation.set(-0.58, 0, 0);
        mesh.rightLeg.extremity.scale.setScalar(1.42);
        mesh.leftArm.upper.rotation.set(-1.42, 0, 0.68);
        mesh.rightArm.upper.rotation.set(0.82, 0, -0.58);
        setBucketOpacity(mesh.footAuraMats, 0.9);
      } else if (isActive) {
        mesh.torsoGroup.rotation.set(0.58, 0.36, -0.22);
        mesh.rightLeg.upper.rotation.set(-1.45, 0, -0.15);
        mesh.rightLeg.lower.rotation.set(0.02, 0, 0);
        mesh.rightLeg.lower.scale.set(1.22, 1.34, 1.22);
        mesh.rightLeg.extremity.rotation.set(0.25, 0, 0);
        mesh.rightLeg.extremity.scale.setScalar(1.72);

        mesh.leftLeg.upper.rotation.set(0.35, 0, 0.2);
        mesh.leftLeg.lower.rotation.set(0.52, 0, 0);
        mesh.rightArm.upper.rotation.set(-1.45, 0, -0.28);
        mesh.rightArm.lower.rotation.set(-0.15, 0, 0);
        mesh.rightArm.extremity.scale.setScalar(1.38);

        setBucketOpacity(mesh.footAuraMats, 0.98);
        mesh.kickFootAura.scale.setScalar(1.72);
        setBucketOpacity(mesh.slashVfxMats, 0.98);
        mesh.slashEffectGroup.scale.setScalar(1.46 * smearBoost);
        mesh.slashEffectGroup.rotation.set(0, 0, -progress * 2.8);

        setBucketOpacity(mesh.launcherVfxMats, 0.88 * (1 - progress * 0.35));
        mesh.launcherEffectGroup.scale.set(
          0.95 + progress * 0.55,
          0.55 + progress * 0.95,
          0.95 + progress * 0.55
        );
        mesh.launcherEffectGroup.position.y = 0.75 + progress * 0.45;

        shockMat.opacity = 0.94 * (1 - progress);
        mesh.groundShockRingMesh.scale.setScalar(0.95 + progress * 2.05);
      } else {
        mesh.torsoGroup.rotation.x = 0.52 * stepR;
        mesh.rightLeg.extremity.scale.setScalar(1 + 0.52 * stepR);
        setBucketOpacity(mesh.launcherVfxMats, 0.4 * stepR);
      }
    } else if (style === 'uppercut') {
      if (isStartup) {
        mesh.hipsGroup.position.y = 0.5;
        mesh.hipsGroup.rotation.y = -0.95 + tension;
        mesh.torsoGroup.rotation.set(0.54, -0.95 + tension, 0.28);
        mesh.rightArm.upper.rotation.set(0.88, 0, -0.52);
        mesh.rightArm.lower.rotation.set(-1.78, 0, 0);
        mesh.rightArm.extremity.rotation.set(0.68, 0, 0);
      } else if (isActive) {
        mesh.hipsGroup.rotation.y = 0.92;
        mesh.torsoGroup.rotation.set(-0.44, 1.04, -0.32);
        mesh.rightArm.upper.rotation.set(-2.82, 0, 0.18);
        mesh.rightArm.lower.rotation.set(-0.04, 0, 0);
        mesh.rightArm.lower.scale.set(1.2, 1.32, 1.2);
        mesh.rightArm.extremity.rotation.set(-0.45, 0.55, 0);
        mesh.rightArm.extremity.scale.setScalar(1.68);

        mesh.rightLeg.upper.rotation.set(-1.48, 0, -0.18);
        mesh.rightLeg.lower.rotation.set(1.68, 0, 0);
        mesh.rightLeg.extremity.rotation.set(0.68, 0, 0);
        mesh.leftLeg.upper.rotation.set(0.48, 0, 0.15);
        mesh.leftLeg.extremity.rotation.set(0.55, 0, 0);

        setBucketOpacity(mesh.footAuraMats, 0.92);
        setBucketOpacity(mesh.slashVfxMats, 0.98);
        mesh.slashEffectGroup.scale.setScalar(1.48 * smearBoost);
        mesh.slashEffectGroup.rotation.set(0.65, 0, progress * 3.6);

        setBucketOpacity(mesh.launcherVfxMats, 0.95 * (1 - progress * 0.25));
        mesh.launcherEffectGroup.scale.set(
          1.05 + progress * 0.55,
          0.75 + progress * 1.35,
          1.05 + progress * 0.55
        );
        mesh.launcherEffectGroup.position.y = 1.15 + progress * 0.85;
        mesh.launcherEffectGroup.rotation.y = progress * 5.2;

        shockMat.opacity = 0.92 * (1 - progress);
        mesh.groundShockRingMesh.scale.setScalar(0.95 + progress * 1.9);
      } else {
        mesh.rightArm.upper.rotation.x = -2.4 * stepR;
        mesh.rightArm.extremity.scale.setScalar(1 + 0.5 * stepR);
        setBucketOpacity(mesh.launcherVfxMats, 0.5 * stepR);
      }
    } else if (style === 'palm_blast') {
      if (isStartup) {
        mesh.hipsGroup.rotation.y = -0.88 + tension;
        mesh.torsoGroup.rotation.set(-0.28, -0.95 + tension, 0);
        mesh.leftArm.upper.rotation.set(-0.35, -0.72, 0.42);
        mesh.leftArm.lower.rotation.set(-1.55, 0, 0);
        mesh.leftArm.extremity.rotation.set(0.62, 0, 0);
        mesh.rightArm.upper.rotation.set(-0.35, -0.72, -0.42);
        mesh.rightArm.lower.rotation.set(-1.55, 0, 0);
        mesh.rightArm.extremity.rotation.set(0.62, 0, 0);
        mesh.leftLeg.upper.rotation.set(-0.72, 0, 0.25);
        mesh.leftLeg.lower.rotation.set(0.92, 0, 0);
        setBucketOpacity(mesh.blastVfxMats, 0.55);
        mesh.blastEffectGroup.scale.setScalar(0.68);
        mesh.blastEffectGroup.position.z = 0.65;
      } else if (isActive) {
        mesh.hipsGroup.rotation.y = 0.34;
        mesh.torsoGroup.rotation.set(0.46, 0.28, 0);
        mesh.leftArm.upper.rotation.set(-1.66, 0.26, 0);
        mesh.leftArm.lower.rotation.set(-0.01, 0, 0);
        mesh.leftArm.lower.scale.set(1.18, 1.28, 1.18);
        mesh.leftArm.extremity.rotation.set(-0.85, 0, -0.35);
        mesh.leftArm.extremity.scale.setScalar(1.58);

        mesh.rightArm.upper.rotation.set(-1.66, -0.26, 0);
        mesh.rightArm.lower.rotation.set(-0.01, 0, 0);
        mesh.rightArm.lower.scale.set(1.18, 1.28, 1.18);
        mesh.rightArm.extremity.rotation.set(-0.85, 0, 0.35);
        mesh.rightArm.extremity.scale.setScalar(1.58);

        mesh.leftLeg.upper.rotation.set(-0.84, 0, 0.28);
        mesh.leftLeg.lower.rotation.set(0.98, 0, 0);
        mesh.leftLeg.extremity.rotation.set(-0.38, 0, 0);
        mesh.rightLeg.upper.rotation.set(0.76, 0, -0.28);
        mesh.rightLeg.lower.rotation.set(0.32, 0, 0);
        mesh.rightLeg.extremity.rotation.set(0.62, 0, 0);

        setBucketOpacity(mesh.slashVfxMats, 0.9 * (1 - progress * 0.4));
        setBucketOpacity(mesh.blastVfxMats, 0.96 * (1 - progress * 0.3));
        mesh.blastEffectGroup.scale.set(
          1.15 + progress * 1.45,
          1.15 + progress * 1.45,
          1.15 + progress * 2.25
        );
        mesh.blastEffectGroup.position.z = 1.15 + progress * 1.85;
        mesh.blastEffectGroup.rotation.z = fighter.id === 'tophia' ? 0 : elapsed * 18;

        if (fighter.id === 'tophia') {
          setBucketOpacity(mesh.launcherVfxMats, 0.85 * (1 - progress * 0.35));
          mesh.launcherEffectGroup.position.z = 1.1 + progress * 1.2;
        }
        shockMat.opacity = 0.85 * (1 - progress);
        mesh.groundShockRingMesh.scale.setScalar(0.85 + progress * 1.75);
      } else {
        mesh.leftArm.upper.rotation.x = -1.5 * stepR;
        mesh.rightArm.upper.rotation.x = -1.5 * stepR;
        setBucketOpacity(mesh.blastVfxMats, 0.45 * stepR);
      }
    } else {
      if (isStartup) {
        mesh.hipsGroup.position.y = 0.58;
        mesh.torsoGroup.rotation.x = -0.58 + tension;
        mesh.leftArm.upper.rotation.set(0.55, 0, 1.45);
        mesh.rightArm.upper.rotation.set(0.55, 0, -1.45);
        setBucketOpacity(mesh.launcherVfxMats, 0.85);
        mesh.launcherEffectGroup.scale.setScalar(1.05);
      } else if (isActive) {
        const flurry = elapsed * 52;
        const sF = Math.sin(flurry);
        const cF = Math.cos(flurry);
        mesh.hipsGroup.rotation.y = Math.sin(flurry * 0.5) * 0.85;
        mesh.torsoGroup.rotation.set(0.28 + sF * 0.18, cF * 0.65, sF * 0.22);

        mesh.leftArm.upper.rotation.set(-1.62 + sF * 0.78, 0.2, 0.25);
        mesh.leftArm.lower.rotation.set(-0.05, 0, 0);
        mesh.leftArm.extremity.rotation.set(sF * 0.6, cF * 0.6, 0);
        mesh.leftArm.extremity.scale.setScalar(1.58);

        mesh.rightArm.upper.rotation.set(-1.62 + cF * 0.78, -0.2, -0.25);
        mesh.rightArm.lower.rotation.set(-0.05, 0, 0);
        mesh.rightArm.extremity.rotation.set(-sF * 0.6, -cF * 0.6, 0);
        mesh.rightArm.extremity.scale.setScalar(1.58);

        mesh.rightLeg.upper.rotation.x = -1.45 * Math.abs(Math.sin(flurry * 0.5));
        mesh.rightLeg.extremity.rotation.x = 0.65;
        mesh.rightLeg.extremity.scale.setScalar(1.48);

        setBucketOpacity(mesh.footAuraMats, 0.98);
        setBucketOpacity(mesh.slashVfxMats, 0.96);
        setBucketOpacity(mesh.blastVfxMats, 0.94);
        setBucketOpacity(mesh.launcherVfxMats, 0.92);

        mesh.slashEffectGroup.scale.setScalar(1.52);
        mesh.slashEffectGroup.rotation.set(sF * 0.5, cF * 0.5, flurry * 0.45);

        mesh.blastEffectGroup.scale.set(1.75, 1.75, 2.75);
        mesh.blastEffectGroup.position.z = 1.85;
        mesh.blastEffectGroup.rotation.z = fighter.id === 'tophia' ? 0 : flurry * 0.35;

        mesh.launcherEffectGroup.scale.set(1.35, 1.45, 1.35);
        mesh.launcherEffectGroup.rotation.y = flurry * 0.25;

        shockMat.opacity = 0.95;
        mesh.groundShockRingMesh.scale.setScalar(1.4 + Math.sin(flurry) * 0.5);
      }
    }
  } else if (fighter.action === 'hitstun' || fighter.action === 'blockstun') {
    const isHit = fighter.action === 'hitstun';
    if (fighter.action === 'blockstun') {
      if (fighter.crouching) {
        mesh.hipsGroup.position.y = 0.54;
        mesh.guardShieldMesh.position.set(0, 0.18, 0.65);
      } else {
        mesh.guardShieldMesh.position.set(0, 0.42, 0.65);
      }
      shieldMat.opacity = 0.92;
      mesh.guardShieldMesh.rotation.z = elapsed * 9;
      mesh.torsoGroup.rotation.set(-0.26, 0, 0);
      mesh.headGroup.rotation.set(-0.24, 0, 0);
      mesh.leftArm.upper.rotation.set(-1.25, 0.62, 0.25);
      mesh.leftArm.lower.rotation.set(-1.52, 0, 0);
      mesh.rightArm.upper.rotation.set(-1.25, -0.62, -0.25);
      mesh.rightArm.lower.rotation.set(-1.52, 0, 0);
    } else if (isHit) {
      // Item 5: Anatomical Directional Hitstun Snap based on lastHitHeight ('overhead' | 'mid' | 'low')
      mesh.torsoGroup.scale.set(1.16, 0.84, 1.16);
      if (fighter.lastHitHeight === 'overhead') {
        // Overhead / High hit: Head and chest whip sharply backward, arms flung wide!
        mesh.torsoGroup.rotation.set(-0.82, 0.42, -0.24);
        mesh.headGroup.rotation.set(-0.72, 0, 0.32);
        mesh.leftArm.upper.rotation.set(-0.45, 0, 1.28);
        mesh.rightArm.upper.rotation.set(-0.45, 0, -1.28);
        mesh.leftLeg.upper.rotation.x = 0.42;
        mesh.rightLeg.upper.rotation.x = -0.42;
      } else if (fighter.lastHitHeight === 'low') {
        // Low hit: Hips drop and knees buckle sharply inward!
        mesh.hipsGroup.position.y = 0.5;
        mesh.torsoGroup.rotation.set(0.58, -0.32, 0.18);
        mesh.headGroup.rotation.set(0.38, 0, -0.2);
        mesh.leftLeg.upper.rotation.set(-1.22, 0, 0.32);
        mesh.leftLeg.lower.rotation.set(1.58, 0, 0);
        mesh.rightLeg.upper.rotation.set(-0.98, 0, -0.32);
        mesh.rightLeg.lower.rotation.set(1.42, 0, 0);
        mesh.leftArm.upper.rotation.set(0.45, 0, 0.75);
        mesh.rightArm.upper.rotation.set(0.45, 0, -0.75);
      } else {
        // Mid hit: Gut-punch C-curve fold forward!
        mesh.hipsGroup.position.z = -0.18;
        mesh.torsoGroup.rotation.set(0.68, 0.36, -0.2);
        mesh.headGroup.rotation.set(0.46, 0, 0.24);
        mesh.leftArm.upper.rotation.set(-0.88, 0.35, 0.65);
        mesh.leftArm.lower.rotation.set(-1.15, 0, 0);
        mesh.rightArm.upper.rotation.set(-0.88, -0.35, -0.65);
        mesh.rightArm.lower.rotation.set(-1.15, 0, 0);
        mesh.leftLeg.upper.rotation.x = -0.45;
        mesh.rightLeg.upper.rotation.x = 0.35;
      }
    }
  } else if (fighter.action === 'knockdown') {
    // Item 1: Knockdown & Wake-up Tech Roll Animation
    if (!fighter.grounded) {
      // Airborne knockdown tumble
      mesh.hipsGroup.rotation.x = -0.95;
      mesh.torsoGroup.rotation.x = -0.35;
      mesh.leftArm.upper.rotation.set(-0.65, 0, 1.15);
      mesh.rightArm.upper.rotation.set(-0.65, 0, -1.15);
      mesh.leftLeg.upper.rotation.x = -0.65;
      mesh.rightLeg.upper.rotation.x = 0.35;
    } else if (fighter.wakeupRollDir !== 0) {
      // Grounded directional Tech Roll spin!
      mesh.hipsGroup.position.y = 0.44;
      mesh.hipsGroup.rotation.x = fighter.wakeupRollDir * progress * Math.PI * 2;
      mesh.torsoGroup.rotation.x = 0.75;
      mesh.leftLeg.upper.rotation.x = -1.45;
      mesh.leftLeg.lower.rotation.x = 1.65;
      mesh.rightLeg.upper.rotation.x = -1.45;
      mesh.rightLeg.lower.rotation.x = 1.65;
      mesh.leftArm.upper.rotation.set(-1.25, 0, 0.35);
      mesh.rightArm.upper.rotation.set(-1.25, 0, -0.35);
    } else if (fighter.actionTimerFrames <= 8) {
      // Stepped wake-up push-off pose in last 8 frames
      mesh.hipsGroup.position.y = 0.48;
      mesh.hipsGroup.rotation.x = -0.38;
      mesh.torsoGroup.rotation.x = 0.52;
      mesh.leftLeg.upper.rotation.x = -1.25;
      mesh.leftLeg.lower.rotation.x = 1.55;
      mesh.rightArm.upper.rotation.set(0.65, 0, -0.45);
    } else {
      // Lying flat on back on the arena floor
      mesh.hipsGroup.position.y = 0.22;
      mesh.hipsGroup.rotation.x = -Math.PI * 0.46;
      mesh.leftArm.upper.rotation.z = 1.05;
      mesh.rightArm.upper.rotation.z = -1.05;
      mesh.leftLeg.upper.rotation.z = 0.22;
      mesh.rightLeg.upper.rotation.z = -0.22;
    }
  } else if (fighter.action === 'ko') {
    mesh.hipsGroup.position.y = 0.24;
    mesh.hipsGroup.rotation.x = -Math.PI * 0.48;
    mesh.leftArm.upper.rotation.z = 1.1;
    mesh.rightArm.upper.rotation.z = -1.1;
  }

  if (fighter.grounded && fighter.action !== 'ko' && fighter.action !== 'knockdown') {
    const rx1L = mesh.leftLeg.upper.rotation.x;
    const rz1L = mesh.leftLeg.upper.rotation.z;
    const rx2L = rx1L + mesh.leftLeg.lower.rotation.x;
    const reachL =
      0.06 +
      0.42 * Math.cos(rx1L) * Math.cos(rz1L) +
      0.46 * Math.cos(rx2L) * Math.cos(rz1L);

    const rx1R = mesh.rightLeg.upper.rotation.x;
    const rz1R = mesh.rightLeg.upper.rotation.z;
    const rx2R = rx1R + mesh.rightLeg.lower.rotation.x;
    const reachR =
      0.06 +
      0.42 * Math.cos(rx1R) * Math.cos(rz1R) +
      0.46 * Math.cos(rx2R) * Math.cos(rz1R);

    const plantedHipsY = Math.max(0.32, Math.max(reachL, reachR) - 0.035);
    mesh.hipsGroup.position.y = fighter.y + plantedHipsY;
  }

  if (fighter.action === 'active') {
    mesh.hipsGroup.position.z = 0.36;
  }
}
