// Scroll progress is the single timeline (tutorial 5.1): every visual state below is a pure
// function of progress, so scrolling back lands on exactly the same state.
export type Vec3 = [number, number, number];

export type ShotKey = {
  target: Vec3;
  position: Vec3;
  /** Focal length in mm on a 36 mm-wide sensor, same as the Blender shots. */
  lens: number;
  /** Horizontal frame shift as a fraction of width (Blender shift_x). */
  shiftX: number;
  explode: number;
  cut: number;
  /** Shot 04 is framed relative to the separate dougong exhibit node. */
  anchor: 'tower' | 'dougong';
};

// Three.js coordinates (Y-up). Converted from production/feiying/scripts/render_shots.py,
// Blender (x, y, z) → three (x, z, -y).
export const SHOTS: readonly ShotKey[] = [
  { target: [0, 20, 0], position: [10, 4, 58], lens: 32, shiftX: 0, explode: 0, cut: 0, anchor: 'tower' },
  { target: [0, 22, 0], position: [-16, 2, 34], lens: 24, shiftX: -0.2, explode: 0, cut: 0, anchor: 'tower' },
  { target: [0, 25, 0], position: [12, 9, 96], lens: 32, shiftX: -0.14, explode: 0.55, cut: 1, anchor: 'tower' },
  { target: [0, 1.9, 0], position: [3, 0, 4.2], lens: 38, shiftX: -0.15, explode: 0, cut: 0, anchor: 'dougong' },
  { target: [0, 14, 0], position: [4.5, 2, 13], lens: 20, shiftX: 0.2, explode: 0, cut: 1, anchor: 'tower' },
  { target: [0, 19, 0], position: [-14, 4, 60], lens: 34, shiftX: 0.2, explode: 0, cut: 0, anchor: 'tower' },
] as const;

export const SCREEN_COUNT = SHOTS.length;
/** Share of each screen's scroll band spent holding the shot before moving on. */
const HOLD = 0.55;

export const clamp = (v: number, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
const smooth = (a: number, b: number, v: number) => {
  const t = clamp((v - a) / (b - a));
  return t * t * (3 - 2 * t);
};
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const lerp3 = (a: Vec3, b: Vec3, t: number): Vec3 => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
const add3 = (a: Vec3, b: Vec3): Vec3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];

/** Continuous screen index 0..5: integers while a screen holds, eased in between. */
export function screenPosition(progress: number): number {
  const p = clamp(progress);
  const band = Math.min(SCREEN_COUNT - 1, Math.floor(p * SCREEN_COUNT));
  if (band === SCREEN_COUNT - 1) return band;
  return band + smooth(HOLD, 1, p * SCREEN_COUNT - band);
}

/** Scroll progress that lands inside screen i's hold, for navigation clicks. */
export function progressForScreen(index: number): number {
  return clamp((index + 0.2) / SCREEN_COUNT);
}

export function vfovForLens(lens: number): number {
  // Horizontal sensor 36 mm at the 16:9 reference frame → vertical half-height 10.125 mm.
  return (2 * Math.atan(10.125 / lens) * 180) / Math.PI;
}

export type Pose = {
  position: Vec3;
  target: Vec3;
  fov: number;
  shiftX: number;
  explode: number;
  cut: number;
  /** 0..1 black dip used when the camera cuts to or from the separate dougong exhibit. */
  fade: number;
  /** Which subject is on stage. */
  subject: 'tower' | 'dougong';
};

function keyPose(key: ShotKey, dougong: Vec3): Pose {
  const base: Vec3 = key.anchor === 'dougong' ? dougong : [0, 0, 0];
  return {
    position: add3(base, key.position), target: add3(base, key.target), fov: vfovForLens(key.lens),
    shiftX: key.shiftX, explode: key.explode, cut: key.cut, fade: 0, subject: key.anchor,
  };
}

/** Move the camera a share of the way toward (positive) or away from (negative) its target. */
function dolly(pose: Pose, amount: number): Pose {
  return { ...pose, position: lerp3(pose.position, pose.target, amount) };
}

function mix(a: Pose, b: Pose, t: number): Pose {
  return {
    position: lerp3(a.position, b.position, t), target: lerp3(a.target, b.target, t),
    fov: lerp(a.fov, b.fov, t), shiftX: lerp(a.shiftX, b.shiftX, t),
    explode: lerp(a.explode, b.explode, t), cut: lerp(a.cut, b.cut, t),
    fade: lerp(a.fade, b.fade, t), subject: t < 0.5 ? a.subject : b.subject,
  };
}

export function poseAt(s: number, dougong: Vec3 = [0, 0, 0]): Pose {
  const pos = clamp(s, 0, SCREEN_COUNT - 1);
  const i = Math.min(SCREEN_COUNT - 2, Math.floor(pos));
  const f = pos - i;
  const a = keyPose(SHOTS[i], dougong);
  const b = keyPose(SHOTS[i + 1], dougong);
  if (a.subject === b.subject) return mix(a, b, f);
  // Subject change: push in and dip to black, then pull back from black on the new subject.
  if (f < 0.5) {
    const t = smooth(0, 1, f * 2);
    return { ...mix(a, dolly(a, 0.3), t), fade: t };
  }
  const t = smooth(0, 1, (f - 0.5) * 2);
  return { ...mix(dolly(b, -0.3), b, t), fade: 1 - t };
}

/** Opacity of screen i's HTML copy at continuous position s. */
export function screenOpacity(i: number, s: number): number {
  return clamp(1 - Math.abs(s - i) * 2.4);
}

/** Piecewise-linear layer weight sampled at s from per-screen values. */
export function layerWeight(values: readonly number[], s: number): number {
  const pos = clamp(s, 0, values.length - 1);
  const i = Math.min(values.length - 2, Math.floor(pos));
  return lerp(values[i], values[i + 1], pos - i);
}

/** Parallax layer weights per screen (tutorial 5.4 step 4: layers move at different rates). */
export const PINES = [1, 0.55, 0, 0, 0, 1] as const;
export const MIST = [1, 0.8, 0.45, 0, 0.25, 1] as const;

/**
 * Cutaway wedge: two vertical planes through the tower axis bounding a wedge that faces the
 * camera. Returns three.js plane normals for `clipIntersection` (a fragment is clipped only
 * when it is behind both planes). `opening` animates the wedge's angle from 0° (planes
 * coincide, nothing clipped) to 90°.
 */
export function wedgePlanes(camera: Vec3, opening: number): { normals: [Vec3, Vec3]; constant: number } {
  const yaw = Math.atan2(-camera[2], camera[0]); // Blender-frame yaw of the camera around the axis
  const half = (Math.PI / 4) * clamp(opening);
  const a = yaw - half;
  const b = yaw + half;
  // Blender-frame normals pointing into the wedge: (-sin a, cos a) and (sin b, -cos b).
  // Converted to three (x, 0, -y) and negated, so "clipped" ⇔ inside both half-spaces.
  return {
    normals: [[Math.sin(a), 0, Math.cos(a)], [-Math.sin(b), 0, -Math.cos(b)]],
    constant: 0,
  };
}
