import { describe, expect, it } from 'vitest';
import { readFileSync, statSync } from 'node:fs';
import { resolve } from 'node:path';
import { layerWeight, poseAt, progressForScreen, PINES, SCREEN_COUNT, screenOpacity, screenPosition, SHOTS, wedgePlanes, type Vec3 } from '../feiying/timeline';
import { FEIYING_SCREENS } from '../feiying/screens';

type GltfNode = { name?: string; children?: number[]; extras?: Record<string, unknown> };
function gltfJson(file: string) {
  const buf = readFileSync(resolve(__dirname, '../../public/models/feiying', file));
  const len = buf.readUInt32LE(12);
  return JSON.parse(buf.subarray(20, 20 + len).toString('utf8')) as { nodes: GltfNode[]; extensionsUsed?: string[]; images?: unknown[] };
}

describe('feiying scroll timeline', () => {
  it('has one shot and one copy screen per design board', () => {
    expect(SHOTS).toHaveLength(6);
    expect(FEIYING_SCREENS).toHaveLength(6);
    expect(FEIYING_SCREENS.map((s) => s.nav)).toEqual(['初见', '塔身', '塔中塔', '斗栱', '石塔', '守护']);
  });

  it('maps progress monotonically onto screens and lands on every screen', () => {
    let last = -1;
    for (let p = 0; p <= 1.0001; p += 0.001) {
      const s = screenPosition(p);
      expect(s).toBeGreaterThanOrEqual(last - 1e-9);
      last = s;
    }
    for (let i = 0; i < SCREEN_COUNT; i += 1) expect(screenPosition(progressForScreen(i))).toBe(i);
    expect(screenPosition(0)).toBe(0);
    expect(screenPosition(1)).toBe(SCREEN_COUNT - 1);
  });

  it('is a pure function of progress, so reverse scrolling reproduces every state', () => {
    const forward = [0.07, 0.31, 0.52, 0.64, 0.88].map((p) => poseAt(screenPosition(p), [22, 0, 0]));
    const backward = [0.88, 0.64, 0.52, 0.31, 0.07].map((p) => poseAt(screenPosition(p), [22, 0, 0])).reverse();
    expect(backward).toEqual(forward);
  });

  it('starts and ends assembled, with the cut closed', () => {
    for (const p of [0, 1]) {
      const pose = poseAt(screenPosition(p));
      expect(pose.explode).toBe(0);
      expect(pose.cut).toBe(0);
      expect(pose.fade).toBe(0);
    }
    expect(poseAt(2).explode).toBeGreaterThan(0);
    expect(poseAt(2).cut).toBe(1);
  });

  it('cuts to the dougong exhibit through black instead of flying across the scene', () => {
    const dougong: Vec3 = [22, 0, 0];
    expect(poseAt(2.5, dougong).fade).toBeCloseTo(1, 5);
    expect(poseAt(3, dougong).subject).toBe('dougong');
    expect(poseAt(3, dougong).target[0]).toBeCloseTo(22);
    expect(poseAt(2.2, dougong).subject).toBe('tower');
    expect(poseAt(3.8, dougong).subject).toBe('tower');
  });

  it('cross-fades copy so only the current screen is fully visible', () => {
    expect(screenOpacity(2, 2)).toBe(1);
    expect(screenOpacity(1, 2)).toBe(0);
    expect(screenOpacity(2, 2.2)).toBeGreaterThan(0);
    expect(layerWeight(PINES, 0)).toBe(1);
    expect(layerWeight(PINES, 3)).toBe(0);
  });
});

describe('feiying cutaway wedge', () => {
  // three.js clipIntersection: a point is removed only when it is on the negative side of both planes.
  const clipped = (cam: Vec3, p: Vec3, opening = 1) => {
    const { normals, constant } = wedgePlanes(cam, opening);
    return normals.every((n) => n[0] * p[0] + n[1] * p[1] + n[2] * p[2] - constant < 0);
  };

  it('opens the quadrant facing the camera and keeps the far side', () => {
    const cam: Vec3 = [10, 4, 58];
    expect(clipped(cam, [1, 10, 6])).toBe(true);    // near wall between the camera and the axis
    expect(clipped(cam, [-1, 10, -6])).toBe(false); // far wall stays
    expect(clipped(cam, [6, 10, -1])).toBe(false);  // side wall outside the wedge
  });

  it('removes nothing when the opening is 0', () => {
    const cam: Vec3 = [10, 4, 58];
    for (const p of [[1, 10, 6], [3, 0, 4], [0.2, 20, 7]] as Vec3[]) expect(clipped(cam, p, 0)).toBe(false);
  });
});

describe('feiying web model (tutorial 4.7)', () => {
  it('keeps every movable part as its own named node with explosion metadata', () => {
    const { nodes } = gltfJson('feiying.glb');
    const names = nodes.map((n) => n.name ?? '');
    for (const name of ['feiying_tower', 'outer_tower', '塔刹', '内塔_石塔', '细部_斗栱']) expect(names).toContain(name);
    const floors = nodes.filter((n) => /^外塔_0[1-7]/.test(n.name ?? '') && !n.name!.endsWith('_geo'));
    expect(floors).toHaveLength(7);
    const movable = nodes.filter((n) => Array.isArray(n.extras?.explodeDirection) && typeof n.extras?.explodeDistance === 'number');
    expect(movable.length).toBe(8); // 7 floors + spire
  });

  it('ships compressed desktop and mobile files under the 20 MB guideline', () => {
    for (const file of ['feiying.glb', 'feiying-mobile.glb']) {
      const gltf = gltfJson(file);
      expect(gltf.extensionsUsed).toEqual(expect.arrayContaining(['KHR_draco_mesh_compression', 'EXT_texture_webp']));
      expect(gltf.images?.length ?? 0).toBeGreaterThan(0);
      expect(statSync(resolve(__dirname, '../../public/models/feiying', file)).size).toBeLessThan(20 * 1024 * 1024);
    }
  });
});
