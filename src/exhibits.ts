import * as THREE from 'three';
import { fitCameraDistance, loadExhibitAsset, type ExhibitAssetKind } from './modelAsset';
import { advanceOrbit, advanceZoom, type Orbit } from './orbitGesture';
import type { MovablePart } from './models/shared';
import { SceneFailure } from './sceneFailure';

// 'tower' stays a controller id for the Feiying chapter, which renders through src/feiying.
export type ExhibitKind = ExhibitAssetKind | 'tower';
type Frame = { distance: number; center: THREE.Vector3 };

// Per-exhibit camera: model yaw so the Lux3D "front" (the reference-image view) faces the
// visitor, plus elevation and distance relative to the fitted frame. Matches render_item.py.
const VIEW: Record<ExhibitAssetKind, { yaw: number; elevation: number; distance: number }> = {
  brush: { yaw: -1.4, elevation: 0.38, distance: 0.82 },
  silk: { yaw: -1.15, elevation: 0.32, distance: 0.78 },
  tea: { yaw: -1.3, elevation: 0.56, distance: 0.82 },
  yishang: { yaw: -1.15, elevation: 0.68, distance: 0.8 },
  dongwu: { yaw: -1.2, elevation: 0.25, distance: 0.82 },
  'nanxun-city': { yaw: -1.3, elevation: 0.62, distance: 0.8 },
};

/** Sky gradient matching the Blender world for each look (render_item.py). */
type Look = 'studio' | 'dusk' | 'day';
const LOOK: Record<ExhibitAssetKind, Look> = { brush: 'studio', silk: 'studio', tea: 'studio', yishang: 'dusk', dongwu: 'day', 'nanxun-city': 'dusk' };
function skyEnvironment(renderer: THREE.WebGLRenderer, look: Look) {
  const pmrem = new THREE.PMREMGenerator(renderer);
  const sky = new THREE.Scene();
  // Dongwu's blue curtain wall only reads blue under a daylight sky, as in its reference photo.
  const horizon = look === 'day' ? 'vec3(0.55, 0.68, 0.85)' : look === 'dusk' ? 'vec3(0.16, 0.10, 0.06)' : 'vec3(0.06, 0.04, 0.026)';
  const zenith = look === 'day' ? 'vec3(0.10, 0.25, 0.62)' : 'vec3(0.008, 0.024, 0.026)';
  sky.add(new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false,
    vertexShader: 'varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: `varying vec3 vDir; void main(){
      float h = clamp((vDir.y + 0.05) / 0.6, 0.0, 1.0);
      vec3 c = vDir.y < -0.05 ? vec3(0.012, 0.012, 0.011) : mix(${horizon}, ${zenith}, h);
      gl_FragColor = vec4(c, 1.0); }`,
  })));
  const target = pmrem.fromScene(sky, 0);
  pmrem.dispose();
  return target;
}

export class ExhibitScene {
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(38, 1, 0.1, 150);
  private renderer: THREE.WebGLRenderer;
  private environmentTarget: THREE.WebGLRenderTarget;
  private root = new THREE.Group();
  private parts: MovablePart[] = [];
  private frame = 0;
  private progress = 0;
  private expanded = false;
  private visualAmount = 0;
  private orbit: Orbit = { yaw: 0, pitch: 0 };
  private zoom = 1;
  private baseRotationY = 0;
  private resizeObserver: ResizeObserver;
  private visibilityObserver: IntersectionObserver;
  private visible = false;
  private activePointerId: number | null = null;
  private previousPointer: [number, number] = [0, 0];
  private disposed = false;
  private ready = false;
  private needsRender = true;
  private assembled: Frame = { distance: 8, center: new THREE.Vector3() };
  private exploded: Frame = { distance: 12, center: new THREE.Vector3() };

  constructor(private host: HTMLElement, private kind: ExhibitAssetKind, private reduced: boolean, private onError?: (error: SceneFailure) => void) {
    try {
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    } catch (error) {
      throw new SceneFailure('graphics', 'WebGL renderer could not create a graphics context', error);
    }
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    // Same look as the approved Blender renders and the Feiying chapter: ACES, dark sky
    // environment, three suns with soft shadows. (A white studio environment reads as fog.)
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    const small = Math.min(window.innerWidth, window.innerHeight) < 720;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, small ? 1.5 : 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.domElement.className = 'exhibit-canvas';
    this.renderer.domElement.setAttribute('aria-hidden', 'true');
    host.appendChild(this.renderer.domElement);
    const look = LOOK[kind];
    this.environmentTarget = skyEnvironment(this.renderer, look);
    this.scene.environment = this.environmentTarget.texture;
    // Blender (x, y, z) → three (x, z, -y); directions from production/feiying/scripts/render_shots.py.
    const sun = (bx: number, by: number, bz: number, color: number, intensity: number, shadow: boolean) => {
      const l = new THREE.DirectionalLight(color, intensity);
      l.position.set(bx, bz, -by).normalize().multiplyScalar(30);
      if (shadow) {
        l.castShadow = true;
        l.shadow.mapSize.set(small ? 1024 : 2048, small ? 1024 : 2048);
        Object.assign(l.shadow.camera, { left: -6, right: 6, top: 7, bottom: -5, near: 1, far: 70 });
        l.shadow.bias = -0.0004;
        l.shadow.normalBias = 0.02;
      }
      this.scene.add(l);
    };
    if (look === 'day') {
      sun(-30, -60, 50, 0xfff5e6, 3.4, true);  // high white sun, front-left
      sun(50, 30, 30, 0xb3d1ff, 0.6, false);   // sky-blue fill
    } else {
      sun(-55, 40, 18, 0xffad66, 5.2, true);   // warm, low, back-left: rim
      sun(-30, -60, 30, 0xffcc99, 2.0, true);  // warm front so the surface reads
      sun(50, -30, 40, 0x8cbfe6, 0.5, false);  // cool fill
    }
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(host);
    this.visibilityObserver = new IntersectionObserver(([entry]) => {
      this.visible = entry?.isIntersecting ?? false;
      if (this.visible) { this.needsRender = true; this.render(); }
      else cancelAnimationFrame(this.frame);
    }, { rootMargin: '120px 0px' });
    this.visibilityObserver.observe(host);
    this.resize();
    this.renderer.domElement.addEventListener('pointerdown', this.onPointerDown);
    this.renderer.domElement.addEventListener('pointermove', this.onPointerMove);
    this.renderer.domElement.addEventListener('pointerup', this.onPointerUp);
    this.renderer.domElement.addEventListener('pointercancel', this.onPointerCancel);
    this.renderer.domElement.addEventListener('lostpointercapture', this.onPointerCancel);
    this.renderer.domElement.addEventListener('wheel', this.onWheel, { passive: false });
    this.renderer.domElement.addEventListener('webglcontextlost', this.onContextLost);
    loadExhibitAsset(kind).then((model) => {
      if (this.disposed) { this.disposeModel(model.root); return; }
      this.root = model.root;
      this.parts = model.parts;
      const anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
      this.root.traverse((object) => {
        if (!(object instanceof THREE.Mesh)) return;
        object.castShadow = true;
        object.receiveShadow = true;
        for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
          if (!(material instanceof THREE.MeshStandardMaterial)) continue;
          for (const map of [material.map, material.roughnessMap, material.emissiveMap]) if (map) map.anisotropy = anisotropy;
        }
      });
      this.scene.add(this.root);
      this.root.rotation.y = VIEW[kind].yaw;
      this.baseRotationY = this.root.rotation.y;
      this.fitFrames();
      this.ready = true;
      this.host.classList.add('is-ready');
      if (this.visible) this.render();
    }).catch((error) => {
      if (!this.disposed) {
        console.error(`[Huzhou ${kind}] Model asset loading failed`, error);
        this.onError?.(new SceneFailure('asset', `Model asset loading failed: ${kind}`, error));
      }
    });
  }

  private onContextLost = (event: Event) => {
    event.preventDefault();
    cancelAnimationFrame(this.frame);
    if (!this.disposed) this.onError?.(new SceneFailure('context-lost', `Graphics context lost: ${this.kind}`));
  };

  private onPointerDown = (event: PointerEvent) => {
    if (this.activePointerId !== null || (event.pointerType === 'mouse' && event.button !== 0)) return;
    this.activePointerId = event.pointerId;
    this.previousPointer = [event.clientX, event.clientY];
    this.needsRender = true;
    this.renderer.domElement.setPointerCapture(event.pointerId);
    if (this.expanded) event.preventDefault();
  };
  private onPointerUp = (event: PointerEvent) => {
    if (event.pointerId !== this.activePointerId) return;
    this.activePointerId = null;
    if (this.renderer.domElement.hasPointerCapture(event.pointerId)) this.renderer.domElement.releasePointerCapture(event.pointerId);
  };
  private onPointerCancel = (event: PointerEvent) => {
    if (event.pointerId === this.activePointerId) this.activePointerId = null;
  };
  private onPointerMove = (event: PointerEvent) => {
    if (event.pointerId !== this.activePointerId) return;
    this.orbit = advanceOrbit(this.orbit,
      { x: event.clientX - this.previousPointer[0], y: event.clientY - this.previousPointer[1] },
      { width: this.host.clientWidth, height: this.host.clientHeight });
    this.previousPointer = [event.clientX, event.clientY];
    this.needsRender = true;
    if (this.expanded) event.preventDefault();
  };
  private onWheel = (event: WheelEvent) => {
    if (!this.expanded) return;
    event.preventDefault();
    this.zoom = advanceZoom(this.zoom, event.deltaY);
    this.needsRender = true;
  };

  private boundsAt(amount: number): THREE.Box3 {
    for (const item of this.parts) item.group.position.copy(item.origin).addScaledVector(item.direction, amount * item.distance);
    this.root.updateMatrixWorld(true);
    return new THREE.Box3().setFromObject(this.root);
  }

  private frameFromBounds(bounds: THREE.Box3): Frame {
    const size = bounds.getSize(new THREE.Vector3());
    return {
      distance: fitCameraDistance({ width: size.x, height: size.y, depth: size.z }, this.camera.fov, this.camera.aspect) * VIEW[this.kind].distance,
      center: bounds.getCenter(new THREE.Vector3()),
    };
  }

  private fitFrames() {
    this.assembled = this.frameFromBounds(this.boundsAt(0));
    this.exploded = this.frameFromBounds(this.boundsAt(1));
    this.boundsAt(this.visualAmount);
  }

  private resize() {
    this.needsRender = true;
    const width = Math.max(1, this.host.clientWidth);
    const height = Math.max(1, this.host.clientHeight);
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    if (this.ready) {
      this.fitFrames();
      if (this.visible) this.render();
    }
  }

  setProgress(progress: number) {
    const next = THREE.MathUtils.clamp(progress, 0, 1);
    if (next !== this.progress) this.needsRender = true;
    this.progress = next;
  }
  setExpanded(expanded: boolean) {
    this.needsRender = true;
    this.expanded = expanded;
    if (!expanded) this.zoom = 1;
  }
  resetRotation() { this.orbit = { yaw: 0, pitch: 0 }; this.needsRender = true; }

  private render = () => {
    // Keep the renderer alive while a pinned chapter is being positioned by
    // the browser. IntersectionObserver can report a stale value during a
    // hash jump, which otherwise leaves a blank canvas until the next scroll.
    if (this.disposed) return;
    cancelAnimationFrame(this.frame);
    this.frame = requestAnimationFrame(this.render);
    if (!this.ready) return;
    const scrollReveal = this.reduced ? 0 : THREE.MathUtils.smoothstep(this.progress, 0.22, 0.78) * 0.18;
    const desired = this.expanded ? 1 : scrollReveal;
    if (!this.needsRender && Math.abs(desired - this.visualAmount) < 0.0001) return;
    this.visualAmount += (desired - this.visualAmount) * (this.reduced ? 1 : 0.11);
    for (const item of this.parts) item.group.position.copy(item.origin).addScaledVector(item.direction, this.visualAmount * item.distance);
    this.root.rotation.y = this.baseRotationY + this.orbit.yaw + (this.reduced ? 0 : this.progress * 0.11);
    this.root.rotation.x = this.orbit.pitch;
    const target = this.assembled.center.clone().lerp(this.exploded.center, this.visualAmount);
    const fittedDistance = THREE.MathUtils.lerp(this.assembled.distance, this.exploded.distance, this.visualAmount);
    // Whole models: "expanded" moves the camera in for a close look instead of exploding parts.
    const distance = fittedDistance * (1 - this.visualAmount * 0.32) * this.zoom;
    const elevation = distance * VIEW[this.kind].elevation;
    this.camera.position.set(target.x, target.y + elevation, target.z + distance);
    this.camera.lookAt(target);
    this.renderer.render(this.scene, this.camera);
    this.needsRender = false;
  };

  private disposeModel(root: THREE.Object3D) {
    const geometries = new Set<THREE.BufferGeometry>();
    const materials = new Set<THREE.Material>();
    const textures = new Set<THREE.Texture>();
    root.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        geometries.add(object.geometry);
        for (const material of Array.isArray(object.material) ? object.material : [object.material]) materials.add(material);
      }
    });
    geometries.forEach((geometry) => geometry.dispose());
    materials.forEach((material) => {
      Object.values(material).forEach((value) => {
        if (value instanceof THREE.Texture) textures.add(value);
      });
      material.dispose();
    });
    textures.forEach((texture) => texture.dispose());
  }

  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    cancelAnimationFrame(this.frame);
    this.resizeObserver.disconnect();
    this.visibilityObserver.disconnect();
    this.renderer.domElement.removeEventListener('pointerdown', this.onPointerDown);
    this.renderer.domElement.removeEventListener('pointermove', this.onPointerMove);
    this.renderer.domElement.removeEventListener('pointerup', this.onPointerUp);
    this.renderer.domElement.removeEventListener('pointercancel', this.onPointerCancel);
    this.renderer.domElement.removeEventListener('lostpointercapture', this.onPointerCancel);
    this.renderer.domElement.removeEventListener('wheel', this.onWheel);
    this.renderer.domElement.removeEventListener('webglcontextlost', this.onContextLost);
    this.disposeModel(this.root);
    this.environmentTarget.dispose();
    this.renderer.dispose();
    this.renderer.forceContextLoss();
    this.renderer.domElement.remove();
    this.host.classList.remove('is-ready');
  }
}
