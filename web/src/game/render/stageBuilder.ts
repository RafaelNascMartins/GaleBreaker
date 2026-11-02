import * as THREE from 'three';
import { disposeObjectResources } from './disposeResources';
import { STAGES } from '../fighters';
import { PropHazard, StageId } from '../types';
import {
  createToonMeshWithOutline,
  HazardMeshEntry,
  StageEnvironmentRefs,
} from './renderTypes';

export function rebuildStageGeometry(
  env: StageEnvironmentRefs,
  stageId: StageId,
  hazards: PropHazard[]
) {
  disposeObjectResources(env.stageGroup);
  while (env.stageGroup.children.length > 0) {
    env.stageGroup.remove(env.stageGroup.children[0]);
  }
  env.hazardMeshes.clear();
  env.spectatorGroups.length = 0;
  env.torchFlames.length = 0;
  env.cloudGroups.length = 0;
  env.overdriveMeshes.length = 0;

  const stage = STAGES[stageId];
  env.scene.background = new THREE.Color(stage.skyColor);
  env.scene.fog = new THREE.FogExp2(
    stage.fogColor,
    stageId === 'zephyr_dojo' ? 0.007 : stageId === 'molten_forge' ? 0.014 : 0.011
  );

  const toon = (
    geometry: THREE.BufferGeometry,
    colorHex: string | number,
    outlineThickness = 0.038,
    outlineBucket?: THREE.Mesh[]
  ) =>
    createToonMeshWithOutline(
      env.toonGradientMap,
      geometry,
      colorHex,
      outlineThickness,
      outlineBucket
    );

  if (stageId === 'zephyr_dojo') {
    env.hemiLight.color.setHex(0xe0f2fe);
    env.hemiLight.groundColor.setHex(0x38bdf8);
    env.hemiLight.intensity = 1.28;
    env.keyLight.color.setHex(0xffffff);
    env.keyLight.intensity = 2.45;

    const cloudSeaGeo = new THREE.CircleGeometry(95, 36);
    cloudSeaGeo.rotateX(-Math.PI / 2);
    const cloudSeaMat = new THREE.MeshBasicMaterial({ color: 0xbae6fd });
    const cloudSea = new THREE.Mesh(cloudSeaGeo, cloudSeaMat);
    cloudSea.position.y = -2.2;
    env.stageGroup.add(cloudSea);

    const sunGroup = new THREE.Group();
    sunGroup.position.set(11.5, 9.2, -22);
    const sunCore = new THREE.Mesh(
      new THREE.CircleGeometry(3.4, 32),
      new THREE.MeshBasicMaterial({ color: 0xfef08a })
    );
    sunGroup.add(sunCore);
    const sunHalo = new THREE.Mesh(
      new THREE.RingGeometry(3.4, 4.8, 32),
      new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.45,
      })
    );
    sunGroup.add(sunHalo);
    env.stageGroup.add(sunGroup);

    const cliffFoundation = toon(
      new THREE.CylinderGeometry(13.2, 10.5, 3.2, 12),
      '#475569',
      0.025
    );
    cliffFoundation.group.position.set(0, -2.5, -0.5);
    env.stageGroup.add(cliffFoundation.group);

    const stageDeckGeo = new THREE.BoxGeometry(24, 1.8, 8.8);
    const stageDeckMat = new THREE.MeshToonMaterial({
      color: 0xe2e8f0,
      gradientMap: env.toonGradientMap,
    });
    const stageDeck = new THREE.Mesh(stageDeckGeo, stageDeckMat);
    stageDeck.position.set(0, -0.9, 0);
    env.stageGroup.add(stageDeck);

    const innerCourt = new THREE.Mesh(
      new THREE.BoxGeometry(19.5, 0.04, 5.2),
      new THREE.MeshToonMaterial({
        color: 0xcbd5e1,
        gradientMap: env.toonGradientMap,
      })
    );
    innerCourt.position.set(0, 0.01, -0.2);
    env.stageGroup.add(innerCourt);

    const centerEmblem = new THREE.Mesh(
      new THREE.RingGeometry(1.4, 1.85, 28),
      new THREE.MeshBasicMaterial({ color: 0x0284c7, side: THREE.DoubleSide })
    );
    centerEmblem.rotation.x = -Math.PI / 2;
    centerEmblem.position.set(0, 0.035, 0);
    env.stageGroup.add(centerEmblem);

    const trimFront = new THREE.Mesh(
      new THREE.BoxGeometry(24, 0.09, 0.24),
      new THREE.MeshBasicMaterial({ color: 0x0284c7 })
    );
    trimFront.position.set(0, 0.01, 2.25);
    env.stageGroup.add(trimFront);

    const backRailBar = toon(
      new THREE.BoxGeometry(22.4, 0.14, 0.16),
      '#ef4444',
      0.025
    );
    backRailBar.group.position.set(0, 0.78, -3.95);
    env.stageGroup.add(backRailBar.group);

    for (let r = -5; r <= 5; r++) {
      if (Math.abs(r) <= 1) continue;
      const postX = r * 2.1;
      const post = toon(
        new THREE.CylinderGeometry(0.11, 0.13, 0.92, 8),
        '#dc2626',
        0.03
      );
      post.group.position.set(postX, 0.46, -3.95);
      env.stageGroup.add(post.group);

      const finial = toon(
        new THREE.SphereGeometry(0.14, 8, 8),
        '#facc15',
        0.03
      );
      finial.group.position.set(postX, 0.98, -3.95);
      env.stageGroup.add(finial.group);
    }

    const mountainSpecs = [
      { x: -16, z: -16, r: 8.8, h: 21 },
      { x: -7.5, z: -18.5, r: 9.8, h: 25 },
      { x: 0, z: -22, r: 11.5, h: 28 },
      { x: 7.5, z: -18.5, r: 10.2, h: 25.5 },
      { x: 15.5, z: -16, r: 8.8, h: 21 },
      { x: -23, z: -12, r: 7.6, h: 18 },
      { x: 23, z: -12, r: 7.8, h: 18.5 },
      { x: -11.5, z: -14, r: 6.2, h: 15.5 },
    ];
    for (const m of mountainSpecs) {
      const peakGroup = new THREE.Group();
      peakGroup.position.set(m.x, -2.2, m.z);

      const baseCone = toon(new THREE.ConeGeometry(m.r, m.h, 7), '#1e3a8a', 0.02);
      baseCone.group.position.y = m.h * 0.5;
      peakGroup.add(baseCone.group);

      const midRidge = toon(
        new THREE.ConeGeometry(m.r * 0.72, m.h * 0.68, 7),
        '#2563eb',
        0.02
      );
      midRidge.group.position.y = m.h * 0.62;
      peakGroup.add(midRidge.group);

      const snowCap = toon(
        new THREE.ConeGeometry(m.r * 0.46, m.h * 0.45, 7),
        '#ffffff',
        0.02
      );
      snowCap.group.position.y = m.h * 0.78;
      peakGroup.add(snowCap.group);

      env.stageGroup.add(peakGroup);
    }

    for (let c = 0; c < 9; c++) {
      const cloud = new THREE.Group();
      const cx = (c - 4) * 5.4;
      const cy = 4.1 + (c % 3) * 1.45;
      const cz = -9.2 - (c % 2) * 3.8;
      cloud.position.set(cx, cy, cz);

      for (let puff = -1; puff <= 1; puff++) {
        const puffMesh = new THREE.Mesh(
          new THREE.SphereGeometry(0.98 - Math.abs(puff) * 0.2, 10, 10),
          new THREE.MeshBasicMaterial({ color: 0xffffff })
        );
        puffMesh.position.set(puff * 0.86, Math.abs(puff) * -0.15, 0);
        cloud.add(puffMesh);
      }
      env.stageGroup.add(cloud);
      env.cloudGroups.push(cloud);
    }

    const archGroup = new THREE.Group();
    archGroup.position.set(0, 0, -5.6);

    for (let st = 0; st < 3; st++) {
      const step = toon(
        new THREE.BoxGeometry(6.8 - st * 0.6, 0.25, 1.4 - st * 0.3),
        '#94a3b8',
        0.02
      );
      step.group.position.set(0, st * 0.22 + 0.12, 1.2 - st * 0.35);
      archGroup.add(step.group);
    }

    for (const xSide of [-4.4, 4.4]) {
      const pillarBase = toon(
        new THREE.CylinderGeometry(0.62, 0.72, 0.65, 10),
        '#1e293b',
        0.03
      );
      pillarBase.group.position.set(xSide, 0.32, 0);
      archGroup.add(pillarBase.group);

      const pillar = toon(
        new THREE.CylinderGeometry(0.42, 0.52, 6.8, 10),
        '#ef4444',
        0.03
      );
      pillar.group.position.set(xSide, 3.4, 0);
      archGroup.add(pillar.group);
    }

    const subBeam = toon(new THREE.BoxGeometry(10.2, 0.44, 0.65), '#ef4444', 0.03);
    subBeam.group.position.set(0, 5.35, 0);
    archGroup.add(subBeam.group);

    const topBeam = toon(new THREE.BoxGeometry(11.8, 0.6, 0.95), '#0f172a', 0.03);
    topBeam.group.position.set(0, 6.5, 0);
    archGroup.add(topBeam.group);

    const pagodaTier2 = toon(new THREE.ConeGeometry(5.6, 1.45, 4), '#0f172a', 0.03);
    pagodaTier2.group.position.set(0, 7.55, 0);
    pagodaTier2.group.rotation.y = Math.PI / 4;
    archGroup.add(pagodaTier2.group);

    const spire = toon(new THREE.ConeGeometry(0.32, 1.6, 8), '#facc15', 0.03);
    spire.group.position.set(0, 8.8, 0);
    archGroup.add(spire.group);

    const plaque = toon(new THREE.BoxGeometry(1.2, 1.45, 0.32), '#facc15', 0.03);
    plaque.group.position.set(0, 5.95, 0.25);
    archGroup.add(plaque.group);

    env.stageGroup.add(archGroup);

    for (const treeSide of [-1, 1]) {
      const treeGroup = new THREE.Group();
      treeGroup.position.set(treeSide * 8.4, 0, -4.6);

      const trunk = toon(
        new THREE.CylinderGeometry(0.28, 0.44, 3.2, 8),
        '#451a03',
        0.03
      );
      trunk.group.position.y = 1.6;
      trunk.group.rotation.z = -treeSide * 0.14;
      treeGroup.add(trunk.group);

      const blossomOffsets = [
        { x: 0, y: 3.4, z: 0, r: 1.25, c: '#f472b6' },
        { x: -treeSide * 0.85, y: 2.95, z: 0.35, r: 0.95, c: '#fb7185' },
        { x: treeSide * 0.75, y: 3.1, z: -0.25, r: 0.9, c: '#f9a8d4' },
      ];
      for (const b of blossomOffsets) {
        const canopy = toon(new THREE.DodecahedronGeometry(b.r, 1), b.c, 0.03);
        canopy.group.position.set(b.x, b.y, b.z);
        treeGroup.add(canopy.group);
      }

      const bannerPole = toon(
        new THREE.CylinderGeometry(0.08, 0.1, 4.4, 8),
        '#facc15',
        0.025
      );
      bannerPole.group.position.set(-treeSide * 2.1, 2.2, 0.3);
      treeGroup.add(bannerPole.group);

      const bannerCloth = toon(
        new THREE.BoxGeometry(0.65, 2.4, 0.06),
        '#10b981',
        0.025
      );
      bannerCloth.group.position.set(-treeSide * 1.72, 2.9, 0.3);
      treeGroup.add(bannerCloth.group);

      env.stageGroup.add(treeGroup);
    }

    // Item 12: Stage Hazard Overdrive (Phase 3 Climax — Twin Emerald Typhoon Vortex Pillars & Sacred Sky Ring)
    for (const side of [-1, 1]) {
      const vortexGroup = new THREE.Group();
      vortexGroup.position.set(side * 6.4, 0, -4.8);
      vortexGroup.visible = false;

      const cone = new THREE.Mesh(
        new THREE.CylinderGeometry(1.35, 0.42, 8.5, 14, 1, true),
        new THREE.MeshBasicMaterial({
          color: 0x34d399,
          transparent: true,
          opacity: 0.42,
          side: THREE.DoubleSide,
          depthWrite: false,
        })
      );
      cone.position.y = 4.25;
      vortexGroup.add(cone);

      for (let r = 0; r < 4; r++) {
        const ring = new THREE.Mesh(
          new THREE.TorusGeometry(0.65 + r * 0.25, 0.05, 6, 20),
          new THREE.MeshBasicMaterial({
            color: r % 2 === 0 ? 0xa7f3d0 : 0x10b981,
            transparent: true,
            opacity: 0.78,
          })
        );
        ring.position.y = 1.4 + r * 1.8;
        ring.rotation.x = Math.PI * 0.5 + 0.18;
        vortexGroup.add(ring);
      }
      env.stageGroup.add(vortexGroup);
      env.overdriveMeshes.push(vortexGroup);
    }
  } else if (stageId === 'molten_forge') {
    env.hemiLight.color.setHex(0xef4444);
    env.hemiLight.groundColor.setHex(0x450a0a);
    env.hemiLight.intensity = 1.1;
    env.keyLight.color.setHex(0xffedd5);
    env.keyLight.intensity = 2.3;

    const lavaLakeGeo = new THREE.CircleGeometry(90, 36);
    lavaLakeGeo.rotateX(-Math.PI / 2);
    const lavaLakeMat = new THREE.MeshBasicMaterial({ color: 0xea580c });
    const lavaLake = new THREE.Mesh(lavaLakeGeo, lavaLakeMat);
    lavaLake.position.y = -0.35;
    env.stageGroup.add(lavaLake);

    for (const r of [11, 17, 25, 34]) {
      const lavaRingGeo = new THREE.RingGeometry(r, r + 1.1, 36);
      lavaRingGeo.rotateX(-Math.PI / 2);
      const lavaRing = new THREE.Mesh(
        lavaRingGeo,
        new THREE.MeshBasicMaterial({ color: 0xfde047, side: THREE.DoubleSide })
      );
      lavaRing.position.y = -0.32;
      env.stageGroup.add(lavaRing);
    }

    const redSunGroup = new THREE.Group();
    redSunGroup.position.set(0, 7.4, -21);
    const redSunCore = new THREE.Mesh(
      new THREE.CircleGeometry(6.4, 36),
      new THREE.MeshBasicMaterial({ color: 0xef4444 })
    );
    redSunGroup.add(redSunCore);

    const redSunInnerGlow = new THREE.Mesh(
      new THREE.CircleGeometry(4.4, 32),
      new THREE.MeshBasicMaterial({ color: 0xf97316 })
    );
    redSunInnerGlow.position.z = 0.05;
    redSunGroup.add(redSunInnerGlow);

    const redSunCorona = new THREE.Mesh(
      new THREE.RingGeometry(6.4, 8.1, 36),
      new THREE.MeshBasicMaterial({
        color: 0x991b1b,
        transparent: true,
        opacity: 0.72,
      })
    );
    redSunGroup.add(redSunCorona);
    env.stageGroup.add(redSunGroup);

    const cragSpecs = [
      { x: -15.5, z: -14.5, r: 4.2, h: 12.5 },
      { x: -9.8, z: -13.2, r: 3.4, h: 9.8 },
      { x: 9.8, z: -13.2, r: 3.4, h: 9.8 },
      { x: 15.5, z: -14.5, r: 4.2, h: 12.5 },
    ];
    for (const crag of cragSpecs) {
      const rock = toon(new THREE.ConeGeometry(crag.r, crag.h, 6), '#18181b', 0.025);
      rock.group.position.set(crag.x, crag.h * 0.45 - 0.5, crag.z);
      env.stageGroup.add(rock.group);

      const magmaCap = new THREE.Mesh(
        new THREE.ConeGeometry(crag.r * 0.35, crag.h * 0.28, 6),
        new THREE.MeshBasicMaterial({ color: 0xf97316 })
      );
      magmaCap.position.set(crag.x, crag.h * 0.82 - 0.5, crag.z);
      env.stageGroup.add(magmaCap);
    }

    const stageDeck = new THREE.Mesh(
      new THREE.BoxGeometry(24, 0.75, 8.4),
      new THREE.MeshToonMaterial({
        color: 0x18181b,
        gradientMap: env.toonGradientMap,
      })
    );
    stageDeck.position.set(0, -0.37, 0);
    env.stageGroup.add(stageDeck);

    for (let f = -4; f <= 4; f++) {
      const fissure = new THREE.Mesh(
        new THREE.BoxGeometry(0.14, 0.03, 7.6),
        new THREE.MeshBasicMaterial({
          color: f % 2 === 0 ? 0xf97316 : 0xef4444,
        })
      );
      fissure.position.set(f * 2.4, 0.01, 0);
      env.stageGroup.add(fissure);
    }

    const forgeCircle = new THREE.Mesh(
      new THREE.RingGeometry(1.6, 2.05, 24),
      new THREE.MeshBasicMaterial({ color: 0xf97316, side: THREE.DoubleSide })
    );
    forgeCircle.rotation.x = -Math.PI / 2;
    forgeCircle.position.set(0, 0.02, 0);
    env.stageGroup.add(forgeCircle);

    const trimFront = new THREE.Mesh(
      new THREE.BoxGeometry(24, 0.1, 0.24),
      new THREE.MeshBasicMaterial({ color: 0xef4444 })
    );
    trimFront.position.set(0, 0.01, 2.25);
    env.stageGroup.add(trimFront);

    for (const bx of [-8.8, -5.2, 5.2, 8.8]) {
      const col = toon(
        new THREE.CylinderGeometry(0.45, 0.58, 2.6, 6),
        '#27272a',
        0.03
      );
      col.group.position.set(bx, 1.3, -4.1);
      env.stageGroup.add(col.group);

      const brazierFlame = new THREE.Mesh(
        new THREE.OctahedronGeometry(0.48, 0),
        new THREE.MeshBasicMaterial({ color: 0xfde047 })
      );
      brazierFlame.position.set(bx, 2.95, -4.1);
      env.stageGroup.add(brazierFlame);
      env.torchFlames.push(brazierFlame);
    }

    const giantAnvilGroup = new THREE.Group();
    giantAnvilGroup.position.set(0, -0.3, -6.8);

    const altarPedestal = toon(
      new THREE.BoxGeometry(9.6, 0.85, 4.6),
      '#450a0a',
      0.03
    );
    altarPedestal.group.position.y = 0.2;
    giantAnvilGroup.add(altarPedestal.group);

    const anvilBase = toon(
      new THREE.BoxGeometry(7.8, 1.5, 3.6),
      '#27272a',
      0.03
    );
    anvilBase.group.position.y = 0.95;
    giantAnvilGroup.add(anvilBase.group);

    const anvilWaist = toon(
      new THREE.BoxGeometry(4.9, 1.95, 2.8),
      '#18181b',
      0.03
    );
    anvilWaist.group.position.y = 2.6;
    giantAnvilGroup.add(anvilWaist.group);

    const anvilTop = toon(
      new THREE.BoxGeometry(9.6, 1.75, 3.9),
      '#3f3f46',
      0.03
    );
    anvilTop.group.position.y = 4.3;
    giantAnvilGroup.add(anvilTop.group);

    const hornGeo = new THREE.ConeGeometry(1.2, 4.8, 12);
    hornGeo.rotateZ(Math.PI / 2);
    const anvilHorn = toon(hornGeo, '#3f3f46', 0.03);
    anvilHorn.group.position.set(-6.8, 4.35, 0);
    giantAnvilGroup.add(anvilHorn.group);

    const anvilHeel = toon(
      new THREE.BoxGeometry(2.4, 1.1, 3.2),
      '#3f3f46',
      0.03
    );
    anvilHeel.group.position.set(5.6, 4.4, 0);
    giantAnvilGroup.add(anvilHeel.group);

    const runeStrip = new THREE.Mesh(
      new THREE.BoxGeometry(9.2, 0.22, 4.0),
      new THREE.MeshBasicMaterial({ color: 0xf97316 })
    );
    runeStrip.position.set(0, 4.85, 0);
    giantAnvilGroup.add(runeStrip);

    for (const hSide of [-1, 1]) {
      const hammerGroup = new THREE.Group();
      hammerGroup.position.set(hSide * 2.4, 5.2, -1.6);
      hammerGroup.rotation.z = hSide * 0.48;

      const handle = toon(
        new THREE.CylinderGeometry(0.22, 0.26, 6.5, 8),
        '#451a03',
        0.03
      );
      hammerGroup.add(handle.group);

      const hammerHead = toon(
        new THREE.BoxGeometry(2.4, 1.35, 1.4),
        '#52525b',
        0.03
      );
      hammerHead.group.position.y = 2.9;
      hammerGroup.add(hammerHead.group);

      giantAnvilGroup.add(hammerGroup);
    }

    for (const cSide of [-1, 1]) {
      for (let link = 0; link < 6; link++) {
        const chainTorus = toon(
          new THREE.TorusGeometry(0.45, 0.13, 6, 12),
          '#27272a',
          0.025
        );
        chainTorus.group.position.set(
          cSide * (4.2 + link * 0.95),
          4.1 - link * 0.52,
          0.4
        );
        chainTorus.group.rotation.y = link % 2 === 0 ? 0 : Math.PI / 2;
        giantAnvilGroup.add(chainTorus.group);
      }
    }

    env.stageGroup.add(giantAnvilGroup);

    // Item 12: Stage Hazard Overdrive (Phase 3 Climax — Erupting Lava Geyser Pillars & Molten Halo)
    for (const gx of [-10.2, -6.5, 6.5, 10.2]) {
      const geyserGroup = new THREE.Group();
      geyserGroup.position.set(gx, -0.2, -5.4);
      geyserGroup.visible = false;

      const geyserPillar = new THREE.Mesh(
        new THREE.CylinderGeometry(0.45, 1.05, 7.8, 10, 1, true),
        new THREE.MeshBasicMaterial({
          color: 0xf97316,
          transparent: true,
          opacity: 0.72,
          side: THREE.DoubleSide,
        })
      );
      geyserPillar.position.y = 3.9;
      geyserGroup.add(geyserPillar);

      const coreJet = new THREE.Mesh(
        new THREE.ConeGeometry(0.55, 6.8, 8),
        new THREE.MeshBasicMaterial({ color: 0xfef08a })
      );
      coreJet.position.y = 3.4;
      geyserGroup.add(coreJet);

      env.stageGroup.add(geyserGroup);
      env.overdriveMeshes.push(geyserGroup);
    }
  } else {
    env.hemiLight.color.setHex(0xfef08a);
    env.hemiLight.groundColor.setHex(0xd97706);
    env.hemiLight.intensity = 1.38;
    env.keyLight.color.setHex(0xfde047);
    env.keyLight.intensity = 2.45;

    const outerFloor = new THREE.Mesh(
      new THREE.CircleGeometry(75, 36),
      new THREE.MeshBasicMaterial({ color: 0xb45309 })
    );
    outerFloor.rotation.x = -Math.PI / 2;
    outerFloor.position.y = -0.06;
    env.stageGroup.add(outerFloor);

    const stageDeck = new THREE.Mesh(
      new THREE.BoxGeometry(24, 0.4, 8.8),
      new THREE.MeshToonMaterial({
        color: 0xf59e0b,
        gradientMap: env.toonGradientMap,
      })
    );
    stageDeck.position.set(0, -0.2, 0);
    env.stageGroup.add(stageDeck);

    const carpetRunner = new THREE.Mesh(
      new THREE.BoxGeometry(20.5, 0.03, 3.8),
      new THREE.MeshToonMaterial({
        color: 0x991b1b,
        gradientMap: env.toonGradientMap,
      })
    );
    carpetRunner.position.set(0, 0.01, 0);
    env.stageGroup.add(carpetRunner);

    const carpetGoldBorder = new THREE.Mesh(
      new THREE.BoxGeometry(21.1, 0.02, 4.3),
      new THREE.MeshBasicMaterial({ color: 0xfacc15 })
    );
    carpetGoldBorder.position.set(0, 0.005, 0);
    env.stageGroup.add(carpetGoldBorder);

    const trimFront = new THREE.Mesh(
      new THREE.BoxGeometry(24, 0.09, 0.24),
      new THREE.MeshBasicMaterial({ color: 0xfde047 })
    );
    trimFront.position.set(0, 0.01, 2.25);
    env.stageGroup.add(trimFront);

    for (const zArch of [-2.8, -5.6, -8.4]) {
      for (const colSide of [-6.8, 6.8]) {
        const colShaft = toon(
          new THREE.CylinderGeometry(0.42, 0.48, 3.4, 10),
          '#d97706',
          0.025
        );
        colShaft.group.position.set(colSide, 1.7, zArch);
        env.stageGroup.add(colShaft.group);

        const colCap = toon(
          new THREE.BoxGeometry(1.15, 0.42, 1.15),
          '#fde047',
          0.025
        );
        colCap.group.position.set(colSide, 3.45, zArch);
        env.stageGroup.add(colCap.group);
      }

      const archRib = toon(
        new THREE.TorusGeometry(6.8, 0.44, 10, 28, Math.PI),
        '#fbbf24',
        0.025
      );
      archRib.group.position.set(0, 0.2, zArch);
      env.stageGroup.add(archRib.group);

      for (let b = 1; b < 11; b++) {
        const ang = (b / 11) * Math.PI;
        const stripeBlock = new THREE.Mesh(
          new THREE.BoxGeometry(0.56, 0.92, 0.94),
          new THREE.MeshBasicMaterial({
            color: b % 2 === 0 ? 0x292524 : 0xfef08a,
          })
        );
        stripeBlock.position.set(
          Math.cos(ang) * 6.8,
          Math.sin(ang) * 6.8 + 0.2,
          zArch
        );
        stripeBlock.rotation.z = ang - Math.PI / 2;
        env.stageGroup.add(stripeBlock);
      }

      for (const lx of [-3.4, 0, 3.4]) {
        const chainCord = new THREE.Mesh(
          new THREE.CylinderGeometry(0.03, 0.03, 1.6, 6),
          new THREE.MeshBasicMaterial({ color: 0x78350f })
        );
        chainCord.position.set(lx, 5.9, zArch);
        env.stageGroup.add(chainCord);

        const chandelierRing = new THREE.Mesh(
          new THREE.TorusGeometry(0.52, 0.05, 6, 16),
          new THREE.MeshBasicMaterial({ color: 0xfacc15 })
        );
        chandelierRing.rotation.x = Math.PI / 2;
        chandelierRing.position.set(lx, 5.15, zArch);
        env.stageGroup.add(chandelierRing);

        const lantern = new THREE.Mesh(
          new THREE.OctahedronGeometry(0.38, 0),
          new THREE.MeshBasicMaterial({ color: 0xfef08a })
        );
        lantern.position.set(lx, 5.15, zArch);
        env.stageGroup.add(lantern);
        env.torchFlames.push(lantern);
      }
    }

    for (const tapX of [-8.2, -5.4, 5.4, 8.2]) {
      const tapestry = toon(
        new THREE.BoxGeometry(1.55, 2.8, 0.08),
        Math.abs(tapX) > 7 ? '#b91c1c' : '#d97706',
        0.025
      );
      tapestry.group.position.set(tapX, 2.8, -4.85);
      env.stageGroup.add(tapestry.group);

      const innerMedallion = new THREE.Mesh(
        new THREE.OctahedronGeometry(0.45, 0),
        new THREE.MeshBasicMaterial({ color: 0xfef08a })
      );
      innerMedallion.scale.set(1, 1.4, 0.2);
      innerMedallion.position.set(tapX, 2.8, -4.78);
      env.stageGroup.add(innerMedallion);
    }

    const backWall = toon(
      new THREE.BoxGeometry(15.2, 7.6, 0.8),
      '#b45309',
      0.025
    );
    backWall.group.position.set(0, 3.8, -11.4);
    env.stageGroup.add(backWall.group);

    const portalArch = toon(
      new THREE.TorusGeometry(2.6, 0.36, 10, 24, Math.PI),
      '#fde047',
      0.03
    );
    portalArch.group.position.set(0, 2.6, -10.9);
    env.stageGroup.add(portalArch.group);

    const portalInnerGlow = new THREE.Mesh(
      new THREE.CircleGeometry(2.5, 24),
      new THREE.MeshBasicMaterial({ color: 0xfef08a })
    );
    portalInnerGlow.position.set(0, 2.5, -10.95);
    env.stageGroup.add(portalInnerGlow);

    for (const winX of [-3.6, 0, 3.6]) {
      const stainedWindow = new THREE.Mesh(
        new THREE.CircleGeometry(0.68, 16),
        new THREE.MeshBasicMaterial({ color: 0xfef08a })
      );
      stainedWindow.position.set(winX, 5.7, -10.92);
      env.stageGroup.add(stainedWindow);
    }

    const goldenDome = toon(
      new THREE.SphereGeometry(3.4, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.6),
      '#facc15',
      0.03
    );
    goldenDome.group.position.set(0, 7.4, -12.2);
    env.stageGroup.add(goldenDome.group);

    const domeSpire = toon(
      new THREE.ConeGeometry(0.28, 1.8, 8),
      '#fef08a',
      0.03
    );
    domeSpire.group.position.set(0, 11.2, -12.2);
    env.stageGroup.add(domeSpire.group);

    const spiceColors = [0xfacc15, 0xf59e0b, 0xef4444, 0xfde047, 0xd97706];
    for (let s = 0; s < 8; s++) {
      const sx = (s - 3.5) * 2.45;
      const mound = toon(
        new THREE.ConeGeometry(0.58, 0.68, 10),
        spiceColors[s % spiceColors.length],
        0.03
      );
      mound.group.position.set(sx, 0.34, -4.2);
      env.stageGroup.add(mound.group);

      if (s % 2 === 0) {
        const amphora = toon(
          new THREE.CylinderGeometry(0.16, 0.28, 0.78, 10),
          '#facc15',
          0.03
        );
        amphora.group.position.set(sx + 0.65, 0.39, -4.05);
        env.stageGroup.add(amphora.group);
      }
    }

    // Item 12: Stage Hazard Overdrive (Phase 3 Climax — Levitating Imperial Monolith Crystals & Thunder Coils)
    for (const ox of [-7.5, -3.8, 3.8, 7.5]) {
      const obeliskGroup = new THREE.Group();
      obeliskGroup.position.set(ox, 3.6, -4.2);
      obeliskGroup.visible = false;

      const crystal = new THREE.Mesh(
        new THREE.OctahedronGeometry(0.62, 0),
        new THREE.MeshBasicMaterial({ color: 0x06b6d4 })
      );
      crystal.scale.set(0.8, 1.65, 0.8);
      obeliskGroup.add(crystal);

      const halo = new THREE.Mesh(
        new THREE.TorusGeometry(0.95, 0.045, 6, 18),
        new THREE.MeshBasicMaterial({ color: 0xfacc15 })
      );
      halo.rotation.x = Math.PI * 0.35;
      obeliskGroup.add(halo);

      env.stageGroup.add(obeliskGroup);
      env.overdriveMeshes.push(obeliskGroup);
    }
  }

  for (let i = 0; i < 10; i++) {
    const xPos = (i - 4.5) * 2.1;
    const specGroup = new THREE.Group();
    specGroup.position.set(xPos, 0, -3.4 - (i % 2) * 0.4);

    const robeColor =
      stageId === 'storm_market'
        ? i % 2 === 0
          ? '#facc15'
          : '#d97706'
        : stageId === 'molten_forge'
        ? i % 2 === 0
          ? '#ef4444'
          : '#7f1d1d'
        : i % 2 === 0
        ? '#0284c7'
        : '#f8fafc';

    const body = toon(
      new THREE.CylinderGeometry(0.26, 0.32, 1.05, 8),
      robeColor,
      0.04
    );
    body.group.position.y = 0.52;
    specGroup.add(body.group);

    const head = toon(new THREE.SphereGeometry(0.2, 8, 8), '#fde68a', 0.04);
    head.group.position.y = 1.25;
    specGroup.add(head.group);

    const hat = toon(
      new THREE.ConeGeometry(0.38, 0.2, 8),
      stageId === 'storm_market' ? '#b45309' : '#1e293b',
      0.04
    );
    hat.group.position.y = 1.44;
    specGroup.add(hat.group);

    env.stageGroup.add(specGroup);
    env.spectatorGroups.push(specGroup);

    if (i % 2 === 0) {
      const stand = toon(
        new THREE.CylinderGeometry(0.2, 0.28, 1.5, 8),
        '#475569',
        0.03
      );
      stand.group.position.set(xPos + 0.9, 0.75, -3.1);
      env.stageGroup.add(stand.group);

      const flameGeo = new THREE.OctahedronGeometry(0.3, 0);
      const flameMat = new THREE.MeshBasicMaterial({ color: stage.accentColor });
      const flame = new THREE.Mesh(flameGeo, flameMat);
      flame.position.set(xPos + 0.9, 1.8, -3.1);
      env.stageGroup.add(flame);
      env.torchFlames.push(flame);
    }
  }

  for (const h of hazards) {
    const entry = buildHazardMesh(env.toonGradientMap, h);
    env.stageGroup.add(entry.group);
    env.hazardMeshes.set(h.id, entry);
  }
}

export function buildHazardMesh(
  toonGradientMap: THREE.DataTexture,
  hazard: PropHazard
): HazardMeshEntry {
  const group = new THREE.Group();
  const outlineMeshes: THREE.Mesh[] = [];

  const shadowGeo = new THREE.CircleGeometry(hazard.radius * 0.95, 16);
  shadowGeo.rotateX(-Math.PI / 2);
  const shadowMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.38,
    depthWrite: false,
  });
  const shadow = new THREE.Mesh(shadowGeo, shadowMat);
  shadow.position.y = 0.015;
  group.add(shadow);

  let mainMat!: THREE.MeshToonMaterial;

  if (hazard.kind === 'stone_pillar') {
    const base = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.BoxGeometry(0.9, 0.3, 0.9),
      '#64748b',
      0.035,
      outlineMeshes
    );
    base.group.position.y = 0.15;
    group.add(base.group);

    const shaft = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.CylinderGeometry(0.38, 0.42, 1.8, 8),
      '#94a3b8',
      0.035,
      outlineMeshes
    );
    shaft.group.position.y = 1.05;
    mainMat = shaft.mat;
    group.add(shaft.group);

    const cap = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.BoxGeometry(0.88, 0.25, 0.88),
      '#475569',
      0.035,
      outlineMeshes
    );
    cap.group.position.y = 2.05;
    group.add(cap.group);
  } else if (hazard.kind === 'lantern' || hazard.kind === 'magma_brazier') {
    const color = hazard.kind === 'magma_brazier' ? '#f97316' : '#10b981';
    const pedestal = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.CylinderGeometry(0.24, 0.34, 0.48, 8),
      '#475569',
      0.04,
      outlineMeshes
    );
    pedestal.group.position.y = 0.24;
    group.add(pedestal.group);

    const core = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.OctahedronGeometry(0.38, 0),
      color,
      0.045,
      outlineMeshes
    );
    core.group.position.y = 0.82;
    mainMat = core.mat;
    group.add(core.group);

    const roof = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.ConeGeometry(0.5, 0.3, 6),
      '#1e293b',
      0.04,
      outlineMeshes
    );
    roof.group.position.y = 1.22;
    group.add(roof.group);
  } else {
    const isOrb = hazard.kind === 'wind_orb';
    const geo = isOrb
      ? new THREE.IcosahedronGeometry(0.45, 1)
      : new THREE.BoxGeometry(0.78, 0.78, 0.78);
    const color = isOrb ? '#38bdf8' : '#d97706';
    const body = createToonMeshWithOutline(
      toonGradientMap,
      geo,
      color,
      0.04,
      outlineMeshes
    );
    body.group.position.y = 0.45;
    mainMat = body.mat;
    group.add(body.group);

    const band = createToonMeshWithOutline(
      toonGradientMap,
      new THREE.TorusGeometry(0.42, 0.045, 6, 16),
      '#090b10',
      0.02,
      outlineMeshes
    );
    band.group.position.y = 0.45;
    group.add(band.group);
  }

  return {
    group,
    mainMat,
    baseColor: mainMat.color.getHex(),
    outlineMeshes,
  };
}

export function updateStageOverdrive(
  env: StageEnvironmentRefs,
  stageId: StageId | null,
  stagePhase: 1 | 2 | 3,
  elapsed: number
) {
  const isOverdrive = stagePhase === 3;
  for (let i = 0; i < env.overdriveMeshes.length; i++) {
    const obj = env.overdriveMeshes[i];
    obj.visible = isOverdrive;
    if (!isOverdrive) continue;

    if (stageId === 'zephyr_dojo') {
      obj.rotation.y = elapsed * (i % 2 === 0 ? 4.5 : -4.5);
      obj.scale.setScalar(0.95 + Math.sin(elapsed * 6 + i) * 0.12);
    } else if (stageId === 'molten_forge') {
      obj.rotation.y = elapsed * 3.2;
      const pulse = 0.85 + Math.abs(Math.sin(elapsed * 7.5 + i * 1.4)) * 0.45;
      obj.scale.set(1, pulse, 1);
    } else {
      obj.position.y = 3.6 + Math.sin(elapsed * 4.2 + i * 1.2) * 0.42;
      obj.rotation.y = elapsed * 2.8;
    }
  }
}
