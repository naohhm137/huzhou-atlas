import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

type GlbNode = { name?: string; extras?: { explodeDirection?: number[]; explodeDistance?: number } };
type GlbMaterial = {
  normalTexture?: { index: number };
  pbrMetallicRoughness?: { baseColorTexture?: { index: number }; metallicRoughnessTexture?: { index: number } };
};

function gltfOf(name: string): { nodes: GlbNode[]; materials?: GlbMaterial[]; textures?: unknown[]; images?: unknown[] } {
  const bytes = readFileSync(join(process.cwd(), 'public', 'models', `${name}.glb`));
  expect(bytes.toString('ascii', 0, 4)).toBe('glTF');
  const jsonLength = bytes.readUInt32LE(12);
  return JSON.parse(bytes.toString('utf8', 20, 20 + jsonLength));
}

const nodesOf = (name: string) => gltfOf(name).nodes;

describe('Blender-authored exhibit assets', () => {
  it('ships four valid GLBs with movable named parts', () => {
    for (const name of ['brush', 'loom', 'tea', 'tower']) {
      const nodes = nodesOf(name);
      expect(nodes.length).toBeGreaterThan(15);
      expect(nodes.some(node => node.extras?.explodeDirection && node.extras?.explodeDistance)).toBe(true);
    }
  });

  it('keeps one complete brush head and no separate duplicate tassels', () => {
    const movable = nodesOf('brush').filter(node => node.extras?.explodeDirection);
    expect(movable.filter(node => node.name?.includes('笔锋'))).toHaveLength(1);
    expect(movable.filter(node => node.name?.includes('外毫'))).toHaveLength(0);
    expect(nodesOf('brush').filter(node => node.name?.includes('笔帽'))).toHaveLength(0);
  });

  it('ships real embedded PBR surface detail for every exhibit', () => {
    for (const name of ['brush', 'loom', 'tea', 'tower']) {
      const gltf = gltfOf(name);
      expect(gltf.images?.length ?? 0, `${name} image textures`).toBeGreaterThan(0);
      expect(gltf.materials?.some(material => material.pbrMetallicRoughness?.baseColorTexture), `${name} albedo`).toBe(true);
      expect(gltf.materials?.some(material => material.pbrMetallicRoughness?.metallicRoughnessTexture), `${name} roughness`).toBe(true);
      expect(gltf.materials?.some(material => material.normalTexture), `${name} surface normal`).toBe(true);
    }
  });

  it('separates the vessel, its saucer, liquor, and visible buds', () => {
    const names = nodesOf('tea').map(node => node.name ?? '');
    for (const part of ['茶盏', '盏托', '茶汤', '芽叶']) expect(names.some(name => name.includes(part))).toBe(true);
    expect(names.filter(name => name.includes('杯底'))).toHaveLength(0);
    expect(names.some(name => name.includes('茶汤侧壁'))).toBe(false);
    expect(names.some(name => name.includes('茶汤透亮浅层'))).toBe(true);
  });

  it('contains seven outer levels and five inner stone levels', () => {
    const names = nodesOf('tower').map(node => node.name ?? '');
    expect(names.filter(name => /^外塔楼层[1-7]$/.test(name))).toHaveLength(7);
    expect(names.filter(name => /^内塔石层[1-5]$/.test(name))).toHaveLength(5);
    expect(names.some(name => name.includes('斗拱'))).toBe(true);
  });
});
