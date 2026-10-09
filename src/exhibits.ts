import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { fitCameraDistance, loadExhibitAsset, type ExhibitAssetKind } from './modelAsset';
import { advanceOrbit, advanceZoom, type Orbit } from './orbitGesture';
import type { MovablePart } from './models/shared';
import { SceneFailure } from './sceneFailure';

export type ExhibitKind = ExhibitAssetKind;
type Frame = { distance: number; center: THREE.Vector3 };

export class ExhibitScene {
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(38, 1, 0.1, 150);
  private renderer: THREE.WebGLRenderer;
  private environmentTarget: THREE.WebGLRenderTarget;
  private root = new THREE.Group();
  private parts: MovablePart[] = [];
  private roofSeams: THREE.Object3D[] = [];
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

  constructor(private host: HTMLElement, private kind: ExhibitKind, private reduced: boolean, private onError?: (error: SceneFailure) => void) {
    try {
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    } catch (error) {
      throw new SceneFailure('graphics', 'WebGL renderer could not create a graphics context', error);
    }
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    const isCity = ['yishang', 'dongwu', 'longemont', 'nanxun-city'].includes(kind);
    this.renderer.toneMappingExposure = isCity ? 1.08 : 1.16;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, window.innerWidth < 720 ? 1.3 : 1.65));
    this.renderer.shadowMap.enabled = isCity;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.domElement.className = 'exhibit-canvas';
    this.renderer.domElement.setAttribute('aria-hidden', 'true');
    host.appendChild(this.renderer.domElement);
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    const room = new RoomEnvironment();
    this.environmentTarget = pmrem.fromScene(room);
    room.dispose();
    pmrem.dispose();
    this.scene.environment = this.environmentTarget.texture;
    this.scene.environmentIntensity = isCity ? 0.92 : 0.82;
    this.scene.add(new THREE.HemisphereLight(0xfff1d7, 0x334d4b, 0.86));
    const key = new THREE.DirectionalLight(0xffe4b7, 2.05);
    key.position.set(4, 7, 7);
    if (isCity) {
      key.castShadow = true;
      key.shadow.mapSize.set(window.innerWidth < 720 ? 1024 : 2048, window.innerWidth < 720 ? 1024 : 2048);
      Object.assign(key.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12, near: 0.1, far: 45 });
      key.shadow.normalBias = 0.018;
      key.shadow.bias = -0.0002;
    }
    this.scene.add(key);
    const fill = new THREE.DirectionalLight(0xa9d0c8, 0.82);
    fill.position.set(-6, 2, 4);
    this.scene.add(fill);
    const rim = new THREE.DirectionalLight(0xfff0d5, 1.32);
    rim.position.set(-2, 5, -6);
    this.scene.add(rim);
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
        if (object.name.includes('穹顶细密竖向屋面接缝')) this.roofSeams.push(object);
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        for (const material of materials) {
          if (!(material instanceof THREE.MeshStandardMaterial)) continue;
          for (const map of [material.map, material.normalMap, material.roughnessMap]) {
            if (map) { map.anisotropy = anisotropy; map.needsUpdate = true; }
          }
        }
      });
      this.scene.add(this.root);
      if (isCity) this.root.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          object.castShadow = !/水面|河床/.test(object.name);
          object.receiveShadow = true;
        }
      });
      this.root.rotation.y = kind === 'silk' ? -0.32 : kind === 'tower' ? -0.18
        : kind === 'yishang' ? -0.26 : kind === 'nanxun-city' ? 0
        : kind === 'dongwu' ? -0.14 : -0.15;
      if (kind === 'brush') this.root.rotation.z = 0.24;
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
    const cityScale = ['yishang', 'dongwu', 'longemont', 'nanxun-city'].includes(this.kind)
      ? (this.host.clientWidth < 620 ? 0.88 : 0.92) : 1;
    return {
      distance: fitCameraDistance({ width: size.x, height: size.y, depth: size.z }, this.camera.fov, this.camera.aspect) * cityScale,
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
    if (!this.visible || this.disposed) return;
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
    const distance = fittedDistance * (this.kind === 'tea' ? 1 - this.visualAmount * 0.16 : 1) * this.zoom;
    const elevation = this.kind === 'tea' ? distance * 0.58 : this.kind === 'silk' ? distance * 0.12
      : this.kind === 'yishang' || this.kind === 'longemont' ? distance * 0.49
      : this.kind === 'nanxun-city' ? distance * 0.22
      : this.kind === 'dongwu' ? -distance * 0.12 : distance * 0.035;
    const lateral = this.kind === 'nanxun-city' ? -distance * 0.35
      : this.kind === 'dongwu' ? distance * 0.12 : 0;
    this.camera.position.set(target.x + lateral, target.y + elevation, target.z + distance);
    this.camera.lookAt(target);
    // Subpixel ribs flicker as dotted lines at atlas scale. Keep the authored
    // geometry for close inspection, where its diameter covers a full pixel.
    const seamPixels = 0.016 * this.host.clientHeight / (2 * Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2)) * this.camera.position.distanceTo(target));
    for (const seam of this.roofSeams) seam.visible = seamPixels >= 0.85;
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
