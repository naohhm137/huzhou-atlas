import { describe, expect, it } from 'vitest';
import { existsSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { assetPathFor, posterPathFor, type ExhibitAssetKind } from '../modelAsset';

// Six exhibits shown whole: one Lux3D standard-tier model each (production/items).
const KINDS: ExhibitAssetKind[] = ['brush', 'silk', 'tea', 'yishang', 'dongwu', 'nanxun-city'];
const pub = (url: string) => join(process.cwd(), 'public', url.replace(/^\//, ''));
type Gltf = { nodes: { name?: string; mesh?: number }[]; meshes: unknown[]; images?: unknown[]; extensionsUsed?: string[];
  materials: { name?: string; emissiveTexture?: unknown; pbrMetallicRoughness?: { baseColorTexture?: unknown; metallicRoughnessTexture?: unknown } }[] };
const read = (file: string): Gltf => {
  const bytes = readFileSync(file);
  expect(bytes.toString('ascii', 0, 4)).toBe('glTF');
  return JSON.parse(bytes.toString('utf8', 20, 20 + bytes.readUInt32LE(12)));
};

describe('whole-model exhibits', () => {
  for (const kind of KINDS) {
    it(`${kind}: compressed desktop and mobile GLBs with PBR textures`, () => {
      for (const mobile of [false, true]) {
        const file = pub(assetPathFor(kind, mobile));
        const gltf = read(file);
        expect(gltf.extensionsUsed).toEqual(expect.arrayContaining(['KHR_draco_mesh_compression', 'EXT_texture_webp']));
        expect(gltf.meshes).toHaveLength(1);
        expect(gltf.materials.some((m) => m.pbrMetallicRoughness?.baseColorTexture && m.pbrMetallicRoughness?.metallicRoughnessTexture)).toBe(true);
        expect(statSync(file).size).toBeLessThan((mobile ? 4 : 8) * 1024 * 1024);
      }
    });
    it(`${kind}: has a rendered poster and close-up`, () => {
      expect(existsSync(pub(posterPathFor(kind, false)))).toBe(true);
      expect(existsSync(pub(posterPathFor(kind, true)))).toBe(true);
    });
  }
  it('lit windows glow on the dusk street scenes and the river has its own water surface', () => {
    for (const kind of ['yishang', 'nanxun-city'] as const) expect(read(pub(assetPathFor(kind))).materials.some((m) => m.emissiveTexture)).toBe(true);
    expect(read(pub(assetPathFor('nanxun-city'))).materials.map((m) => m.name)).toContain('nanxun_water');
  });
});
