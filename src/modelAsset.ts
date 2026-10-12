import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import type { ExhibitModel, MovablePart } from './models/shared';

export type ExhibitAssetKind = 'brush' | 'silk' | 'tea' | 'yishang' | 'dongwu' | 'nanxun-city';
export type AssetIndexPath = string;
// Each exhibit is one Lux3D standard-tier model, exported by production/items/scripts/export_item.py.
const fileName: Record<ExhibitAssetKind, string> = {
  brush: 'brush', silk: 'loom', tea: 'tea', yishang: 'yishang', dongwu: 'dongwu', 'nanxun-city': 'nanxun',
};
const loader = new GLTFLoader().setDRACOLoader(new DRACOLoader().setDecoderPath(`${import.meta.env.BASE_URL}draco/`));

export function assetPathFor(kind: ExhibitAssetKind, mobile = false): string {
  return `${import.meta.env.BASE_URL}models/items/${fileName[kind]}${mobile ? '-mobile' : ''}.glb`;
}

export function assetIndexPath(): AssetIndexPath {
  return `${import.meta.env.BASE_URL}asset-index.json`;
}

export function posterPathFor(kind: ExhibitAssetKind, expanded: boolean): string {
  return `${import.meta.env.BASE_URL}media/items/${fileName[kind]}${expanded ? '-detail' : ''}.webp`;
}

export function collectMovableParts(root: THREE.Object3D): MovablePart[] {
  const parts: MovablePart[] = [];
  const names = new Set<string>();
  root.traverse((node) => {
    const raw = node.userData.explodeDirection;
    if (raw === undefined) return;
    const distance = node.userData.explodeDistance;
    const valid = Array.isArray(raw) && raw.length === 3 && raw.every((n) => typeof n === 'number' && Number.isFinite(n))
      && typeof distance === 'number' && Number.isFinite(distance) && distance > 0;
    if (!valid || !node.name || names.has(node.name)) throw new Error(`Invalid explosion part: ${node.name || 'unnamed'}`);
    const direction = new THREE.Vector3(raw[0], raw[1], raw[2]);
    if (direction.lengthSq() < 1e-8) throw new Error(`Invalid explosion direction: ${node.name}`);
    names.add(node.name);
    parts.push({ group: node as THREE.Group, origin: node.position.clone(), direction: direction.normalize(), distance });
  });
  return parts;
}

export function fitCameraDistance(size: { width: number; height: number; depth: number }, fovDegrees: number, aspect: number): number {
  const halfVertical = THREE.MathUtils.degToRad(fovDegrees) / 2;
  const vertical = size.height / (2 * Math.tan(halfVertical));
  const horizontal = size.width / (2 * Math.tan(halfVertical) * Math.max(0.2, aspect));
  return (Math.max(vertical, horizontal) * 1.25) + size.depth * 0.55 + 0.2;
}

export async function loadExhibitAsset(kind: ExhibitAssetKind): Promise<ExhibitModel> {
  const mobile = typeof window !== 'undefined' && Math.min(window.innerWidth, window.innerHeight) < 720;
  const gltf = await loader.loadAsync(assetPathFor(kind, mobile));
  const root = new THREE.Group();
  root.add(gltf.scene);
  // Exhibits are shown whole (no part explosion); a model may still carry explode metadata.
  return { root, parts: collectMovableParts(root), metadata: {} };
}
