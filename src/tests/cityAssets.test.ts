import { describe, expect, it } from 'vitest';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

type Node = { name?: string; mesh?: number; extras?: { explodeDirection?: number[]; explodeDistance?: number } };
type Material = {
  normalTexture?: { index: number };
  pbrMetallicRoughness?: { baseColorTexture?: { index: number }; metallicRoughnessTexture?: { index: number } };
};

function readGlb(name: string): { nodes: Node[]; materials: Material[]; images: unknown[]; meshes: unknown[] } {
  const bytes = readFileSync(join(process.cwd(), 'public', 'models', `city-${name}.glb`));
  expect(bytes.toString('ascii', 0, 4)).toBe('glTF');
  const jsonLength = bytes.readUInt32LE(12);
  return JSON.parse(bytes.toString('utf8', 20, 20 + jsonLength));
}

describe('Blender city scenes', () => {
  const scenes = [
    ['yishang', ['石板街', '商铺', '屋顶', '悬灯']],
    ['dongwu', ['街区', '裙楼', '西塔', '东塔']],
    ['longemont', ['广场', '门廊', '拱环', '穹棚']],
    ['nanxun', ['河道', '护岸', '楼群', '屋顶']],
  ] as const;

  for (const [name, expectedParts] of scenes) {
    it(`${name} ships an editable source and a detailed, separable GLB`, () => {
      expect(existsSync(join(process.cwd(), 'assets', 'blender', 'sources', `city-${name}.blend`))).toBe(true);
      const gltf = readGlb(name);
      const movable = gltf.nodes.filter(node => node.extras?.explodeDirection);
      expect(gltf.meshes.length).toBeGreaterThan(40);
      for (const word of expectedParts) expect(movable.some(node => node.name?.includes(word)), `${name}: ${word}`).toBe(true);
      for (const node of movable) {
        expect(node.extras?.explodeDirection).toHaveLength(3);
        expect(node.extras?.explodeDistance).toBeGreaterThan(0);
      }
      expect(gltf.images.length).toBeGreaterThan(0);
      expect(gltf.materials.some(mat => mat.pbrMetallicRoughness?.baseColorTexture)).toBe(true);
      expect(gltf.materials.some(mat => mat.pbrMetallicRoughness?.metallicRoughnessTexture)).toBe(true);
      expect(gltf.materials.some(mat => mat.normalTexture)).toBe(true);
    });
  }
});
