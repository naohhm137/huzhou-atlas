import { describe, expect, it } from 'vitest';
import { advanceOrbit, advanceZoom } from '../orbitGesture';

describe('exhibit orbit gesture', () => {
  it('makes a quarter-stage horizontal drag visibly turn the object', () => {
    const result = advanceOrbit({ yaw: 0, pitch: 0 }, { x: 150, y: 0 }, { width: 600, height: 400 });
    expect(result.yaw).toBeGreaterThan(1.2);
    expect(result.pitch).toBe(0);
  });

  it('uses the stage dimensions and reverses without accumulating drift', () => {
    const moved = advanceOrbit({ yaw: 0, pitch: 0 }, { x: 100, y: 60 }, { width: 400, height: 400 });
    expect(moved.yaw).toBeGreaterThan(1.2);
    expect(moved.pitch).toBeGreaterThan(0.2);
    const back = advanceOrbit(moved, { x: -100, y: -60 }, { width: 400, height: 400 });
    expect(back.yaw).toBeCloseTo(0, 8);
    expect(back.pitch).toBeCloseTo(0, 8);
  });

  it('clamps vertical tilt so the exhibit cannot flip upside down', () => {
    const result = advanceOrbit({ yaw: 0, pitch: 0 }, { x: 0, y: 1000 }, { width: 390, height: 560 });
    expect(result.pitch).toBeGreaterThan(0.7);
    expect(result.pitch).toBeLessThanOrEqual(0.75);
  });
});

describe('expanded exhibit zoom', () => {
  it('moves closer on upward wheel input and clamps both ends', () => {
    expect(advanceZoom(1, -120)).toBeLessThan(1);
    expect(advanceZoom(0.46, -1000)).toBe(0.45);
    expect(advanceZoom(1.79, 1000)).toBe(1.8);
  });
});
