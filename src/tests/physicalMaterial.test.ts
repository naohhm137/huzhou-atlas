import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { toPhysicalMaterial } from '../physicalMaterial';

describe('Physical material promotion', () => {
  it('promotes a GLTF standard material without requiring Physical-only properties', () => {
    const map = new THREE.Texture();
    const original = new THREE.MeshStandardMaterial({ map, color: 0x986442, roughness: 0.68, metalness: 0.02 });
    original.normalScale.set(1.18, 1.18);
    const result = toPhysicalMaterial(original);
    expect(result).toBeInstanceOf(THREE.MeshPhysicalMaterial);
    expect(result.map).toBe(map);
    expect(result.color.equals(original.color)).toBe(true);
    expect(result.normalScale.toArray()).toEqual([1.18, 1.18]);
    expect(result.roughness).toBe(0.68);
    expect(result.clearcoat).toBe(0.22);
    expect(original.type).toBe('MeshStandardMaterial');
  });
});
