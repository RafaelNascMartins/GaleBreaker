import * as THREE from 'three';
import { FIGHTERS, getFighterPalette } from '../fighters';
import { FighterId } from '../types';
import {
  ArticulatedLimb,
  createToonMeshWithOutline,
  RiggedFighterMesh,
} from './renderTypes';

const _tmpColor = new THREE.Color();

export function applyPaletteToMesh(
  mesh: RiggedFighterMesh,
  paletteIndex: number
) {
  if (mesh.paletteIndex === paletteIndex && paletteIndex === 0) return;
  mesh.paletteIndex = paletteIndex;

  const targetPal = getFighterPalette(mesh.id, paletteIndex);
  const targetPrimary = _tmpColor.set(targetPal.swatch[0]).getHex();
  const targetAccent = _tmpColor.set(targetPal.swatch[2]).getHex();

  for (let i = 0; i < mesh.originalBaseColors.length; i++) {
    const orig = mesh.originalBaseColors[i];
    const origHexStr = `#${orig.toString(16).padStart(6, '0')}`;
    const remappedStr = targetPal.remap[origHexStr];
    const mapped = remappedStr
      ? _tmpColor.set(remappedStr).getHex()
      : orig;
    mesh.baseColors[i] = mapped;
    mesh.hitFlashMaterials[i].color.setHex(mapped);
  }

  (mesh.auraRing.material as THREE.MeshBasicMaterial).color.setHex(targetPrimary);
  (mesh.superAuraCylMesh.material as THREE.MeshBasicMaterial).color.setHex(targetPrimary);
  (mesh.guardShieldMesh.material as THREE.MeshBasicMaterial).color.setHex(targetPrimary);
  (mesh.groundShockRingMesh.material as THREE.MeshBasicMaterial).color.setHex(targetAccent);
}

export function buildFighterModel(
  fighterId: FighterId,
  toonGradientMap: THREE.DataTexture,
  paletteIndex = 0
): RiggedFighterMesh {
  const def = FIGHTERS[fighterId];
  const root = new THREE.Group();

  const hitFlashMaterials: THREE.MeshToonMaterial[] = [];
  const originalBaseColors: number[] = [];
  const baseColors: number[] = [];
  const outlineMeshes: THREE.Mesh[] = [];

  const registerMat = (mat: THREE.MeshToonMaterial) => {
    hitFlashMaterials.push(mat);
    const hex = mat.color.getHex();
    originalBaseColors.push(hex);
    baseColors.push(hex);
  };

  const shadowGeo = new THREE.CircleGeometry(0.68, 24);
  shadowGeo.rotateX(-Math.PI / 2);
  const shadowMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.72,
    depthWrite: false,
  });
  const shadowDisc = new THREE.Mesh(shadowGeo, shadowMat);
  shadowDisc.position.y = 0.008;
  root.add(shadowDisc);

  const auraGeo = new THREE.RingGeometry(0.68, 0.82, 28);
  auraGeo.rotateX(-Math.PI / 2);
  const auraMat = new THREE.MeshBasicMaterial({
    color: def.primaryColor,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.28,
    depthWrite: false,
  });
  const auraRing = new THREE.Mesh(auraGeo, auraMat);
  auraRing.position.y = 0.012;
  root.add(auraRing);

  const hipsGroup = new THREE.Group();
  hipsGroup.position.set(0, 0.92, 0);
  root.add(hipsGroup);

  const pelvisColor =
    fighterId === 'kaze'
      ? '#f8fafc'
      : fighterId === 'ignis'
      ? '#1e293b'
      : fighterId === 'tophia'
      ? '#78350f'
      : '#0f172a';

  const pelvisGeo = new THREE.CylinderGeometry(0.28, 0.34, 0.32, 10);
  const pelvis = createToonMeshWithOutline(
    toonGradientMap,
    pelvisGeo,
    pelvisColor,
    0.04,
    outlineMeshes
  );
  registerMat(pelvis.mat);
  hipsGroup.add(pelvis.group);

  const beltGeo = new THREE.TorusGeometry(0.29, 0.065, 8, 18);
  beltGeo.rotateX(Math.PI / 2);
  const beltColor =
    fighterId === 'kaze'
      ? '#ef4444'
      : fighterId === 'ignis'
      ? '#facc15'
      : fighterId === 'tophia'
      ? '#10b981'
      : '#06b6d4';
  const belt = createToonMeshWithOutline(
    toonGradientMap,
    beltGeo,
    beltColor,
    0.04,
    outlineMeshes
  );
  belt.group.position.y = 0.12;
  registerMat(belt.mat);
  hipsGroup.add(belt.group);

  const buildLeg = (side: number): ArticulatedLimb => {
    const upper = new THREE.Group();
    upper.position.set(side * 0.18, -0.06, 0);

    const thighRadiusTop = fighterId === 'kaze' || fighterId === 'tophia' ? 0.19 : 0.15;
    const thighRadiusBot = fighterId === 'kaze' || fighterId === 'tophia' ? 0.23 : 0.13;
    const thighGeo = new THREE.CylinderGeometry(thighRadiusTop, thighRadiusBot, 0.44, 10);
    const thigh = createToonMeshWithOutline(
      toonGradientMap,
      thighGeo,
      pelvisColor,
      0.04,
      outlineMeshes
    );
    thigh.group.position.y = -0.22;
    registerMat(thigh.mat);
    upper.add(thigh.group);

    const lower = new THREE.Group();
    lower.position.set(0, -0.42, 0);
    upper.add(lower);

    const shinColor =
      fighterId === 'kaze'
        ? '#0f172a'
        : fighterId === 'ignis'
        ? '#ef4444'
        : fighterId === 'tophia'
        ? '#f59e0b'
        : '#06b6d4';

    const shinGeo = new THREE.CylinderGeometry(0.12, 0.1, 0.42, 10);
    const shin = createToonMeshWithOutline(
      toonGradientMap,
      shinGeo,
      shinColor,
      0.04,
      outlineMeshes
    );
    shin.group.position.y = -0.21;
    registerMat(shin.mat);
    lower.add(shin.group);

    const extremity = new THREE.Group();
    extremity.position.set(0, -0.41, 0);
    lower.add(extremity);

    const footGeo = new THREE.BoxGeometry(0.18, 0.12, 0.34);
    const foot = createToonMeshWithOutline(
      toonGradientMap,
      footGeo,
      fighterId === 'tophia' ? '#451a03' : '#1e293b',
      0.04,
      outlineMeshes
    );
    foot.group.position.set(0, 0, 0.07);
    registerMat(foot.mat);
    extremity.add(foot.group);

    hipsGroup.add(upper);
    return { upper, lower, extremity };
  };

  const leftLeg = buildLeg(-1);
  const rightLeg = buildLeg(1);

  const torsoGroup = new THREE.Group();
  torsoGroup.position.set(0, 0.14, 0);
  hipsGroup.add(torsoGroup);

  const torsoGeo = new THREE.CylinderGeometry(0.36, 0.27, 0.64, 12);
  const torso = createToonMeshWithOutline(
    toonGradientMap,
    torsoGeo,
    def.outfitColor,
    0.04,
    outlineMeshes
  );
  torso.group.position.y = 0.32;
  registerMat(torso.mat);
  torsoGroup.add(torso.group);

  const capeOrCoatGroup = new THREE.Group();
  capeOrCoatGroup.position.set(0, 0.52, -0.22);
  torsoGroup.add(capeOrCoatGroup);

  const backAccessoryGroup = new THREE.Group();
  backAccessoryGroup.position.set(0, 0.45, -0.32);
  torsoGroup.add(backAccessoryGroup);

  if (fighterId === 'kaze') {
    const lapelGeo = new THREE.TorusGeometry(0.26, 0.055, 6, 12);
    lapelGeo.rotateX(Math.PI * 0.35);
    const lapel = createToonMeshWithOutline(
      toonGradientMap,
      lapelGeo,
      '#f8fafc',
      0.03,
      outlineMeshes
    );
    lapel.group.position.set(0, 0.56, 0.08);
    registerMat(lapel.mat);
    torsoGroup.add(lapel.group);

    for (const side of [-0.12, 0.12]) {
      const scarfGeo = new THREE.BoxGeometry(0.14, 0.85, 0.04);
      const scarf = createToonMeshWithOutline(
        toonGradientMap,
        scarfGeo,
        '#ef4444',
        0.03,
        outlineMeshes
      );
      scarf.group.position.set(side, -0.35, -0.08);
      scarf.group.rotation.x = 0.25;
      registerMat(scarf.mat);
      capeOrCoatGroup.add(scarf.group);
    }

    const shurikenRing = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.TorusGeometry(0.48, 0.04, 6, 16),
      '#34d399',
      0.03,
      outlineMeshes
    );
    registerMat(shurikenRing.mat);
    backAccessoryGroup.add(shurikenRing.group);
  } else if (fighterId === 'ignis') {
    const chestPlateGeo = new THREE.BoxGeometry(0.38, 0.48, 0.26);
    const chestPlate = createToonMeshWithOutline(
      toonGradientMap,
      chestPlateGeo,
      '#fde68a',
      0.03,
      outlineMeshes
    );
    chestPlate.group.position.set(0, 0.35, 0.16);
    registerMat(chestPlate.mat);
    torsoGroup.add(chestPlate.group);

    for (const side of [-1, 1]) {
      const pauldron = createToonMeshWithOutline(
        toonGradientMap,
        new THREE.SphereGeometry(0.25, 10, 8),
        '#1e293b',
        0.04,
        outlineMeshes
      );
      pauldron.group.position.set(side * 0.42, 0.58, 0);
      registerMat(pauldron.mat);
      torsoGroup.add(pauldron.group);

      const spike = createToonMeshWithOutline(
        toonGradientMap,
        new THREE.ConeGeometry(0.09, 0.28, 6),
        '#facc15',
        0.04,
        outlineMeshes
      );
      spike.group.position.set(side * 0.56, 0.74, 0);
      spike.group.rotation.z = -side * 0.6;
      registerMat(spike.mat);
      torsoGroup.add(spike.group);
    }
  } else if (fighterId === 'tophia') {
    const mantleGeo = new THREE.CylinderGeometry(0.46, 0.52, 0.22, 12);
    const mantle = createToonMeshWithOutline(
      toonGradientMap,
      mantleGeo,
      '#f59e0b',
      0.04,
      outlineMeshes
    );
    mantle.group.position.set(0, 0.54, 0);
    registerMat(mantle.mat);
    torsoGroup.add(mantle.group);

    const skirtGeo = new THREE.BoxGeometry(0.56, 0.75, 0.08);
    const skirt = createToonMeshWithOutline(
      toonGradientMap,
      skirtGeo,
      '#f59e0b',
      0.03,
      outlineMeshes
    );
    skirt.group.position.set(0, -0.5, 0);
    registerMat(skirt.mat);
    capeOrCoatGroup.add(skirt.group);

    for (let i = 0; i < 5; i++) {
      const ang = (i / 5) * Math.PI - Math.PI * 0.5;
      const stone = createToonMeshWithOutline(
        toonGradientMap,
        new THREE.OctahedronGeometry(0.14, 0),
        i % 2 === 0 ? '#10b981' : '#f59e0b',
        0.04,
        outlineMeshes
      );
      stone.group.position.set(Math.sin(ang) * 0.68, Math.cos(ang) * 0.55 + 0.15, 0);
      registerMat(stone.mat);
      backAccessoryGroup.add(stone.group);
    }
  } else {
    const collarGeo = new THREE.CylinderGeometry(0.32, 0.28, 0.24, 10, 1, true);
    const collar = createToonMeshWithOutline(
      toonGradientMap,
      collarGeo,
      '#06b6d4',
      0.03,
      outlineMeshes
    );
    collar.group.position.set(0, 0.64, 0);
    registerMat(collar.mat);
    torsoGroup.add(collar.group);

    for (const side of [-0.18, 0.18]) {
      const tailGeo = new THREE.BoxGeometry(0.26, 0.88, 0.06);
      const tail = createToonMeshWithOutline(
        toonGradientMap,
        tailGeo,
        '#0f172a',
        0.035,
        outlineMeshes
      );
      tail.group.position.set(side, -0.45, -0.05);
      tail.group.rotation.z = side * 0.4;
      registerMat(tail.mat);
      capeOrCoatGroup.add(tail.group);
    }
  }

  const buildArm = (side: number): ArticulatedLimb => {
    const upper = new THREE.Group();
    upper.position.set(side * 0.42, 0.56, 0);

    const sleeveColor =
      fighterId === 'kaze' || fighterId === 'ignis'
        ? '#fde68a'
        : fighterId === 'tophia'
        ? '#f59e0b'
        : '#0f172a';

    const upperArmGeo = new THREE.CylinderGeometry(0.11, 0.1, 0.36, 10);
    const upperArm = createToonMeshWithOutline(
      toonGradientMap,
      upperArmGeo,
      sleeveColor,
      0.04,
      outlineMeshes
    );
    upperArm.group.position.y = -0.18;
    registerMat(upperArm.mat);
    upper.add(upperArm.group);

    const lower = new THREE.Group();
    lower.position.set(0, -0.34, 0);
    upper.add(lower);

    const forearmGeo = new THREE.CylinderGeometry(0.1, 0.11, 0.34, 10);
    const forearm = createToonMeshWithOutline(
      toonGradientMap,
      forearmGeo,
      def.primaryColor,
      0.04,
      outlineMeshes
    );
    forearm.group.position.y = -0.17;
    registerMat(forearm.mat);
    lower.add(forearm.group);

    const extremity = new THREE.Group();
    extremity.position.set(0, -0.36, 0);
    lower.add(extremity);

    const fistSize = fighterId === 'ignis' ? 0.22 : 0.14;
    const fistGeo = new THREE.DodecahedronGeometry(fistSize, 1);
    const fist = createToonMeshWithOutline(
      toonGradientMap,
      fistGeo,
      def.accentColor,
      0.045,
      outlineMeshes
    );
    fist.group.position.set(0, 0, 0);
    registerMat(fist.mat);
    extremity.add(fist.group);

    if (fighterId === 'volt') {
      const tonfaGeo = new THREE.BoxGeometry(0.07, 0.58, 0.12);
      const tonfa = createToonMeshWithOutline(
        toonGradientMap,
        tonfaGeo,
        '#facc15',
        0.035,
        outlineMeshes
      );
      tonfa.group.position.set(side * 0.1, 0.12, 0.08);
      registerMat(tonfa.mat);
      extremity.add(tonfa.group);
    }

    torsoGroup.add(upper);
    return { upper, lower, extremity };
  };

  const leftArm = buildArm(-1);
  const rightArm = buildArm(1);

  const headGroup = new THREE.Group();
  headGroup.position.set(0, 0.82, 0);
  torsoGroup.add(headGroup);

  const headGeo = new THREE.SphereGeometry(0.24, 14, 12);
  const head = createToonMeshWithOutline(
    toonGradientMap,
    headGeo,
    '#fde68a',
    0.04,
    outlineMeshes
  );
  registerMat(head.mat);
  headGroup.add(head.group);

  const eyeGeo = new THREE.BoxGeometry(0.28, 0.07, 0.14);
  const eyeColor =
    fighterId === 'volt' ? '#06b6d4' : fighterId === 'ignis' ? '#ef4444' : '#090b10';
  const eyes = createToonMeshWithOutline(
    toonGradientMap,
    eyeGeo,
    eyeColor,
    0.02,
    outlineMeshes
  );
  eyes.group.position.set(0, 0.02, 0.18);
  registerMat(eyes.mat);
  headGroup.add(eyes.group);

  const hairTailGroup = new THREE.Group();
  hairTailGroup.position.set(0, 0.12, -0.18);
  headGroup.add(hairTailGroup);

  if (fighterId === 'kaze') {
    const bandGeo = new THREE.TorusGeometry(0.23, 0.04, 8, 18);
    bandGeo.rotateX(Math.PI / 2);
    const band = createToonMeshWithOutline(
      toonGradientMap,
      bandGeo,
      '#ef4444',
      0.03,
      outlineMeshes
    );
    band.group.position.y = 0.1;
    registerMat(band.mat);
    headGroup.add(band.group);

    const hairCap = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.ConeGeometry(0.24, 0.28, 8),
      def.hairColor,
      0.04,
      outlineMeshes
    );
    hairCap.group.position.set(0, 0.22, -0.04);
    hairCap.group.rotation.x = -0.35;
    registerMat(hairCap.mat);
    headGroup.add(hairCap.group);

    const pony = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.ConeGeometry(0.14, 0.58, 8),
      def.hairColor,
      0.04,
      outlineMeshes
    );
    pony.group.position.set(0, -0.18, -0.14);
    pony.group.rotation.x = 0.65;
    registerMat(pony.mat);
    hairTailGroup.add(pony.group);
  } else if (fighterId === 'ignis') {
    const spikeAngles = [
      { x: 0, y: 0.34, z: 0.04, rx: 0.15, rz: 0, s: 1.15, c: '#f97316' },
      { x: 0, y: 0.32, z: -0.12, rx: -0.45, rz: 0, s: 1.25, c: '#facc15' },
      { x: -0.16, y: 0.26, z: -0.04, rx: -0.2, rz: 0.55, s: 0.95, c: '#ef4444' },
      { x: 0.16, y: 0.26, z: -0.04, rx: -0.2, rz: -0.55, s: 0.95, c: '#ef4444' },
      { x: 0, y: 0.22, z: -0.24, rx: -0.85, rz: 0, s: 1.05, c: '#f97316' },
    ];
    for (const sp of spikeAngles) {
      const cone = createToonMeshWithOutline(
        toonGradientMap,
        new THREE.ConeGeometry(0.13 * sp.s, 0.38 * sp.s, 6),
        sp.c,
        0.04,
        outlineMeshes
      );
      cone.group.position.set(sp.x, sp.y, sp.z);
      cone.group.rotation.set(sp.rx, 0, sp.rz);
      registerMat(cone.mat);
      headGroup.add(cone.group);
    }
  } else if (fighterId === 'tophia') {
    const crownCap = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.SphereGeometry(0.245, 12, 10, 0, Math.PI * 2, 0, Math.PI * 0.55),
      def.hairColor,
      0.035,
      outlineMeshes
    );
    crownCap.group.position.y = 0.02;
    registerMat(crownCap.mat);
    headGroup.add(crownCap.group);

    const tiara = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.OctahedronGeometry(0.11, 0),
      '#f59e0b',
      0.03,
      outlineMeshes
    );
    tiara.group.position.set(0, 0.2, 0.18);
    registerMat(tiara.mat);
    headGroup.add(tiara.group);

    for (const side of [-1, 1]) {
      const bun = createToonMeshWithOutline(
        toonGradientMap,
        new THREE.SphereGeometry(0.13, 10, 10),
        def.hairColor,
        0.04,
        outlineMeshes
      );
      bun.group.position.set(side * 0.22, 0.22, -0.02);
      registerMat(bun.mat);
      headGroup.add(bun.group);

      const pin = createToonMeshWithOutline(
        toonGradientMap,
        new THREE.CylinderGeometry(0.02, 0.02, 0.36, 6),
        '#10b981',
        0.02,
        outlineMeshes
      );
      pin.group.position.set(side * 0.22, 0.22, -0.02);
      pin.group.rotation.z = side * 0.7;
      registerMat(pin.mat);
      headGroup.add(pin.group);
    }

    const braid = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.CylinderGeometry(0.08, 0.04, 0.52, 8),
      def.hairColor,
      0.04,
      outlineMeshes
    );
    braid.group.position.set(0, -0.22, -0.08);
    registerMat(braid.mat);
    hairTailGroup.add(braid.group);
  } else {
    for (let i = 0; i < 4; i++) {
      const bolt = createToonMeshWithOutline(
        toonGradientMap,
        new THREE.ConeGeometry(0.11, 0.42, 5),
        '#facc15',
        0.04,
        outlineMeshes
      );
      bolt.group.position.set((i - 1.5) * 0.09, 0.26, -0.06 - i * 0.04);
      bolt.group.rotation.set(-0.55, 0, (i - 1.5) * -0.25);
      registerMat(bolt.mat);
      headGroup.add(bolt.group);
    }
  }

  const handAuraMats: THREE.MeshBasicMaterial[] = [];
  const footAuraMats: THREE.MeshBasicMaterial[] = [];
  const slashVfxMats: THREE.MeshBasicMaterial[] = [];
  const blastVfxMats: THREE.MeshBasicMaterial[] = [];
  const launcherVfxMats: THREE.MeshBasicMaterial[] = [];

  const makeVfxMat = (
    color: string,
    bucket: THREE.MeshBasicMaterial[]
  ): THREE.MeshBasicMaterial => {
    const m = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    bucket.push(m);
    return m;
  };

  const buildLimbAuraGroup = (
    bucket: THREE.MeshBasicMaterial[],
    isFoot = false
  ): THREE.Group => {
    const g = new THREE.Group();
    const s = isFoot ? 1.25 : 1.0;
    if (fighterId === 'kaze') {
      for (let r = 0; r < 2; r++) {
        const ring = new THREE.Mesh(
          new THREE.TorusGeometry(0.24 * s, 0.028 * s, 6, 16),
          makeVfxMat(r === 0 ? '#34d399' : '#a7f3d0', bucket)
        );
        ring.rotation.set(r === 0 ? 0.6 : -0.6, r * 1.1, 0);
        g.add(ring);
      }
      for (let b = 0; b < 3; b++) {
        const ang = (b / 3) * Math.PI * 2;
        const blade = new THREE.Mesh(
          new THREE.ConeGeometry(0.06 * s, 0.32 * s, 4),
          makeVfxMat('#10b981', bucket)
        );
        blade.position.set(Math.cos(ang) * 0.22 * s, 0, Math.sin(ang) * 0.22 * s);
        blade.rotation.z = ang + Math.PI * 0.5;
        g.add(blade);
      }
    } else if (fighterId === 'ignis') {
      const core = new THREE.Mesh(
        new THREE.DodecahedronGeometry(0.24 * s, 0),
        makeVfxMat('#fde047', bucket)
      );
      g.add(core);
      for (let f = 0; f < 5; f++) {
        const ang = (f / 5) * Math.PI * 2;
        const flame = new THREE.Mesh(
          new THREE.ConeGeometry(0.11 * s, 0.42 * s, 5),
          makeVfxMat(f % 2 === 0 ? '#ef4444' : '#f97316', bucket)
        );
        flame.position.set(Math.cos(ang) * 0.16 * s, -0.08 * s, Math.sin(ang) * 0.16 * s);
        flame.rotation.set(Math.sin(ang) * 0.85, 0, -Math.cos(ang) * 0.85);
        g.add(flame);
      }
    } else if (fighterId === 'tophia') {
      const geoRing = new THREE.Mesh(
        new THREE.RingGeometry(0.18 * s, 0.3 * s, 6),
        makeVfxMat('#f59e0b', bucket)
      );
      geoRing.rotation.x = Math.PI * 0.5;
      g.add(geoRing);
      for (let c = 0; c < 4; c++) {
        const ang = (c / 4) * Math.PI * 2;
        const shard = new THREE.Mesh(
          new THREE.OctahedronGeometry(0.11 * s, 0),
          makeVfxMat(c % 2 === 0 ? '#fde047' : '#10b981', bucket)
        );
        shard.position.set(Math.cos(ang) * 0.25 * s, 0, Math.sin(ang) * 0.25 * s);
        g.add(shard);
      }
    } else {
      const plasmaBlade = new THREE.Mesh(
        new THREE.ConeGeometry(0.09 * s, 0.78 * s, 4),
        makeVfxMat('#06b6d4', bucket)
      );
      plasmaBlade.position.set(0, -0.18 * s, 0.14 * s);
      plasmaBlade.rotation.x = Math.PI * 0.5;
      g.add(plasmaBlade);
      for (let l = 0; l < 4; l++) {
        const ang = (l / 4) * Math.PI * 2;
        const spark = new THREE.Mesh(
          new THREE.ConeGeometry(0.055 * s, 0.36 * s, 3),
          makeVfxMat('#facc15', bucket)
        );
        spark.position.set(Math.cos(ang) * 0.2 * s, 0, Math.sin(ang) * 0.2 * s);
        spark.rotation.set(ang, l * 0.8, 0.65);
        g.add(spark);
      }
    }
    return g;
  };

  const leftHandAura = buildLimbAuraGroup(handAuraMats, false);
  leftArm.extremity.add(leftHandAura);

  const rightHandAura = buildLimbAuraGroup(handAuraMats, false);
  rightArm.extremity.add(rightHandAura);

  const kickFootAura = buildLimbAuraGroup(footAuraMats, true);
  kickFootAura.position.set(0, 0, 0.12);
  rightLeg.extremity.add(kickFootAura);

  const slashEffectGroup = new THREE.Group();
  slashEffectGroup.position.set(0, 0.35, 0.55);
  torsoGroup.add(slashEffectGroup);

  const slashGeo = new THREE.TorusGeometry(0.86, 0.075, 8, 24, Math.PI * 0.88);
  const slashMat = makeVfxMat(def.accentColor, slashVfxMats);
  const slashArcMesh = new THREE.Mesh(slashGeo, slashMat);
  slashArcMesh.rotation.y = Math.PI / 2;
  slashEffectGroup.add(slashArcMesh);

  if (fighterId === 'kaze') {
    const outerWind = new THREE.Mesh(
      new THREE.TorusGeometry(1.04, 0.045, 6, 24, Math.PI * 0.95),
      makeVfxMat('#10b981', slashVfxMats)
    );
    outerWind.rotation.set(0.18, Math.PI / 2, -0.15);
    slashEffectGroup.add(outerWind);

    const innerWind = new THREE.Mesh(
      new THREE.TorusGeometry(0.68, 0.035, 6, 20, Math.PI * 0.85),
      makeVfxMat('#ecfdf5', slashVfxMats)
    );
    innerWind.rotation.set(-0.18, Math.PI / 2, 0.2);
    slashEffectGroup.add(innerWind);

    for (let i = 0; i < 5; i++) {
      const ang = (i / 4) * Math.PI * 0.82;
      const fin = new THREE.Mesh(
        new THREE.ConeGeometry(0.08, 0.42, 4),
        makeVfxMat('#34d399', slashVfxMats)
      );
      fin.position.set(0, Math.sin(ang) * 0.92, Math.cos(ang) * 0.92);
      fin.rotation.x = -ang;
      slashEffectGroup.add(fin);
    }
  } else if (fighterId === 'ignis') {
    const coreArc = new THREE.Mesh(
      new THREE.TorusGeometry(0.76, 0.05, 6, 20, Math.PI * 0.8),
      makeVfxMat('#fef08a', slashVfxMats)
    );
    coreArc.rotation.y = Math.PI / 2;
    slashEffectGroup.add(coreArc);

    for (let i = 0; i < 6; i++) {
      const ang = (i / 5) * Math.PI * 0.85;
      const flameCone = new THREE.Mesh(
        new THREE.ConeGeometry(0.14, 0.52, 5),
        makeVfxMat(i % 2 === 0 ? '#ef4444' : '#f97316', slashVfxMats)
      );
      flameCone.position.set(
        (i % 2 === 0 ? 1 : -1) * 0.08,
        Math.sin(ang) * 0.92,
        Math.cos(ang) * 0.92
      );
      flameCone.rotation.x = Math.PI * 0.5 - ang;
      slashEffectGroup.add(flameCone);
    }
  } else if (fighterId === 'tophia') {
    for (let i = 0; i < 6; i++) {
      const ang = (i / 5) * Math.PI * 0.85;
      const crystal = new THREE.Mesh(
        new THREE.OctahedronGeometry(0.16, 0),
        makeVfxMat(i % 2 === 0 ? '#f59e0b' : '#10b981', slashVfxMats)
      );
      crystal.position.set(0, Math.sin(ang) * 0.9, Math.cos(ang) * 0.9);
      crystal.rotation.set(ang, i * 0.7, 0.4);
      slashEffectGroup.add(crystal);
    }
  } else {
    const twinArc = new THREE.Mesh(
      new THREE.TorusGeometry(0.98, 0.05, 6, 20, Math.PI * 0.9),
      makeVfxMat('#06b6d4', slashVfxMats)
    );
    twinArc.rotation.set(0.28, Math.PI / 2, 0.15);
    slashEffectGroup.add(twinArc);

    for (let i = 0; i < 7; i++) {
      const ang = (i / 6) * Math.PI * 0.88;
      const bolt = new THREE.Mesh(
        new THREE.BoxGeometry(0.06, 0.38, 0.06),
        makeVfxMat(i % 2 === 0 ? '#facc15' : '#38bdf8', slashVfxMats)
      );
      bolt.position.set(
        (i % 2 === 0 ? 1 : -1) * 0.12,
        Math.sin(ang) * 0.92,
        Math.cos(ang) * 0.92
      );
      bolt.rotation.set(ang + (i % 2 === 0 ? 0.55 : -0.55), 0, (i % 2 === 0 ? 1 : -1) * 0.45);
      slashEffectGroup.add(bolt);
    }
  }

  const blastEffectGroup = new THREE.Group();
  blastEffectGroup.position.set(0, 0.32, 1.35);
  torsoGroup.add(blastEffectGroup);

  const blastGeo = new THREE.CylinderGeometry(0.25, 0.65, 1.8, 12, 1, true);
  blastGeo.rotateX(Math.PI / 2);
  const blastMat = makeVfxMat(def.primaryColor, blastVfxMats);
  const blastWaveMesh = new THREE.Mesh(blastGeo, blastMat);
  blastEffectGroup.add(blastWaveMesh);

  if (fighterId === 'kaze') {
    for (let r = 0; r < 4; r++) {
      const vortexRing = new THREE.Mesh(
        new THREE.TorusGeometry(0.32 + r * 0.14, 0.04, 6, 18),
        makeVfxMat(r % 2 === 0 ? '#34d399' : '#a7f3d0', blastVfxMats)
      );
      vortexRing.position.z = -0.55 + r * 0.42;
      vortexRing.rotation.set(r * 0.35, r * 0.25, 0);
      blastEffectGroup.add(vortexRing);
    }
  } else if (fighterId === 'ignis') {
    const fireCore = new THREE.Mesh(
      new THREE.DodecahedronGeometry(0.42, 1),
      makeVfxMat('#fef08a', blastVfxMats)
    );
    fireCore.position.z = 0.25;
    blastEffectGroup.add(fireCore);

    for (let f = 0; f < 8; f++) {
      const ang = (f / 8) * Math.PI * 2;
      const magmaSpike = new THREE.Mesh(
        new THREE.ConeGeometry(0.18, 0.85, 5),
        makeVfxMat(f % 2 === 0 ? '#ef4444' : '#f97316', blastVfxMats)
      );
      magmaSpike.position.set(Math.cos(ang) * 0.38, Math.sin(ang) * 0.38, 0.15);
      magmaSpike.rotation.set(Math.PI * 0.5 + Math.sin(ang) * 0.45, 0, -Math.cos(ang) * 0.45);
      blastEffectGroup.add(magmaSpike);
    }
  } else if (fighterId === 'tophia') {
    for (let m = 0; m < 5; m++) {
      const monolith = new THREE.Mesh(
        new THREE.ConeGeometry(0.2 + m * 0.03, 0.95 + m * 0.18, 5),
        makeVfxMat(m % 2 === 0 ? '#f59e0b' : '#10b981', blastVfxMats)
      );
      monolith.position.set(
        (m % 2 === 0 ? 1 : -1) * 0.16,
        -0.25 + m * 0.08,
        -0.55 + m * 0.38
      );
      monolith.rotation.set(0.55, 0, (m % 2 === 0 ? -1 : 1) * 0.22);
      blastEffectGroup.add(monolith);
    }
  } else {
    const coreBeam = new THREE.Mesh(
      new THREE.CylinderGeometry(0.14, 0.22, 2.2, 8),
      makeVfxMat('#fef08a', blastVfxMats)
    );
    coreBeam.rotation.x = Math.PI / 2;
    blastEffectGroup.add(coreBeam);

    for (let c = 0; c < 4; c++) {
      const hexCoil = new THREE.Mesh(
        new THREE.RingGeometry(0.32 + c * 0.08, 0.42 + c * 0.08, 6),
        makeVfxMat(c % 2 === 0 ? '#06b6d4' : '#facc15', blastVfxMats)
      );
      hexCoil.position.z = -0.6 + c * 0.45;
      blastEffectGroup.add(hexCoil);
    }
  }

  const launcherEffectGroup = new THREE.Group();
  launcherEffectGroup.position.set(0, 1.25, 0.95);
  root.add(launcherEffectGroup);

  const pillarGeo = new THREE.CylinderGeometry(0.32, 0.68, 2.5, 12, 1, true);
  const pillarMat = makeVfxMat(def.primaryColor, launcherVfxMats);
  const launcherPillarMesh = new THREE.Mesh(pillarGeo, pillarMat);
  launcherEffectGroup.add(launcherPillarMesh);

  if (fighterId === 'kaze') {
    for (let i = 0; i < 4; i++) {
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(0.55 - i * 0.06, 0.04, 6, 18),
        makeVfxMat(i % 2 === 0 ? '#34d399' : '#ecfdf5', launcherVfxMats)
      );
      ring.position.y = -0.8 + i * 0.55;
      ring.rotation.set(Math.PI * 0.5 + 0.2, i * 0.6, 0);
      launcherEffectGroup.add(ring);
    }
  } else if (fighterId === 'ignis') {
    for (let i = 0; i < 6; i++) {
      const ang = (i / 6) * Math.PI * 2;
      const spire = new THREE.Mesh(
        new THREE.ConeGeometry(0.22, 1.45, 5),
        makeVfxMat(i % 2 === 0 ? '#ef4444' : '#fde047', launcherVfxMats)
      );
      spire.position.set(Math.cos(ang) * 0.48, -0.55, Math.sin(ang) * 0.48);
      spire.rotation.set(Math.sin(ang) * 0.25, 0, -Math.cos(ang) * 0.25);
      launcherEffectGroup.add(spire);
    }
  } else if (fighterId === 'tophia') {
    for (let i = 0; i < 6; i++) {
      const ang = (i / 6) * Math.PI * 2;
      const crystalPillar = new THREE.Mesh(
        new THREE.ConeGeometry(0.26, 1.75, 5),
        makeVfxMat(i % 2 === 0 ? '#f59e0b' : '#10b981', launcherVfxMats)
      );
      crystalPillar.position.set(Math.cos(ang) * 0.52, -0.4, Math.sin(ang) * 0.52);
      crystalPillar.rotation.set(Math.sin(ang) * 0.32, i * 0.5, -Math.cos(ang) * 0.32);
      launcherEffectGroup.add(crystalPillar);
    }
  } else {
    for (let i = 0; i < 6; i++) {
      const ang = (i / 6) * Math.PI * 2;
      const boltPillar = new THREE.Mesh(
        new THREE.ConeGeometry(0.12, 2.3, 4),
        makeVfxMat(i % 2 === 0 ? '#facc15' : '#06b6d4', launcherVfxMats)
      );
      boltPillar.position.set(Math.cos(ang) * 0.5, 0, Math.sin(ang) * 0.5);
      boltPillar.rotation.z = (i % 2 === 0 ? 1 : -1) * 0.18;
      launcherEffectGroup.add(boltPillar);
    }
  }

  const shieldGeo = new THREE.RingGeometry(0.18, 0.68, 6);
  const shieldMat = new THREE.MeshBasicMaterial({
    color: def.primaryColor,
    transparent: true,
    opacity: 0,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const guardShieldMesh = new THREE.Mesh(shieldGeo, shieldMat);
  guardShieldMesh.position.set(0, 0.36, 0.62);
  torsoGroup.add(guardShieldMesh);

  const shockGeo = new THREE.RingGeometry(0.55, 1.35, 28);
  shockGeo.rotateX(-Math.PI / 2);
  const shockMat = new THREE.MeshBasicMaterial({
    color: def.accentColor,
    transparent: true,
    opacity: 0,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const groundShockRingMesh = new THREE.Mesh(shockGeo, shockMat);
  groundShockRingMesh.position.set(0, 0.025, 0.65);
  root.add(groundShockRingMesh);

  const superCylGeo = new THREE.CylinderGeometry(0.76, 0.88, 1.85, 16, 1, true);
  const superCylMat = new THREE.MeshBasicMaterial({
    color: def.primaryColor,
    transparent: true,
    opacity: 0,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const superAuraCylMesh = new THREE.Mesh(superCylGeo, superCylMat);
  superAuraCylMesh.position.set(0, 0.92, 0);
  root.add(superAuraCylMesh);

  const built: RiggedFighterMesh = {
    id: fighterId,
    paletteIndex: 0,
    root,
    shadowDisc,
    auraRing,
    hipsGroup,
    torsoGroup,
    headGroup,
    hairTailGroup,
    capeOrCoatGroup,
    backAccessoryGroup,
    leftArm,
    rightArm,
    leftLeg,
    rightLeg,
    leftHandAura,
    rightHandAura,
    kickFootAura,
    slashEffectGroup,
    blastEffectGroup,
    launcherEffectGroup,
    slashArcMesh,
    blastWaveMesh,
    launcherPillarMesh,
    guardShieldMesh,
    groundShockRingMesh,
    superAuraCylMesh,
    handAuraMats,
    footAuraMats,
    slashVfxMats,
    blastVfxMats,
    launcherVfxMats,
    hitFlashMaterials,
    originalBaseColors,
    baseColors,
    outlineMeshes,
  };

  if (paletteIndex !== 0) {
    applyPaletteToMesh(built, paletteIndex);
  }
  return built;
}
