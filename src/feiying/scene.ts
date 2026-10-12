import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { clamp, poseAt, screenPosition, wedgePlanes, type Pose, type Vec3 } from './timeline';

export type LabelId = 'spire' | 'outer' | 'inner' | 'base' | 'dou' | 'gong' | 'ang';
type Part = { node: THREE.Object3D; origin: THREE.Vector3; direction: THREE.Vector3; distance: number };

export type FeiyingSceneOptions = {
  reducedMotion: boolean;
  onLoadProgress?: (fraction: number) => void;
  onReady?: () => void;
  onError?: (error: unknown) => void;
  /** Called every rendered frame with projected label positions (CSS px, or null when hidden). */
  onLabels?: (labels: Partial<Record<LabelId, [number, number] | null>>) => void;
};

const BASE = import.meta.env.BASE_URL;
// Blender Z-up → three Y-up, for the light positions copied from render_shots.py.
const fromBlender = (x: number, y: number, z: number) => new THREE.Vector3(x, z, -y);

export class FeiyingScene {
  private renderer: THREE.WebGLRenderer;
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(36, 1, 0.5, 600);
  private env: THREE.WebGLRenderTarget;
  private tower: THREE.Object3D | null = null;
  private dougong: THREE.Object3D | null = null;
  private dougongOrigin: Vec3 = [0, 0, 0];
  private parts: Part[] = [];
  private named = new Map<string, THREE.Object3D>();
  private clip = [new THREE.Plane(), new THREE.Plane()];
  private progress = 0;
  private shown: Pose | null = null;
  private frame = 0;
  private visible = true;
  private dirty = true;
  private disposed = false;
  private controls: OrbitControls | null = null;
  private manual = { explode: 0, cut: 0 };
  private resizeObserver: ResizeObserver;

  constructor(private host: HTMLElement, private opts: FeiyingSceneOptions) {
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    const small = Math.min(window.innerWidth, window.innerHeight) < 720;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, small ? 1.5 : 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    // Match the approved Blender render (render_shots.py): ACES gives the contrast that
    // Blender's "AgX Medium High Contrast" look has; three's plain AgX reads flat and milky.
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.renderer.localClippingEnabled = true;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.domElement.className = 'feiying-canvas';
    this.renderer.domElement.setAttribute('aria-hidden', 'true');
    host.appendChild(this.renderer.domElement);

    // Image-based fill from the same dark gradient as the Blender world (ink-teal zenith,
    // faint warm horizon). A white studio environment is what made the tower look fogged.
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    const sky = new THREE.Scene();
    sky.add(new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false,
      vertexShader: 'varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader: `varying vec3 vDir;
        void main(){
          float h = clamp((vDir.y + 0.05) / 0.6, 0.0, 1.0);
          vec3 horizon = vec3(0.06, 0.04, 0.026), zenith = vec3(0.008, 0.024, 0.026), ground = vec3(0.012, 0.012, 0.011);
          vec3 c = vDir.y < -0.05 ? ground : mix(horizon, zenith, h);
          gl_FragColor = vec4(c, 1.0);
        }`,
    })));
    this.env = pmrem.fromScene(sky, 0);
    pmrem.dispose();
    this.scene.environment = this.env.texture;
    this.scene.environmentIntensity = 1.0;

    // Same sun rig as the Blender shots: warm low key from back-left (rim + shadows),
    // warm front so the facade reads, cool fill. Intensities follow the Blender sun strengths.
    const light = (pos: THREE.Vector3, color: number, intensity: number) => {
      const l = new THREE.DirectionalLight(color, intensity);
      l.position.copy(pos);
      l.target.position.set(0, 14, 0);
      this.scene.add(l, l.target);
      return l;
    };
    const key = light(fromBlender(-55, 40, 18), 0xffad66, 5.2);
    const front = light(fromBlender(-30, -60, 30), 0xffcc99, 2.0);
    light(fromBlender(50, -30, 40), 0x8cbfe6, 0.5);
    for (const l of [key, front]) {
      l.castShadow = true;
      l.shadow.mapSize.set(small ? 1024 : 2048, small ? 1024 : 2048);
      Object.assign(l.shadow.camera, { left: -40, right: 40, top: 60, bottom: -30, near: 1, far: 220 });
      l.shadow.bias = -0.0004;
      l.shadow.normalBias = 0.06;
    }

    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(host);
    this.resize();
    this.load(small);
  }

  private load(small: boolean) {
    const draco = new DRACOLoader().setDecoderPath(`${BASE}draco/`);
    const loader = new GLTFLoader().setDRACOLoader(draco);
    loader.load(`${BASE}models/feiying/feiying${small ? '-mobile' : ''}.glb`, (gltf) => {
      draco.dispose();
      if (this.disposed) return;
      this.setup(gltf.scene);
      this.opts.onReady?.();
    }, (event) => {
      if (event.total) this.opts.onLoadProgress?.(event.loaded / event.total);
    }, (error) => {
      draco.dispose();
      if (!this.disposed) this.opts.onError?.(error);
    });
  }

  private setup(root: THREE.Object3D) {
    this.scene.add(root);
    root.traverse((node) => {
      if (node.name) this.named.set(node.name, node);
      // explodeDirection is authored in Blender's Z-up frame; extras are not axis-converted.
      const raw = node.userData.explodeDirection;
      const distance = node.userData.explodeDistance;
      if (Array.isArray(raw) && typeof distance === 'number') {
        this.parts.push({ node, origin: node.position.clone(),
          direction: new THREE.Vector3(raw[0], raw[2], -raw[1]).normalize(), distance });
      }
    });
    this.tower = this.named.get('feiying_tower') ?? null;
    this.dougong = this.named.get('细部_斗栱') ?? null;
    if (!this.tower || !this.dougong || this.parts.length < 8) throw new Error('feiying.glb is missing tower parts');
    const o = this.dougong.position;
    this.dougongOrigin = [o.x, o.y, o.z];

    // Only the outer timber shell is cut away; the stone pagoda and spire stay whole.
    const outer = this.named.get('outer_tower');
    const patched = new Set<THREE.Material>();
    outer?.traverse((node) => {
      if (!(node instanceof THREE.Mesh)) return;
      for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
        if (patched.has(material)) continue;
        patched.add(material);
        material.side = THREE.DoubleSide;
        material.clippingPlanes = this.clip;
        material.clipIntersection = true;
        // Inside faces seen through the cut read as dark timber rather than lit facade.
        material.onBeforeCompile = (shader: THREE.WebGLProgramParametersWithUniforms) => {
          shader.fragmentShader = shader.fragmentShader.replace('#include <dithering_fragment>',
            '#include <dithering_fragment>\n  if (!gl_FrontFacing) gl_FragColor.rgb *= vec3(0.32, 0.22, 0.18);');
        };
        material.needsUpdate = true;
      }
    });
    const anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
    root.traverse((node) => {
      if (!(node instanceof THREE.Mesh)) return;
      // Eaves shading the floors below is most of what made the Blender shots read as real.
      node.castShadow = true;
      // The stone pagoda stands inside the timber shell; in Blender bounce light keeps it
      // readable. Without GI here, letting it skip the shell's shadow plays that role.
      let inner = false;
      for (let p: THREE.Object3D | null = node; p; p = p.parent) if (p.name === '内塔_石塔') inner = true;
      node.receiveShadow = !inner;
      const material = node.material as THREE.MeshStandardMaterial;
      for (const map of [material.map, material.roughnessMap, material.metalnessMap]) if (map) map.anisotropy = anisotropy;
    });
    this.dirty = true;
    this.loop();
    // Read-only probe for scripts/verify-feiying.mjs (reverse-scroll and return-to-origin checks).
    (window as unknown as { __feiyingDebug?: () => unknown }).__feiyingDebug = () => ({
      camera: this.camera.position.toArray().map((v) => Number(v.toFixed(3))),
      maxOffset: Math.max(...this.parts.map((p) => p.node.position.distanceTo(p.origin))),
    });
  }

  setProgress(progress: number) {
    const next = clamp(progress);
    if (next !== this.progress) { this.progress = next; this.dirty = true; }
  }

  setVisible(visible: boolean) {
    this.visible = visible;
    if (visible) { this.dirty = true; this.loop(); } else cancelAnimationFrame(this.frame);
  }

  /** Free-view mode: orbit / zoom with pointer or touch, plus manual explode and cut. */
  setFreeView(on: boolean) {
    if (on && !this.controls) {
      this.controls = new OrbitControls(this.camera, this.renderer.domElement);
      this.controls.target.set(0, 18, 0);
      this.controls.enablePan = false;
      this.controls.enableDamping = !this.opts.reducedMotion;
      this.controls.minDistance = 18;
      this.controls.maxDistance = 140;
      this.controls.maxPolarAngle = Math.PI * 0.62;
      this.camera.clearViewOffset();
      this.manual = { explode: 0, cut: 0 };
      this.controls.addEventListener('change', () => { this.dirty = true; });
    } else if (!on && this.controls) {
      this.controls.dispose();
      this.controls = null;
      this.shown = null; // snap back to the scroll-driven pose
    }
    this.renderer.domElement.style.pointerEvents = on ? 'auto' : 'none';
    this.dirty = true;
  }

  setManual(explode: number, cut: number) { this.manual = { explode, cut }; this.dirty = true; }

  private target(): Pose {
    const s = screenPosition(this.progress);
    return poseAt(s, this.dougongOrigin);
  }

  private apply(pose: Pose) {
    const { camera } = this;
    for (const part of this.parts) part.node.position.copy(part.origin).addScaledVector(part.direction, part.distance * pose.explode);
    const onTower = pose.subject === 'tower';
    if (this.tower) this.tower.visible = onTower;
    if (this.dougong) this.dougong.visible = !onTower;
    // Slow drift so held shots are never frozen; a function of progress, so it reverses exactly.
    if (!this.opts.reducedMotion) {
      if (this.tower) this.tower.rotation.y = this.progress * 0.9;
      if (this.dougong) this.dougong.rotation.y = -0.25 + this.progress * 0.5;
    }
    if (!this.controls) {
      camera.position.set(...pose.position);
      camera.lookAt(new THREE.Vector3(...pose.target));
      camera.fov = pose.fov;
      const w = this.host.clientWidth, h = this.host.clientHeight;
      const portrait = w < h;
      // Portrait: widen and step back so the subject fits the narrow frame, and shift it up
      // so the copy block sits below it (tutorial 5.6: model above, text below).
      if (portrait) {
        camera.fov = Math.min(68, pose.fov * 1.2);
        const back = new THREE.Vector3(...pose.position).sub(new THREE.Vector3(...pose.target)).multiplyScalar(0.35);
        camera.position.add(back);
      }
      camera.setViewOffset(w, h, portrait ? 0 : pose.shiftX * w, portrait ? h * 0.12 : 0, w, h);
      camera.updateProjectionMatrix();
    }
    const opening = this.controls ? this.manual.cut : pose.cut;
    const { normals, constant } = wedgePlanes([camera.position.x, camera.position.y, camera.position.z], opening);
    this.clip[0].set(new THREE.Vector3(...normals[0]), -constant);
    this.clip[1].set(new THREE.Vector3(...normals[1]), -constant);
    if (this.controls) {
      for (const part of this.parts) part.node.position.copy(part.origin).addScaledVector(part.direction, part.distance * this.manual.explode);
    }
    // The black dip layer is a sibling of the canvas host, so publish on the shared parent.
    (this.host.parentElement ?? this.host).style.setProperty('--feiying-fade', (this.controls ? 0 : pose.fade).toFixed(3));
  }

  private labels() {
    if (!this.opts.onLabels) return;
    const out: Partial<Record<LabelId, [number, number] | null>> = {};
    const w = this.host.clientWidth, h = this.host.clientHeight;
    const box = new THREE.Box3();
    const project = (p: THREE.Vector3): [number, number] | null => {
      const v = p.clone().project(this.camera);
      return v.z > 1 || Math.abs(v.x) > 1.05 || Math.abs(v.y) > 1.05 ? null : [(v.x + 1) / 2 * w, (1 - v.y) / 2 * h];
    };
    const at = (name: string, fx: number, fy: number, fz = 0.5) => {
      const node = this.named.get(name);
      if (!node || !node.visible) return null;
      box.setFromObject(node);
      return project(new THREE.Vector3(
        THREE.MathUtils.lerp(box.min.x, box.max.x, fx), THREE.MathUtils.lerp(box.min.y, box.max.y, fy),
        THREE.MathUtils.lerp(box.min.z, box.max.z, fz)));
    };
    if (this.tower?.visible) {
      out.spire = at('塔刹', 0.5, 0.35);
      out.outer = at('外塔_05', 1, 0.45);
      out.inner = at('内塔_石塔', 0.5, 0.5, 0.55);
      out.base = at('内塔_石塔', 0.5, 0.06, 0.55);
    } else if (this.dougong?.visible) {
      out.dou = at('细部_斗栱', 0.62, 0.38);
      out.gong = at('细部_斗栱', 0.25, 0.62);
      out.ang = at('细部_斗栱', 0.7, 0.86);
    }
    this.opts.onLabels(out);
  }

  private loop = () => {
    if (this.disposed || !this.visible) return;
    cancelAnimationFrame(this.frame);
    this.frame = requestAnimationFrame(this.loop);
    if (!this.tower) return;
    if (this.controls) this.controls.update();
    const goal = this.target();
    if (!this.controls) {
      // Damped chase toward the progress-determined pose: smooths wheel steps and always
      // converges onto the exact pose for the current progress (no accumulated state).
      const prev = this.shown;
      let next = goal;
      if (prev && prev.subject === goal.subject && !this.opts.reducedMotion) {
        const k = 0.16;
        const lerp = (a: number, b: number) => a + (b - a) * k;
        next = {
          ...goal,
          position: goal.position.map((v, i) => lerp(prev.position[i], v)) as Vec3,
          target: goal.target.map((v, i) => lerp(prev.target[i], v)) as Vec3,
          fov: lerp(prev.fov, goal.fov), shiftX: lerp(prev.shiftX, goal.shiftX),
          explode: lerp(prev.explode, goal.explode), cut: lerp(prev.cut, goal.cut), fade: lerp(prev.fade, goal.fade),
        };
        const gap = Math.abs(next.position[0] - goal.position[0]) + Math.abs(next.position[1] - goal.position[1])
          + Math.abs(next.position[2] - goal.position[2]) + Math.abs(next.explode - goal.explode) + Math.abs(next.cut - goal.cut)
          + Math.abs(next.fade - goal.fade);
        if (gap < 0.002) next = goal;
      }
      const moving = next !== goal;
      if (!this.dirty && !moving) return;
      this.shown = next;
      this.dirty = moving;
    } else if (!this.dirty) {
      return;
    } else {
      this.dirty = false;
    }
    this.apply(this.controls ? { ...goal, subject: 'tower', fade: 0 } : this.shown!);
    this.renderer.render(this.scene, this.camera);
    this.labels();
  };

  private resize() {
    const w = Math.max(1, this.host.clientWidth), h = Math.max(1, this.host.clientHeight);
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.dirty = true;
    this.shown = null;
  }

  dispose() {
    this.disposed = true;
    cancelAnimationFrame(this.frame);
    this.resizeObserver.disconnect();
    this.controls?.dispose();
    this.scene.traverse((node) => {
      if (!(node instanceof THREE.Mesh)) return;
      node.geometry.dispose();
      for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
        for (const value of Object.values(material)) if (value instanceof THREE.Texture) value.dispose();
        material.dispose();
      }
    });
    this.env.dispose();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}
