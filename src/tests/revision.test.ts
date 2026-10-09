import { describe, expect, it } from 'vitest';
import { chapterMediaTime, MEDIA_RANGES } from '../storyTiming';
import { makeBrush } from '../models/brush';
import { makeLoom } from '../models/loom';
import { makeTea } from '../models/tea';
import { makeTower } from '../models/tower';
import { displacedPosition } from '../models/shared';
import * as THREE from 'three';

describe('story exposure and reversibility', () => {
  it('holds the Nanxun photograph through the opening', () => {
    expect(MEDIA_RANGES.opening[1]).toBeLessThanOrEqual(2.1);
    expect(chapterMediaTime('opening', 1)).toBeLessThanOrEqual(2.1);
    expect(chapterMediaTime('opening', 0.8)).toBeGreaterThan(chapterMediaTime('opening', 0.2));
  });
  it('reverses each transition without hysteresis', () => {
    expect(chapterMediaTime('thread-bridge', 0.25)).toBe(chapterMediaTime('thread-bridge', 0.25));
    expect(chapterMediaTime('thread-bridge', 0.8)).toBeGreaterThan(chapterMediaTime('thread-bridge', 0.2));
  });
});

describe('museum-inspired structures', () => {
  it('gives the bamboo shaft a slender 19:1 proportion and separate hair layers', () => {
    const model = makeBrush();
    expect(model.metadata.shaftLength / model.metadata.shaftDiameter).toBeGreaterThanOrEqual(18);
    expect(model.parts.length).toBeGreaterThanOrEqual(6);
    expect(model.parts.some(part => part.group.name.includes('外毫'))).toBe(true);
  });
  it('builds a loom with individually addressable warp threads', () => {
    const model = makeLoom();
    expect(model.parts.filter(part => part.group.name.startsWith('经丝')).length).toBeGreaterThanOrEqual(48);
    for (const word of ['经轴', '卷布轴', '综', '筘', '梭']) {
      expect(model.parts.some(part => part.group.name.includes(word))).toBe(true);
    }
  });
  it('separates saucer, bowl, volume of liquor and buds', () => {
    const model = makeTea();
    expect(model.parts.length).toBeGreaterThanOrEqual(10);
    expect(model.metadata.saucerDiameter / model.metadata.bowlDiameter).toBeGreaterThan(1.3);
    expect(model.parts.some(part => part.group.name.includes('茶汤'))).toBe(true);
    expect(model.parts.filter(part => part.group.name.includes('芽叶')).length).toBeGreaterThanOrEqual(5);
  });
  it('reveals the five-level inner stone pagoda beneath seven distinct outer timber levels', () => {
    const model = makeTower();
    expect(model.parts.filter(part => part.group.name.startsWith('外塔楼层')).length).toBe(7);
    expect(model.parts.filter(part => part.group.name.startsWith('内塔石层')).length).toBe(5);
    expect(model.parts.filter(part => part.group.name.startsWith('外塔飞檐')).length).toBe(7);
    expect(model.parts.length).toBeGreaterThanOrEqual(23);
    expect(model.parts.some(part => part.group.name.includes('斗拱'))).toBe(true);
    expect(model.parts.some(part => part.group.name.includes('须弥座'))).toBe(true);
  });
  it('leaves a sightline through the outer tower into the inner stone tower', () => {
    const model = makeTower();
    model.root.updateMatrixWorld(true);
    const ray = new THREE.Raycaster(new THREE.Vector3(0, -1.9, 8), new THREE.Vector3(0, 0, -1));
    const first = ray.intersectObject(model.root, true)[0]?.object;
    let cursor: THREE.Object3D | null = first ?? null;
    let inInnerTower = false;
    while (cursor) {
      if (cursor.name.startsWith('内塔')) inInnerTower = true;
      cursor = cursor.parent;
    }
    expect(inInnerTower).toBe(true);
  });
});

it('displacement returns exactly to its origin at zero', () => {
  const origin: [number, number, number] = [1, 2, 3];
  const direction: [number, number, number] = [0, 1, 0];
  expect(displacedPosition(origin, direction, 4, 0)).toEqual(origin);
  expect(displacedPosition(origin, direction, 4, 1)).toEqual([1, 6, 3]);
});
