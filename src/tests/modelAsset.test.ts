import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { assetPathFor, collectMovableParts, fitCameraDistance } from '../modelAsset';

describe('GLB part contract', () => {
  it('routes each city chapter to the corresponding Blender city asset', () => {
    expect(assetPathFor('yishang')).toMatch(/models\/city-yishang\.glb$/);
    expect(assetPathFor('dongwu')).toMatch(/models\/city-dongwu\.glb$/);
    expect(assetPathFor('longemont')).toMatch(/models\/city-longemont\.glb$/);
    expect(assetPathFor('nanxun-city')).toMatch(/models\/city-nanxun\.glb$/);
  });
  it('records a node origin and normalizes its explosion direction', () => {
    const root = new THREE.Group();
    const head = new THREE.Group();
    head.name = '笔锋';
    head.position.set(0, -1.8, 0);
    head.userData = { explodeDirection: [0, -2, 0], explodeDistance: 0.5 };
    root.add(head);
    const parts = collectMovableParts(root);
    expect(parts).toHaveLength(1);
    expect(parts[0].origin.toArray()).toEqual([0, -1.8, 0]);
    expect(parts[0].direction.toArray()).toEqual([0, -1, 0]);
    expect(parts[0].distance).toBe(0.5);
  });

  it('rejects an invalid explosion contract instead of animating unpredictably', () => {
    const root = new THREE.Group();
    const invalid = new THREE.Group();
    invalid.name = '盏身';
    invalid.userData = { explodeDirection: [0, 0, 0], explodeDistance: 0.4 };
    root.add(invalid);
    expect(() => collectMovableParts(root)).toThrow(/盏身/);
  });

  it('fits a tall exploded model in a narrow stage without cropping', () => {
    const distance = fitCameraDistance({ width: 2.9, height: 8.4, depth: 2.9 }, 38, 390 / 480);
    const verticalVisibleHeight = 2 * distance * Math.tan(38 * Math.PI / 360);
    expect(verticalVisibleHeight).toBeGreaterThan(8.4 * 1.12);
  });
});
