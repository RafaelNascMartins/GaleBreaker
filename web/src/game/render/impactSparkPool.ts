import * as THREE from 'three';
import { ImpactSparkType } from '../types';

const SPARK_POOL_SIZE = 8;
const STREAKS_PER_SPARK = 6;
const FLOOR_CRACK_POOL_SIZE = 6;
const FISSURES_PER_CRACK = 5;

interface PooledFloorCrack {
  active: boolean;
  life: number;
  maxLife: number;
  baseScale: number;
  group: THREE.Group;
  outerRingMat: THREE.MeshBasicMaterial;
  coreDiscMat: THREE.MeshBasicMaterial;
  fissureMat: THREE.MeshBasicMaterial;
}

interface PooledImpactSpark {
  active: boolean;
  type: ImpactSparkType;
  life: number;
  maxLife: number;
  targetScale: number;
  group: THREE.Group;
  ringMesh: THREE.Mesh;
  ringMat: THREE.MeshBasicMaterial;
  coreMesh: THREE.Mesh;
  coreMat: THREE.MeshBasicMaterial;
  streakPivot: THREE.Group;
  streakMeshes: THREE.Mesh[];
  streakMat: THREE.MeshBasicMaterial;
}

export class ImpactSparkPool {
  private pool: PooledImpactSpark[] = [];
  private cursor = 0;
  private crackPool: PooledFloorCrack[] = [];
  private crackCursor = 0;

  constructor(scene: THREE.Scene) {
    const ringGeo = new THREE.RingGeometry(0.42, 0.68, 24);
    const coreGeo = new THREE.OctahedronGeometry(0.38, 0);
    coreGeo.scale(1, 1, 0.25);
    const streakGeo = new THREE.ConeGeometry(0.075, 0.85, 4);
    streakGeo.translate(0, 0.425, 0);

    for (let i = 0; i < SPARK_POOL_SIZE; i++) {
      const group = new THREE.Group();
      group.visible = false;

      const ringMat = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.9,
        depthWrite: false,
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      group.add(ringMesh);

      const coreMat = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.95,
        depthWrite: false,
      });
      const coreMesh = new THREE.Mesh(coreGeo, coreMat);
      group.add(coreMesh);

      const streakMat = new THREE.MeshBasicMaterial({
        color: 0xfef08a,
        transparent: true,
        opacity: 0.9,
        depthWrite: false,
      });
      const streakPivot = new THREE.Group();
      const streakMeshes: THREE.Mesh[] = [];
      for (let s = 0; s < STREAKS_PER_SPARK; s++) {
        const sMesh = new THREE.Mesh(streakGeo, streakMat);
        sMesh.rotation.z = (s / STREAKS_PER_SPARK) * Math.PI * 2;
        streakPivot.add(sMesh);
        streakMeshes.push(sMesh);
      }
      group.add(streakPivot);

      scene.add(group);
      this.pool.push({
        active: false,
        type: 'hit',
        life: 0,
        maxLife: 0.2,
        targetScale: 1.4,
        group,
        ringMesh,
        ringMat,
        coreMesh,
        coreMat,
        streakPivot,
        streakMeshes,
        streakMat,
      });
    }

    // Item 7: Pre-allocate 6 Floor Impact Cracks & Elemental Scars (Zero-GC)
    const crackRingGeo = new THREE.RingGeometry(0.55, 1.05, 7);
    crackRingGeo.rotateX(-Math.PI * 0.5);
    const crackCoreGeo = new THREE.CircleGeometry(0.55, 7);
    crackCoreGeo.rotateX(-Math.PI * 0.5);
    const fissureGeo = new THREE.PlaneGeometry(0.11, 1.25);
    fissureGeo.translate(0, 0.55, 0);
    fissureGeo.rotateX(-Math.PI * 0.5);

    for (let c = 0; c < FLOOR_CRACK_POOL_SIZE; c++) {
      const crackGroup = new THREE.Group();
      crackGroup.visible = false;

      const outerRingMat = new THREE.MeshBasicMaterial({
        color: 0x0f172a,
        transparent: true,
        opacity: 0.85,
        depthWrite: false,
      });
      const outerRing = new THREE.Mesh(crackRingGeo, outerRingMat);
      crackGroup.add(outerRing);

      const coreDiscMat = new THREE.MeshBasicMaterial({
        color: 0xf97316,
        transparent: true,
        opacity: 0.72,
        depthWrite: false,
      });
      const coreDisc = new THREE.Mesh(crackCoreGeo, coreDiscMat);
      coreDisc.position.y = 0.002;
      crackGroup.add(coreDisc);

      const fissureMat = new THREE.MeshBasicMaterial({
        color: 0xfef08a,
        transparent: true,
        opacity: 0.9,
        depthWrite: false,
      });
      for (let f = 0; f < FISSURES_PER_CRACK; f++) {
        const fisMesh = new THREE.Mesh(fissureGeo, fissureMat);
        fisMesh.rotation.y = (f / FISSURES_PER_CRACK) * Math.PI * 2 + f * 0.27;
        fisMesh.position.y = 0.004;
        crackGroup.add(fisMesh);
      }

      scene.add(crackGroup);
      this.crackPool.push({
        active: false,
        life: 0,
        maxLife: 3.4,
        baseScale: 1.0,
        group: crackGroup,
        outerRingMat,
        coreDiscMat,
        fissureMat,
      });
    }
  }

  public spawnFloorCrack(
    x: number,
    z: number,
    accentColorHex = 0xf97316,
    scale = 1.15
  ) {
    const slot = this.crackPool[this.crackCursor];
    this.crackCursor = (this.crackCursor + 1) % FLOOR_CRACK_POOL_SIZE;

    slot.active = true;
    slot.life = 0;
    slot.maxLife = 3.4;
    slot.baseScale = scale;

    slot.group.position.set(x, 0.018, z);
    slot.group.rotation.y = Math.random() * Math.PI * 2;
    slot.group.scale.setScalar(scale * 0.55);
    slot.group.visible = true;

    slot.coreDiscMat.color.setHex(accentColorHex);
    slot.fissureMat.color.setHex(0xffffff);
    slot.outerRingMat.opacity = 0.85;
    slot.coreDiscMat.opacity = 0.75;
    slot.fissureMat.opacity = 0.92;
  }

  public spawn(
    x: number,
    y: number,
    z: number,
    type: ImpactSparkType,
    accentColorHex = 0x38bdf8
  ) {
    const entry = this.pool[this.cursor];
    this.cursor = (this.cursor + 1) % SPARK_POOL_SIZE;

    entry.active = true;
    entry.type = type;
    entry.life = 0;

    entry.group.position.set(x, y, z + 0.45);
    entry.group.rotation.set(0, 0, Math.random() * Math.PI);
    entry.group.visible = true;

    if (type === 'hit') {
      entry.maxLife = 0.18;
      entry.targetScale = 1.25;
      entry.ringMat.color.setHex(accentColorHex);
      entry.coreMat.color.setHex(0xffffff);
      entry.streakMat.color.setHex(accentColorHex);
    } else if (type === 'heavy') {
      entry.maxLife = 0.28;
      entry.targetScale = 2.15;
      entry.ringMat.color.setHex(accentColorHex);
      entry.coreMat.color.setHex(0xfef08a);
      entry.streakMat.color.setHex(0xffffff);
    } else if (type === 'block') {
      entry.maxLife = 0.2;
      entry.targetScale = 1.45;
      entry.ringMat.color.setHex(0x38bdf8);
      entry.coreMat.color.setHex(0xe0f2fe);
      entry.streakMat.color.setHex(0x7dd3fc);
    } else if (type === 'parry') {
      entry.maxLife = 0.34;
      entry.targetScale = 2.55;
      entry.ringMat.color.setHex(0xfacc15);
      entry.coreMat.color.setHex(0xffffff);
      entry.streakMat.color.setHex(0xfef08a);
    } else if (type === 'clash') {
      entry.maxLife = 0.38;
      entry.targetScale = 2.95;
      entry.ringMat.color.setHex(0xe879f9);
      entry.coreMat.color.setHex(0xffffff);
      entry.streakMat.color.setHex(0xfacc15);
    } else {
      // 'wall' bounce shockwave
      entry.maxLife = 0.32;
      entry.targetScale = 2.35;
      entry.ringMat.color.setHex(0xf97316);
      entry.coreMat.color.setHex(0xfef08a);
      entry.streakMat.color.setHex(0xfb923c);
      entry.group.rotation.y = x >= 0 ? -Math.PI * 0.32 : Math.PI * 0.32;
    }

    entry.ringMesh.scale.setScalar(0.25);
    entry.coreMesh.scale.setScalar(0.35);
    for (let s = 0; s < STREAKS_PER_SPARK; s++) {
      const angle = (s / STREAKS_PER_SPARK) * Math.PI * 2;
      const sm = entry.streakMeshes[s];
      sm.position.set(0, 0, 0);
      sm.rotation.z = angle;
      sm.scale.set(1, 0.5, 1);
    }
  }

  public update(dt: number) {
    for (let i = 0; i < SPARK_POOL_SIZE; i++) {
      const entry = this.pool[i];
      if (!entry.active) continue;

      entry.life += dt;
      if (entry.life >= entry.maxLife) {
        entry.active = false;
        entry.group.visible = false;
        continue;
      }

      const t = entry.life / entry.maxLife;
      const easeOut = 1 - Math.pow(1 - t, 3);
      const fade = Math.max(0, 1 - t);

      const ringScale = 0.25 + easeOut * entry.targetScale;
      entry.ringMesh.scale.setScalar(ringScale);
      entry.ringMat.opacity = fade * 0.92;

      const coreScale =
        t < 0.28
          ? 0.35 + (t / 0.28) * entry.targetScale * 0.85
          : entry.targetScale * 0.85 * (1 - (t - 0.28) / 0.72);
      entry.coreMesh.scale.setScalar(Math.max(0.01, coreScale));
      entry.coreMesh.rotation.z += dt * 8.5;
      entry.coreMat.opacity = fade;

      entry.streakMat.opacity = fade * 0.95;
      const radialDist = easeOut * entry.targetScale * 0.65;
      for (let s = 0; s < STREAKS_PER_SPARK; s++) {
        const sm = entry.streakMeshes[s];
        const angle = sm.rotation.z + Math.PI * 0.5;
        sm.position.set(
          Math.cos(angle) * radialDist,
          Math.sin(angle) * radialDist,
          0
        );
        sm.scale.set(
          Math.max(0.15, 1 - t * 0.65),
          0.45 + easeOut * (entry.type === 'clash' || entry.type === 'heavy' ? 1.25 : 0.75),
          1
        );
      }
    }

    // Step floor cracks & scorch marks
    for (let c = 0; c < FLOOR_CRACK_POOL_SIZE; c++) {
      const slot = this.crackPool[c];
      if (!slot.active) continue;

      slot.life += dt;
      if (slot.life >= slot.maxLife) {
        slot.active = false;
        slot.group.visible = false;
        continue;
      }

      const t = slot.life / slot.maxLife;
      const expand = t < 0.08 ? 0.55 + (t / 0.08) * 0.45 : 1.0;
      slot.group.scale.setScalar(slot.baseScale * expand);
      const fade = t < 0.55 ? 1.0 : Math.max(0, 1 - (t - 0.55) / 0.45);
      slot.outerRingMat.opacity = 0.82 * fade;
      slot.coreDiscMat.opacity = 0.68 * fade;
      slot.fissureMat.opacity = 0.88 * Math.max(0, 1 - t * 1.2);
    }
  }
}
