import * as THREE from 'three';
import { FighterId } from '../types';

export const isSoftwareGl = (() => {
  if (typeof document === 'undefined') return true;
  const gl = document.createElement('canvas').getContext('webgl2');
  if (!gl) return true;
  const ext = gl.getExtension('WEBGL_debug_renderer_info');
  const param = ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER;
  const gpu = String(gl.getParameter(param));
  gl.getExtension('WEBGL_lose_context')?.loseContext();
  return /SwiftShader|llvmpipe|softpipe|Software|Basic Render/i.test(gpu);
})();

export interface ArticulatedLimb {
  upper: THREE.Group;
  lower: THREE.Group;
  extremity: THREE.Group;
}

export interface RiggedFighterMesh {
  id: FighterId;
  paletteIndex: number;
  root: THREE.Group;
  shadowDisc: THREE.Mesh;
  auraRing: THREE.Mesh;
  hipsGroup: THREE.Group;
  torsoGroup: THREE.Group;
  headGroup: THREE.Group;
  hairTailGroup: THREE.Group;
  capeOrCoatGroup: THREE.Group;
  backAccessoryGroup: THREE.Group;
  leftArm: ArticulatedLimb;
  rightArm: ArticulatedLimb;
  leftLeg: ArticulatedLimb;
  rightLeg: ArticulatedLimb;
  leftHandAura: THREE.Group;
  rightHandAura: THREE.Group;
  kickFootAura: THREE.Group;
  slashEffectGroup: THREE.Group;
  blastEffectGroup: THREE.Group;
  launcherEffectGroup: THREE.Group;
  slashArcMesh: THREE.Mesh;
  blastWaveMesh: THREE.Mesh;
  launcherPillarMesh: THREE.Mesh;
  guardShieldMesh: THREE.Mesh;
  groundShockRingMesh: THREE.Mesh;
  superAuraCylMesh: THREE.Mesh;
  handAuraMats: THREE.MeshBasicMaterial[];
  footAuraMats: THREE.MeshBasicMaterial[];
  slashVfxMats: THREE.MeshBasicMaterial[];
  blastVfxMats: THREE.MeshBasicMaterial[];
  launcherVfxMats: THREE.MeshBasicMaterial[];
  hitFlashMaterials: THREE.MeshToonMaterial[];
  originalBaseColors: number[];
  baseColors: number[];
  outlineMeshes: THREE.Mesh[];
}

export interface HazardMeshEntry {
  group: THREE.Group;
  mainMat: THREE.MeshToonMaterial;
  baseColor: number;
  outlineMeshes: THREE.Mesh[];
}

export interface HitboxOverlayPair {
  hurtboxMesh: THREE.Mesh;
  hitboxMesh: THREE.Mesh;
}

export interface StageEnvironmentRefs {
  scene: THREE.Scene;
  stageGroup: THREE.Group;
  spectatorGroups: THREE.Group[];
  torchFlames: THREE.Mesh[];
  cloudGroups: THREE.Group[];
  overdriveMeshes: THREE.Object3D[];
  hazardMeshes: Map<string, HazardMeshEntry>;
  hemiLight: THREE.HemisphereLight;
  keyLight: THREE.DirectionalLight;
  toonGradientMap: THREE.DataTexture;
}

export function createToonMeshWithOutline(
  toonGradientMap: THREE.DataTexture,
  geometry: THREE.BufferGeometry,
  colorHex: string | number,
  outlineThickness = 0.038,
  outlineBucket?: THREE.Mesh[]
): { group: THREE.Group; mat: THREE.MeshToonMaterial; mesh: THREE.Mesh } {
  const group = new THREE.Group();
  const mat = new THREE.MeshToonMaterial({
    color: colorHex,
    gradientMap: toonGradientMap,
  });
  const mesh = new THREE.Mesh(geometry, mat);
  mesh.castShadow = !isSoftwareGl;
  mesh.receiveShadow = !isSoftwareGl;
  group.add(mesh);

  const outlineMat = new THREE.MeshBasicMaterial({
    color: 0x090b10,
    side: THREE.BackSide,
  });
  const outlineMesh = new THREE.Mesh(geometry, outlineMat);
  outlineMesh.scale.setScalar(1 + outlineThickness);
  group.add(outlineMesh);
  if (outlineBucket) {
    outlineBucket.push(outlineMesh);
  }

  return { group, mat, mesh };
}
