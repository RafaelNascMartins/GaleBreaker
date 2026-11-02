import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { FIGHTERS, getFighterPalette } from './fighters';
import { updateFighterMesh } from './render/fighterAnimator';
import { applyPaletteToMesh, buildFighterModel } from './render/fighterBuilder';
import { ImpactSparkPool } from './render/impactSparkPool';
import { disposeObjectResources } from './render/disposeResources';
import {
  HazardMeshEntry,
  HitboxOverlayPair,
  isSoftwareGl,
  RiggedFighterMesh,
  StageEnvironmentRefs,
} from './render/renderTypes';
import { rebuildStageGeometry, updateStageOverdrive } from './render/stageBuilder';
import {
  BoundingBox2D,
  CombatSnapshot,
  FighterId,
  FighterRuntimeState,
  GameScreenState,
  GameSettings,
  ImpactSparkType,
  MoveType,
  PropHazard,
  StageId,
} from './types';

export { isSoftwareGl };

// Reusable scratch math objects at module scope (Zero GC in render loop)
const _vec3A = new THREE.Vector3();
const _vec3B = new THREE.Vector3();
const _mat4 = new THREE.Matrix4();
const _quat = new THREE.Quaternion();
const _euler = new THREE.Euler();
const _scale = new THREE.Vector3();
const _color = new THREE.Color();

const PARTICLE_POOL_SIZE = 120;
const LINEUP_IDS: FighterId[] = ['kaze', 'ignis', 'tophia', 'volt'];
const LINEUP_X_POSITIONS: Record<FighterId, number> = {
  kaze: -3.45,
  ignis: -1.15,
  tophia: 1.15,
  volt: 3.45,
};

interface PooledParticle {
  active: boolean;
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  rx: number;
  ry: number;
  scale: number;
  life: number;
  maxLife: number;
  colorHex: number;
}

export class CelArenaRenderer {
  public renderer: THREE.WebGLRenderer;
  public scene: THREE.Scene;
  public cameraP1: THREE.PerspectiveCamera;
  private toonGradientMap: THREE.DataTexture;
  private floorBumpTexture: THREE.CanvasTexture;
  private environmentTarget: THREE.WebGLRenderTarget;
  private particleDensityScale = 1;

  private p1Mesh: RiggedFighterMesh | null = null;
  private p2Mesh: RiggedFighterMesh | null = null;
  private currentP1Id: FighterId | null = null;
  private currentP2Id: FighterId | null = null;
  private currentStageId: StageId | null = null;

  // Outdoor Character Selection Lineup (all 4 fighters standing together outside the arena)
  private lineupGroup: THREE.Group;
  private lineupFighters: Map<FighterId, RiggedFighterMesh> = new Map();
  private lineupPedestals: Map<FighterId, THREE.Mesh> = new Map();
  private selectedLineupFighter: FighterId = 'kaze';
  private selectedLineupPalette = 0;
  private chosenAnimActive = false;
  private chosenAnimTime = 0;
  private previewLineupMove: MoveType | null = null;
  private previewLineupTimer = 0;

  // 2D Hitbox & Hurtbox visualization overlays
  private p1BoxOverlay: HitboxOverlayPair;
  private p2BoxOverlay: HitboxOverlayPair;

  private stageGroup: THREE.Group;
  private hazardMeshes: Map<string, HazardMeshEntry> = new Map();
  private spectatorGroups: THREE.Group[] = [];
  private torchFlames: THREE.Mesh[] = [];
  private cloudGroups: THREE.Group[] = [];
  private overdriveMeshes: THREE.Object3D[] = [];
  private keyLight: THREE.DirectionalLight;
  private hemiLight: THREE.HemisphereLight;
  private combatPointLight: THREE.PointLight;
  private combatLightIntensity = 0;
  private impactFrameGroup: THREE.Group;
  private impactFrameSlashMat: THREE.MeshBasicMaterial;
  private impactFrameRingMat: THREE.MeshBasicMaterial;
  private stageEnvRefs: StageEnvironmentRefs;

  // Pooled InstancedMesh particle & debris system + 3D Impact Spark Pool
  private particleInstancedMesh: THREE.InstancedMesh;
  private particles: PooledParticle[] = [];
  private particleCursor = 0;
  private impactSparkPool: ImpactSparkPool;

  // Camera shake & 2D Street Fighter tracking state
  private cameraTrauma = 0;
  private camSmoothedPos = new THREE.Vector3(0, 1.85, 7.6);
  private camSmoothedLook = new THREE.Vector3(0, 1.35, 0);

  constructor(container: HTMLElement) {
    this.renderer = new THREE.WebGLRenderer({
      antialias: !isSoftwareGl,
      powerPreference: 'high-performance',
    });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.12;
    this.renderer.setPixelRatio(isSoftwareGl ? 1 : Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = !isSoftwareGl;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.setSize(
      container.clientWidth || window.innerWidth,
      container.clientHeight || window.innerHeight
    );

    container.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();

    const pmremGenerator = new THREE.PMREMGenerator(this.renderer);
    const room = new RoomEnvironment();
    this.environmentTarget = pmremGenerator.fromScene(room, 0.04);
    this.scene.environment = this.environmentTarget.texture;
    room.dispose();
    pmremGenerator.dispose();

    const aspect =
      (container.clientWidth || window.innerWidth) /
      (container.clientHeight || window.innerHeight);
    this.cameraP1 = new THREE.PerspectiveCamera(48, aspect, 0.1, 160);
    this.scene.add(this.cameraP1);

    // 4-step Cel-Shaded Toon Gradient Texture
    const steps = new Uint8Array([65, 140, 210, 255]);
    this.toonGradientMap = new THREE.DataTexture(steps, 4, 1, THREE.RedFormat);
    this.toonGradientMap.minFilter = THREE.NearestFilter;
    this.toonGradientMap.magFilter = THREE.NearestFilter;
    this.toonGradientMap.needsUpdate = true;

    this.floorBumpTexture = this.createProceduralArenaFloorTexture();

    // Balanced Studio 3-Point Rig
    this.hemiLight = new THREE.HemisphereLight(0x93c5fd, 0x1e293b, 0.95);
    this.scene.add(this.hemiLight);

    this.keyLight = new THREE.DirectionalLight(0xfffbeb, 2.2);
    this.keyLight.position.set(8, 18, 16);
    this.keyLight.castShadow = !isSoftwareGl;
    this.keyLight.shadow.mapSize.set(1024, 1024);
    this.keyLight.shadow.camera.left = -14;
    this.keyLight.shadow.camera.right = 14;
    this.keyLight.shadow.camera.top = 12;
    this.keyLight.shadow.camera.bottom = -12;
    this.keyLight.shadow.camera.near = 1;
    this.keyLight.shadow.camera.far = 50;
    this.keyLight.shadow.bias = -0.0005;
    this.keyLight.shadow.normalBias = 0.02;
    this.scene.add(this.keyLight);

    const rimLight = new THREE.DirectionalLight(0x38bdf8, 1.25);
    rimLight.position.set(-10, 12, -10);
    this.scene.add(rimLight);

    // Item 8: Dynamic Elemental Point Light for Strikes & Hitsparks (Zero-GC)
    this.combatPointLight = new THREE.PointLight(0x38bdf8, 0, 7.5, 1.8);
    this.combatPointLight.position.set(0, 1.5, 1.0);
    this.scene.add(this.combatPointLight);

    // Item 6: High-Contrast Anime Impact Frame Flash Assembly (Zero-GC)
    this.impactFrameGroup = new THREE.Group();
    this.impactFrameGroup.visible = false;
    const slashBeamGeo = new THREE.PlaneGeometry(24, 0.55);
    this.impactFrameSlashMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.95,
      side: THREE.DoubleSide,
      depthTest: false,
    });
    const slashBeam = new THREE.Mesh(slashBeamGeo, this.impactFrameSlashMat);
    slashBeam.rotation.z = 0.28;
    this.impactFrameGroup.add(slashBeam);

    const flashRingGeo = new THREE.RingGeometry(1.4, 3.8, 24);
    this.impactFrameRingMat = new THREE.MeshBasicMaterial({
      color: 0xf43f5e,
      transparent: true,
      opacity: 0.88,
      side: THREE.DoubleSide,
      depthTest: false,
    });
    const flashRing = new THREE.Mesh(flashRingGeo, this.impactFrameRingMat);
    this.impactFrameGroup.add(flashRing);
    this.scene.add(this.impactFrameGroup);

    this.stageGroup = new THREE.Group();
    this.scene.add(this.stageGroup);

    this.stageEnvRefs = {
      scene: this.scene,
      stageGroup: this.stageGroup,
      spectatorGroups: this.spectatorGroups,
      torchFlames: this.torchFlames,
      cloudGroups: this.cloudGroups,
      overdriveMeshes: this.overdriveMeshes,
      hazardMeshes: this.hazardMeshes,
      hemiLight: this.hemiLight,
      keyLight: this.keyLight,
      toonGradientMap: this.toonGradientMap,
    };

    // Build 3D Outdoor Lineup Group for Character Select
    this.lineupGroup = new THREE.Group();
    this.lineupGroup.visible = false;
    this.scene.add(this.lineupGroup);
    this.buildOutdoorSelectLineup();

    // Build 2D Hitbox & Hurtbox wireframe overlay meshes
    this.p1BoxOverlay = this.createHitboxOverlayPair(0x10b981, 0xef4444);
    this.p2BoxOverlay = this.createHitboxOverlayPair(0x38bdf8, 0xf97316);

    // Pooled 3D Directional Hitsparks & Shockwaves
    this.impactSparkPool = new ImpactSparkPool(this.scene);

    // Pooled InstancedMesh for Debris & Elemental Bursts
    const debrisGeo = new THREE.DodecahedronGeometry(0.18, 0);
    const debrisMat = new THREE.MeshToonMaterial({
      color: 0xffffff,
      gradientMap: this.toonGradientMap,
    });
    this.particleInstancedMesh = new THREE.InstancedMesh(
      debrisGeo,
      debrisMat,
      PARTICLE_POOL_SIZE
    );
    this.particleInstancedMesh.frustumCulled = false;
    this.scene.add(this.particleInstancedMesh);

    for (let i = 0; i < PARTICLE_POOL_SIZE; i++) {
      this.particles.push({
        active: false,
        x: 0,
        y: -50,
        z: 0,
        vx: 0,
        vy: 0,
        vz: 0,
        rx: 0,
        ry: 0,
        scale: 0.001,
        life: 0,
        maxLife: 1,
        colorHex: 0xffffff,
      });
      _mat4.makeTranslation(0, -50, 0);
      this.particleInstancedMesh.setMatrixAt(i, _mat4);
      this.particleInstancedMesh.setColorAt(i, _color.setHex(0xffffff));
    }
    this.particleInstancedMesh.instanceMatrix.needsUpdate = true;
    if (this.particleInstancedMesh.instanceColor) {
      this.particleInstancedMesh.instanceColor.needsUpdate = true;
    }
  }

  private createHitboxOverlayPair(
    hurtColor: number,
    hitColor: number
  ): HitboxOverlayPair {
    const planeGeo = new THREE.PlaneGeometry(1, 1);
    const hurtMat = new THREE.MeshBasicMaterial({
      color: hurtColor,
      wireframe: true,
      transparent: true,
      opacity: 0.45,
      depthTest: false,
    });
    const hitMat = new THREE.MeshBasicMaterial({
      color: hitColor,
      transparent: true,
      opacity: 0.38,
      side: THREE.DoubleSide,
      depthTest: false,
    });

    const hurtboxMesh = new THREE.Mesh(planeGeo, hurtMat);
    const hitboxMesh = new THREE.Mesh(planeGeo, hitMat);
    hurtboxMesh.visible = false;
    hitboxMesh.visible = false;
    this.scene.add(hurtboxMesh);
    this.scene.add(hitboxMesh);
    return { hurtboxMesh, hitboxMesh };
  }

  private updateBoxOverlay(
    pair: HitboxOverlayPair,
    hurtbox: BoundingBox2D,
    hitbox: BoundingBox2D | null,
    visible: boolean
  ) {
    pair.hurtboxMesh.visible = visible;
    if (visible) {
      pair.hurtboxMesh.position.set(hurtbox.x, hurtbox.y, 0.35);
      pair.hurtboxMesh.scale.set(hurtbox.width, hurtbox.height, 1);
    }
    if (visible && hitbox) {
      pair.hitboxMesh.visible = true;
      pair.hitboxMesh.position.set(hitbox.x, hitbox.y, 0.4);
      pair.hitboxMesh.scale.set(hitbox.width, hitbox.height, 1);
    } else {
      pair.hitboxMesh.visible = false;
    }
  }

  private buildOutdoorSelectLineup() {
    for (const id of LINEUP_IDS) {
      const def = FIGHTERS[id];
      const xPos = LINEUP_X_POSITIONS[id];

      const pedGeo = new THREE.CylinderGeometry(0.88, 1.02, 0.22, 20);
      const pedMat = new THREE.MeshToonMaterial({
        color: 0x1e293b,
        gradientMap: this.toonGradientMap,
      });
      const ped = new THREE.Mesh(pedGeo, pedMat);
      ped.position.set(xPos, -0.11, 1.2);
      this.lineupGroup.add(ped);

      const ringGeo = new THREE.RingGeometry(0.92, 1.15, 28);
      ringGeo.rotateX(-Math.PI / 2);
      const ringMat = new THREE.MeshBasicMaterial({
        color: def.primaryColor,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.85,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.set(xPos, 0.02, 1.2);
      this.lineupGroup.add(ring);
      this.lineupPedestals.set(id, ring);

      const fighterMesh = buildFighterModel(id, this.toonGradientMap, 0);
      fighterMesh.root.position.set(xPos, 0, 1.2);
      fighterMesh.root.rotation.y = 0;
      this.lineupGroup.add(fighterMesh.root);
      this.lineupFighters.set(id, fighterMesh);
    }
  }

  public setLineupSelection(
    fighterId: FighterId,
    isChosen: boolean,
    paletteIndex = 0
  ) {
    if (this.selectedLineupFighter !== fighterId) {
      const prevMesh = this.lineupFighters.get(this.selectedLineupFighter);
      if (prevMesh && prevMesh.paletteIndex !== 0) {
        applyPaletteToMesh(prevMesh, 0);
      }
      this.selectedLineupFighter = fighterId;
    }
    this.selectedLineupPalette = paletteIndex;
    const selMesh = this.lineupFighters.get(fighterId);
    if (selMesh && selMesh.paletteIndex !== paletteIndex) {
      applyPaletteToMesh(selMesh, paletteIndex);
    }

    if (isChosen && !this.chosenAnimActive) {
      this.chosenAnimActive = true;
      this.chosenAnimTime = 0;
      const xPos = LINEUP_X_POSITIONS[fighterId];
      const pal = getFighterPalette(fighterId, paletteIndex);
      const colorHex = new THREE.Color(pal.swatch[0]).getHex();
      this.spawnBurstParticles(xPos, 1.4, 1.2, colorHex, 28);
    } else if (!isChosen) {
      this.chosenAnimActive = false;
      this.chosenAnimTime = 0;
    }
  }

  public triggerLineupMovePreview(moveType: MoveType) {
    this.previewLineupMove = moveType;
    this.previewLineupTimer = 0.58;
    const xPos = LINEUP_X_POSITIONS[this.selectedLineupFighter];
    const pal = getFighterPalette(this.selectedLineupFighter, this.selectedLineupPalette);
    const colorHex = Number(pal.swatch[0].replace('#', '0x')) || 0x10b981;
    this.spawnBurstParticles(xPos + 0.45, 1.25, 1.35, colorHex, 12);
    this.combatPointLight.color.setHex(colorHex);
    this.combatPointLight.position.set(xPos + 0.4, 1.4, 1.8);
    this.combatLightIntensity = 4.2;
  }

  private createProceduralArenaFloorTexture(): THREE.CanvasTexture {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = '#334155';
    ctx.fillRect(0, 0, 512, 512);

    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 6;
    for (let i = 0; i <= 512; i += 64) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, 512);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(512, i);
      ctx.stroke();
    }

    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 2;
    ctx.strokeRect(12, 12, 488, 488);

    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(8, 4);
    tex.anisotropy = this.renderer.capabilities.getMaxAnisotropy();
    return tex;
  }

  public syncStageAndFighters(
    stageId: StageId,
    p1Id: FighterId,
    p2Id: FighterId,
    hazards: PropHazard[],
    p1Palette = 0,
    p2Palette = 0
  ) {
    if (this.currentStageId !== stageId) {
      this.currentStageId = stageId;
      rebuildStageGeometry(this.stageEnvRefs, stageId, hazards);
    }

    if (this.currentP1Id !== p1Id || !this.p1Mesh) {
      this.currentP1Id = p1Id;
      if (this.p1Mesh) {
        this.scene.remove(this.p1Mesh.root);
        disposeObjectResources(this.p1Mesh.root);
      }
      this.p1Mesh = buildFighterModel(p1Id, this.toonGradientMap, p1Palette);
      this.scene.add(this.p1Mesh.root);
    } else if (this.p1Mesh.paletteIndex !== p1Palette) {
      applyPaletteToMesh(this.p1Mesh, p1Palette);
    }

    if (this.currentP2Id !== p2Id || !this.p2Mesh) {
      this.currentP2Id = p2Id;
      if (this.p2Mesh) {
        this.scene.remove(this.p2Mesh.root);
        disposeObjectResources(this.p2Mesh.root);
      }
      this.p2Mesh = buildFighterModel(p2Id, this.toonGradientMap, p2Palette);
      this.scene.add(this.p2Mesh.root);
    } else if (this.p2Mesh.paletteIndex !== p2Palette) {
      applyPaletteToMesh(this.p2Mesh, p2Palette);
    }
  }

  public spawnImpactSpark(
    x: number,
    y: number,
    z: number,
    type: ImpactSparkType,
    accentColorHex = 0x38bdf8
  ) {
    this.impactSparkPool.spawn(x, y, z, type, accentColorHex);
    // Item 8: Pulse Dynamic Point Light at exact collision point
    this.combatPointLight.color.setHex(
      type === 'parry' || type === 'clash' ? 0xfacc15 : accentColorHex
    );
    this.combatPointLight.position.set(x, y, z + 0.9);
    this.combatLightIntensity =
      type === 'clash' || type === 'heavy' || type === 'wall' ? 6.5 : 3.8;
  }

  public spawnFloorCrack(
    x: number,
    z: number,
    accentColorHex = 0xf97316,
    scale = 1.15
  ) {
    this.impactSparkPool.spawnFloorCrack(x, z, accentColorHex, scale);
  }

  public spawnBurstParticles(
    x: number,
    y: number,
    z: number,
    colorHex: number,
    count: number
  ) {
    for (let i = 0; i < Math.round(count * this.particleDensityScale); i++) {
      const p = this.particles[this.particleCursor];
      this.particleCursor = (this.particleCursor + 1) % PARTICLE_POOL_SIZE;
      const angle = Math.random() * Math.PI * 2;
      const speed = 2.5 + Math.random() * 8.5;
      p.active = true;
      p.x = x;
      p.y = y + (Math.random() - 0.3) * 0.6;
      p.z = z;
      p.vx = Math.cos(angle) * speed;
      p.vy = 2.8 + Math.random() * 6.5;
      p.vz = (Math.random() - 0.5) * 3.0;
      p.rx = Math.random() * 6;
      p.ry = Math.random() * 6;
      p.scale = 0.55 + Math.random() * 0.95;
      p.life = 0;
      p.maxLife = 0.35 + Math.random() * 0.4;
      p.colorHex = colorHex;
    }
  }

  public addCameraTrauma(amount: number) {
    this.cameraTrauma = Math.min(1, this.cameraTrauma + amount);
  }

  public updateAndRender(
    snapshot: CombatSnapshot,
    screenState: GameScreenState,
    settings: GameSettings,
    dt: number,
    elapsed: number
  ) {
    const isSelectScreen = screenState === 'select';
    this.particleDensityScale = settings.particleDensity === 'low' ? 0.25 : settings.particleDensity === 'medium' ? 0.5 : 1;
    if (this.cameraP1.fov !== settings.fov) {
      this.cameraP1.fov = settings.fov;
      this.cameraP1.updateProjectionMatrix();
    }
    this.lineupGroup.visible = isSelectScreen;

    if (isSelectScreen) {
      if (this.p1Mesh) this.p1Mesh.root.visible = false;
      if (this.p2Mesh) this.p2Mesh.root.visible = false;
      this.updateBoxOverlay(this.p1BoxOverlay, snapshot.p1.hurtbox, null, false);
      this.updateBoxOverlay(this.p2BoxOverlay, snapshot.p2.hurtbox, null, false);

      if (this.chosenAnimActive) {
        this.chosenAnimTime += dt;
      }
      if (this.previewLineupTimer > 0) {
        this.previewLineupTimer = Math.max(0, this.previewLineupTimer - dt);
        if (this.previewLineupTimer === 0) {
          this.previewLineupMove = null;
        }
      }

      for (const id of LINEUP_IDS) {
        const mesh = this.lineupFighters.get(id);
        const ring = this.lineupPedestals.get(id);
        if (!mesh || !ring) continue;

        const isSelected = id === this.selectedLineupFighter;
        const isChosen = isSelected && this.chosenAnimActive;
        const isPreviewingMove = isSelected && !isChosen && this.previewLineupMove !== null;
        const xPos = LINEUP_X_POSITIONS[id];

        ring.scale.setScalar(isSelected ? 1.25 + Math.sin(elapsed * 8) * 0.08 : 0.85);
        (ring.material as THREE.MeshBasicMaterial).opacity = isSelected ? 1.0 : 0.28;

        const previewMoveData = isPreviewingMove
          ? FIGHTERS[id].moves[this.previewLineupMove!]
          : null;
        const previewProgress = isPreviewingMove ? 1 - this.previewLineupTimer / 0.58 : 0;

        const dummyState: FighterRuntimeState = {
          ...snapshot.p1,
          id,
          paletteIndex: isSelected ? this.selectedLineupPalette : 0,
          x: xPos,
          y: isChosen
            ? Math.max(0, Math.sin(Math.min(1, this.chosenAnimTime * 2.2) * Math.PI) * 1.15)
            : isPreviewingMove && this.previewLineupMove === 'air_punch'
            ? Math.sin(previewProgress * Math.PI) * 0.65
            : 0,
          z: 1.2,
          vx: 0,
          vy: 0,
          vz: 0,
          facingRight: true,
          grounded: !isChosen && !(isPreviewingMove && this.previewLineupMove === 'air_punch'),
          crouching: isPreviewingMove && this.previewLineupMove === 'down_punch',
          action: isChosen
            ? 'active'
            : isPreviewingMove
            ? previewProgress < 0.25
              ? 'startup'
              : 'active'
            : 'idle',
          actionTimerFrames: isChosen
            ? 5
            : isPreviewingMove
            ? Math.max(1, Math.round((1 - previewProgress) * 10))
            : 0,
          actionTotalFrames: 10,
          currentMove: isChosen
            ? FIGHTERS[id].moves.ultimate
            : previewMoveData,
          hitFlashTimer: 0,
        };

        updateFighterMesh(mesh, dummyState, elapsed, settings.celOutlines);
        mesh.root.rotation.y = isChosen
          ? this.chosenAnimTime * 6.28
          : isSelected
          ? 0.12
          : 0;
      }
    } else {
      const isIntroClash =
        screenState === 'playing' && snapshot.countdownTimer > 1.0;
      const isVictoryPodium =
        screenState === 'gameover' && snapshot.winner !== 0 && snapshot.koSlowMoTimer <= 0;

      if (this.p1Mesh) {
        this.p1Mesh.root.visible = true;
        const p1RenderState: FighterRuntimeState =
          isIntroClash && snapshot.countdownTimer >= 2.0
            ? {
                ...snapshot.p1,
                action: 'active',
                actionTimerFrames: 4,
                actionTotalFrames: 10,
                currentMove: FIGHTERS[snapshot.p1.id].moves.elemental,
              }
            : isVictoryPodium && snapshot.winner === 1
            ? {
                ...snapshot.p1,
                action: 'active',
                actionTimerFrames: 5,
                actionTotalFrames: 10,
                currentMove: FIGHTERS[snapshot.p1.id].moves.ultimate,
              }
            : snapshot.p1;
        updateFighterMesh(this.p1Mesh, p1RenderState, elapsed, settings.celOutlines);
      }
      if (this.p2Mesh) {
        this.p2Mesh.root.visible = true;
        const p2RenderState: FighterRuntimeState =
          isIntroClash && snapshot.countdownTimer < 2.0
            ? {
                ...snapshot.p2,
                action: 'active',
                actionTimerFrames: 4,
                actionTotalFrames: 10,
                currentMove: FIGHTERS[snapshot.p2.id].moves.heavy,
              }
            : isVictoryPodium && snapshot.winner === 2
            ? {
                ...snapshot.p2,
                action: 'active',
                actionTimerFrames: 5,
                actionTotalFrames: 10,
                currentMove: FIGHTERS[snapshot.p2.id].moves.ultimate,
              }
            : snapshot.p2;
        updateFighterMesh(this.p2Mesh, p2RenderState, elapsed, settings.celOutlines);
      }

      if (screenState === 'playing' && snapshot.hitstopTimerMs <= 0) {
        for (const f of [snapshot.p1, snapshot.p2]) {
          const isChargingHeavy =
            f.action === 'startup' &&
            (f.currentMove?.type === 'heavy' ||
              f.currentMove?.type === 'elemental' ||
              f.currentMove?.type === 'ultimate');
          if (f.action === 'active' || isChargingHeavy) {
            const pal = getFighterPalette(f.id, f.paletteIndex);
            const useAccent = Math.random() > 0.45;
            const hexStr = (useAccent ? pal.swatch[2] : pal.swatch[0]).replace(
              '#',
              '0x'
            );
            const colorHex = Number(hexStr) || 0x10b981;
            const dir = f.facingRight ? 1 : -1;
            const reachOffset =
              f.action === 'active'
                ? 0.85 + Math.random() * (f.currentMove?.range ?? 1.8) * 0.55
                : 0.35;
            this.spawnBurstParticles(
              f.x + dir * reachOffset,
              f.y + 0.95 + Math.random() * 0.55,
              f.z + (Math.random() - 0.5) * 0.35,
              colorHex,
              f.action === 'active' ? 2 : 1
            );
          }
        }
      }

      const showBoxes =
        settings.showHitboxes &&
        (screenState === 'playing' || screenState === 'paused') &&
        snapshot.countdownTimer <= 0;
      this.updateBoxOverlay(
        this.p1BoxOverlay,
        snapshot.p1.hurtbox,
        snapshot.p1.activeHitbox,
        showBoxes
      );
      this.updateBoxOverlay(
        this.p2BoxOverlay,
        snapshot.p2.hurtbox,
        snapshot.p2.activeHitbox,
        showBoxes
      );
    }

    // Update destructible hazards (hidden during outdoor select lineup)
    for (const h of snapshot.hazards) {
      const entry = this.hazardMeshes.get(h.id);
      if (!entry) continue;
      entry.group.visible = !isSelectScreen && !h.destroyed;
      if (!h.destroyed && !isSelectScreen) {
        entry.group.position.set(h.x, 0, h.z);
        const speed = Math.abs(h.vx);
        if (speed > 0.5) {
          entry.group.rotation.z -= dt * h.vx * 1.2;
        }
        entry.mainMat.color.setHex(h.hitFlash > 0 ? 0xffffff : entry.baseColor);
        for (const om of entry.outlineMeshes) {
          om.visible = settings.celOutlines;
        }
      }
    }

    // Drift mountain clouds gently
    for (let i = 0; i < this.cloudGroups.length; i++) {
      const cloud = this.cloudGroups[i];
      cloud.position.x += Math.sin(elapsed * 0.3 + i) * 0.4 * dt;
    }

    // Item 12: Animate Stage Hazard Overdrive in Phase 3 Climax
    updateStageOverdrive(
      this.stageEnvRefs,
      this.currentStageId,
      isSelectScreen ? 1 : snapshot.stagePhase,
      elapsed
    );

    // Item 1 & Item 6: Dim ambient light dramatically during Ultimate Super Flash OR Anime Impact Frame!
    const baseHemiIntensity =
      this.currentStageId === 'storm_market'
        ? 1.38
        : this.currentStageId === 'zephyr_dojo'
        ? 1.28
        : 1.1;
    const isImpactFrameActive = snapshot.impactFrameTimer > 0 && !isSelectScreen;
    this.hemiLight.intensity = isImpactFrameActive
      ? 0.08
      : snapshot.cinematicTimer > 0 && !isSelectScreen
      ? 0.35
      : baseHemiIntensity;

    // Item 6: Update High-Contrast Anime Impact Frame geometry
    this.impactFrameGroup.visible = isImpactFrameActive;
    if (isImpactFrameActive) {
      const midImpactX = (snapshot.p1.x + snapshot.p2.x) * 0.5;
      const midImpactY = Math.max(snapshot.p1.y, snapshot.p2.y) + 1.25;
      this.impactFrameGroup.position.set(midImpactX, midImpactY, -0.35);
      this.impactFrameGroup.rotation.z = Math.sin(elapsed * 90) * 0.35;
      this.impactFrameRingMat.color.setHex(snapshot.impactFrameColorHex || 0xf43f5e);
    }

    // Item 8: Decay Dynamic Combat Point Light smoothly
    if (this.combatLightIntensity > 0) {
      this.combatLightIntensity = Math.max(0, this.combatLightIntensity - dt * 16.0);
      this.combatPointLight.intensity = this.combatLightIntensity;
    } else {
      this.combatPointLight.intensity = 0;
    }

    // Update background spectators & stage climax lighting
    const excitement = snapshot.spectatorExcitement;
    const bounceSpeed = 4 + excitement * 12;
    const bounceAmp = 0.06 + excitement * 0.24;
    for (let i = 0; i < this.spectatorGroups.length; i++) {
      const spec = this.spectatorGroups[i];
      spec.position.y = Math.abs(Math.sin(elapsed * bounceSpeed + i * 1.1)) * bounceAmp;
    }

    const flameScale = 0.8 + snapshot.stagePhase * 0.35 + Math.sin(elapsed * 14) * 0.15;
    for (const flame of this.torchFlames) {
      flame.scale.setScalar(flameScale);
      flame.rotation.y += dt * 3.5;
    }

    // Step pooled 3D Hitsparks & Shockwaves
    this.impactSparkPool.update(dt);

    // Step pooled InstancedMesh particles
    for (let i = 0; i < PARTICLE_POOL_SIZE; i++) {
      const p = this.particles[i];
      if (!p.active) continue;
      p.life += dt;
      if (p.life >= p.maxLife) {
        p.active = false;
        _mat4.makeTranslation(0, -50, 0);
        this.particleInstancedMesh.setMatrixAt(i, _mat4);
        continue;
      }
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.z += p.vz * dt;
      p.vy -= 16.5 * dt;
      if (p.y < 0.1) {
        p.y = 0.1;
        p.vy *= -0.45;
      }
      const progress = p.life / p.maxLife;
      const s = p.scale * (1 - progress);
      _vec3A.set(p.x, p.y, p.z);
      _euler.set(p.rx + p.life * 8, p.ry + p.life * 8, 0);
      _quat.setFromEuler(_euler);
      _scale.setScalar(Math.max(0.001, s));
      _mat4.compose(_vec3A, _quat, _scale);
      this.particleInstancedMesh.setMatrixAt(i, _mat4);
      this.particleInstancedMesh.setColorAt(i, _color.setHex(p.colorHex));
    }
    this.particleInstancedMesh.instanceMatrix.needsUpdate = true;
    if (this.particleInstancedMesh.instanceColor) {
      this.particleInstancedMesh.instanceColor.needsUpdate = true;
    }

    // Camera Framing (including Item 1 Cinematic Ultimate Zoom & K.O. Zoom)
    this.cameraTrauma = Math.max(0, this.cameraTrauma - dt * 2.6);
    const shakeMag = settings.cameraShake ? this.cameraTrauma * this.cameraTrauma * 0.24 : 0;
    const shakeX = (Math.random() - 0.5) * 2 * shakeMag;
    const shakeY = (Math.random() - 0.5) * 2 * shakeMag;

    const midX = (snapshot.p1.x + snapshot.p2.x) * 0.5;
    const maxY = Math.max(snapshot.p1.y, snapshot.p2.y);
    const sep = Math.abs(snapshot.p1.x - snapshot.p2.x);

    if (isSelectScreen) {
      const selX = LINEUP_X_POSITIONS[this.selectedLineupFighter] * 0.22;
      _vec3A.set(selX, 1.65, 7.6);
      _vec3B.set(selX * 0.5, 1.15, 1.2);
      this.camSmoothedPos.lerp(_vec3A, 1 - Math.exp(-10 * dt));
      this.camSmoothedLook.lerp(_vec3B, 1 - Math.exp(-10 * dt));
    } else if (screenState === 'title') {
      // Item 16: Live 3D Showcase Diorama Camera (frames the two fighters on the right half of the viewport)
      const orbitX = Math.sin(elapsed * 0.55) * 0.95 - 1.15;
      const orbitY = 1.45 + Math.cos(elapsed * 0.4) * 0.12;
      _vec3A.set(orbitX, orbitY, 5.15);
      _vec3B.set(-1.05, 1.18, 0);
      this.camSmoothedPos.lerp(_vec3A, 1 - Math.exp(-8 * dt));
      this.camSmoothedLook.lerp(_vec3B, 1 - Math.exp(-8 * dt));
    } else if (screenState === 'loading') {
      const swayX = Math.sin(elapsed * 0.45) * 1.4;
      _vec3A.set(swayX, 2.1, 7.4);
      _vec3B.set(0, 1.35, 0);
      this.camSmoothedPos.lerp(_vec3A, 1 - Math.exp(-8 * dt));
      this.camSmoothedLook.lerp(_vec3B, 1 - Math.exp(-8 * dt));
    } else if (snapshot.cinematicTimer > 0 && snapshot.cinematicFocusPlayer !== 0) {
      // Item 1: Heroic Super Flash Zoom-In on the Ultimate Caster
      const focusFighter =
        snapshot.cinematicFocusPlayer === 1 ? snapshot.p1 : snapshot.p2;
      const sideOffset = focusFighter.facingRight ? 0.55 : -0.55;
      _vec3A.set(focusFighter.x + sideOffset, focusFighter.y + 1.45, 4.15);
      _vec3B.set(focusFighter.x + sideOffset * 0.35, focusFighter.y + 1.18, 0);
      const damp = 1 - Math.exp(-22 * dt);
      this.camSmoothedPos.lerp(_vec3A, damp);
      this.camSmoothedLook.lerp(_vec3B, damp);
    } else if (screenState === 'playing' && snapshot.countdownTimer > 0) {
      // Item 9: Interactive Stage Intro Camera Pan during 3..2..1..FIGHT!
      if (snapshot.countdownTimer >= 2.0) {
        // 3.0s -> 2.0s: Low-angle heroic close-up on P1
        _vec3A.set(snapshot.p1.x + 0.65, 1.32, 4.35);
        _vec3B.set(snapshot.p1.x + 0.15, 1.18, 0);
      } else if (snapshot.countdownTimer >= 1.0) {
        // 2.0s -> 1.0s: Whip-pan to P2 (Rival / Boss)
        _vec3A.set(snapshot.p2.x - 0.65, 1.38, 4.35);
        _vec3B.set(snapshot.p2.x - 0.15, 1.22, 0);
      } else {
        // 1.0s -> 0.0s: Pull back smoothly to combat framing on "FIGHT!"
        _vec3A.set(midX, 1.65, 7.6);
        _vec3B.set(midX, 1.22, 0);
      }
      const damp = 1 - Math.exp(-11 * dt);
      this.camSmoothedPos.lerp(_vec3A, damp);
      this.camSmoothedLook.lerp(_vec3B, damp);
    } else if (screenState === 'gameover' && snapshot.winner !== 0 && snapshot.koSlowMoTimer <= 0) {
      // Item 10: Post-Match Victory Podium Close-up (frames the winner on the left side of the screen)
      const winnerFighter = snapshot.winner === 1 ? snapshot.p1 : snapshot.p2;
      _vec3A.set(winnerFighter.x + 1.15, 1.28, 3.85);
      _vec3B.set(winnerFighter.x + 0.95, 1.15, 0);
      const damp = 1 - Math.exp(-7 * dt);
      this.camSmoothedPos.lerp(_vec3A, damp);
      this.camSmoothedLook.lerp(_vec3B, damp);
    } else {
      const baseZoom = settings.dynamicZoom
        ? Math.max(6.4, Math.min(10.8, 5.4 + sep * 0.55))
        : 7.8;
      const zoomDist = snapshot.koSlowMoTimer > 0 ? baseZoom * 0.82 : baseZoom;
      const targetCamY = 1.65 + maxY * 0.42;
      const targetLookY = 1.22 + maxY * 0.48;

      _vec3A.set(midX, targetCamY, zoomDist);
      _vec3B.set(midX, targetLookY, 0);

      const damp = 1 - Math.exp(-14 * dt);
      this.camSmoothedPos.lerp(_vec3A, damp);
      this.camSmoothedLook.lerp(_vec3B, damp);
    }

    this.cameraP1.position.set(
      this.camSmoothedPos.x + shakeX,
      this.camSmoothedPos.y + shakeY,
      this.camSmoothedPos.z
    );
    this.cameraP1.lookAt(this.camSmoothedLook);

    const canvas = this.renderer.domElement;
    const w = canvas.clientWidth || window.innerWidth;
    const h = canvas.clientHeight || window.innerHeight;
    this.cameraP1.aspect = w / h;
    this.cameraP1.updateProjectionMatrix();
    this.renderer.setViewport(0, 0, w, h);
    this.renderer.render(this.scene, this.cameraP1);
  }

  public handleResize(width: number, height: number) {
    this.cameraP1.aspect = width / height;
    this.cameraP1.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  public dispose() {
    disposeObjectResources(this.scene);
    this.environmentTarget.dispose();
    this.toonGradientMap.dispose();
    this.floorBumpTexture.dispose();
    this.scene.clear();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}
