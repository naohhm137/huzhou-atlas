import * as THREE from 'three';
import { box, mesh, newModel, part, rod, type ExhibitModel, type Vec3 } from './shared';

const brick = new THREE.MeshStandardMaterial({ color: 0x985f4b, roughness: 0.93, side: THREE.DoubleSide });
const brickLight = new THREE.MeshStandardMaterial({ color: 0xb5785f, roughness: 0.88 });
const timber = new THREE.MeshStandardMaterial({ color: 0x3d3028, roughness: 0.78 });
const timberRed = new THREE.MeshStandardMaterial({ color: 0x733c32, roughness: 0.81 });
const roof = new THREE.MeshStandardMaterial({ color: 0x363f3b, roughness: 0.76, metalness: 0.04, side: THREE.DoubleSide });
const roofEdge = new THREE.MeshStandardMaterial({ color: 0x62706a, roughness: 0.66 });
const stone = new THREE.MeshStandardMaterial({ color: 0xc2bdaf, roughness: 0.94 });
const stoneShade = new THREE.MeshStandardMaterial({ color: 0x85877f, roughness: 0.98 });
const stoneDark = new THREE.MeshStandardMaterial({ color: 0x5b5d56, roughness: 1 });
const gold = new THREE.MeshStandardMaterial({ color: 0xb89d62, roughness: 0.48, metalness: 0.24 });

const circle = (radius: number, angle: number): Vec3 => [Math.sin(angle) * radius, 0, Math.cos(angle) * radius];

function octagon(parent: THREE.Object3D, top: number, bottom: number, height: number, material: THREE.Material, y = 0, open = false) {
  const object = mesh(parent, new THREE.CylinderGeometry(top, bottom, height, 8, 1, open), material, [0, y, 0]);
  object.rotation.y = Math.PI / 8;
  return object;
}

function railRing(parent: THREE.Object3D, radius: number, y: number, material: THREE.Material, thickness = 0.014) {
  for (let i = 0; i < 8; i++) {
    const a = i * Math.PI / 4 + Math.PI / 8;
    const b = (i + 1) * Math.PI / 4 + Math.PI / 8;
    const start = circle(radius, a);
    const end = circle(radius, b);
    rod(parent, [start[0], y, start[2]], [end[0], y, end[2]], thickness, material, 6);
  }
}

function roofTier(group: THREE.Group, radius: number, topY: number) {
  octagon(group, radius * 0.67, radius * 1.22, 0.19, roof, topY - 0.07);
  octagon(group, radius * 0.64, radius * 0.91, 0.05, roofEdge, topY + 0.015);
  railRing(group, radius * 1.22, topY - 0.17, roofEdge, 0.018);
  for (let i = 0; i < 8; i++) {
    const angle = i * Math.PI / 4 + Math.PI / 8;
    const edge = circle(radius * 1.23, angle);
    const mid = circle(radius * 0.66, angle);
    rod(group, [mid[0], topY + 0.035, mid[2]], [edge[0], topY - 0.14, edge[2]], 0.012, roofEdge, 5);
    const tip = circle(radius * 1.3, angle);
    const sweep = new THREE.CatmullRomCurve3([
      new THREE.Vector3(edge[0] * 0.92, topY - 0.13, edge[2] * 0.92),
      new THREE.Vector3(edge[0], topY - 0.13, edge[2]),
      new THREE.Vector3(tip[0], topY - 0.04, tip[2]),
    ]);
    mesh(group, new THREE.TubeGeometry(sweep, 8, 0.016, 5), roofEdge);
  }
}

function outerLevel(model: ExhibitModel, level: number) {
  const y = -1.88 + level * 0.61;
  const radius = 0.94 - level * 0.055;
  const group = part(model, `外塔楼层 ${level + 1} · 八角楼阁`, [0, y, 0], [0.12 * Math.sin(level), 1, 0.08 * Math.cos(level)], 0.32 + level * 0.12);
  // The historic shell is continuous; this digital section omits two front bays
  // and the lowest floor plates so visitors can actually see the stone tower.
  if (level >= 4) octagon(group, radius * 0.88, radius * 0.9, 0.067, timber, -0.31);
  else railRing(group, radius * 0.84, -0.31, timber, 0.026);
  for (let face = 0; face < 8; face++) {
    const angle = face * Math.PI / 4 + Math.PI / 8;
    const p = circle(radius * 0.82, angle);
    // The two front bays remain open, an interpretive cutaway into the smaller stone tower.
    if (face !== 0 && face !== 7) {
      const panel = box(group, [radius * 0.55, 0.31, 0.025], face % 2 ? brick : brickLight, [p[0], -0.02, p[2]]);
      panel.rotation.y = angle;
      for (let lattice = -1; lattice <= 1; lattice++) {
        const offset = lattice * radius * 0.14;
        const local: Vec3 = [p[0] + Math.cos(angle) * offset, -0.01, p[2] - Math.sin(angle) * offset];
        rod(group, [local[0], -0.17, local[2]], [local[0], 0.14, local[2]], 0.009, timber, 5);
      }
    }
    const corner = circle(radius * 0.87, angle + Math.PI / 8);
    rod(group, [corner[0], -0.28, corner[2]], [corner[0], 0.19, corner[2]], 0.031, timberRed, 8);
    const beamStart = circle(radius * 0.68, angle);
    const beamEnd = circle(radius * 1.03, angle);
    rod(group, [beamStart[0], 0.14, beamStart[2]], [beamEnd[0], 0.14, beamEnd[2]], 0.018, timber, 6);
  }
  railRing(group, radius * 0.92, -0.22, timber, 0.018);
  const eave = part(model, `外塔飞檐 ${level + 1} · 瓦脊与翘角`, [0, y + 0.34, 0], [level % 2 ? -0.3 : 0.3, 1, 0.25], 0.45 + level * 0.07);
  roofTier(eave, radius, 0);
  return radius;
}

function brackets(model: ExhibitModel) {
  const group = part(model, '外塔斗拱 · 檐下层叠支承', [0, 0, 0], [0.85, 0.2, 0.2], 0.65);
  for (let level = 0; level < 7; level++) {
    const y = -1.88 + level * 0.61 + 0.20;
    const radius = 0.94 - level * 0.055;
    for (let face = 0; face < 8; face++) {
      const angle = face * Math.PI / 4 + Math.PI / 8;
      for (let step = 0; step < 3; step++) {
        const p = circle(radius * (0.77 + step * 0.12), angle);
        const arm = box(group, [0.13 + step * 0.06, 0.035, 0.085], step === 2 ? gold : timberRed, [p[0], y + step * 0.044, p[2]]);
        arm.rotation.y = angle;
        const post = circle(radius * (0.8 + step * 0.1), angle);
        rod(group, [post[0], y + step * 0.043 - 0.04, post[2]], [post[0], y + step * 0.043 + 0.04, post[2]], 0.012, timber, 5);
      }
    }
  }
}

function innerLevel(model: ExhibitModel, level: number) {
  const y = -1.93 + level * 0.25;
  const radius = 0.39 - level * 0.034;
  const group = part(model, `内塔石层 ${level + 1} · 佛龛与石檐`, [0, y, 0], [0.1 * Math.sin(level * 1.7), 0.45 + level * 0.06, 0.3], 0.29 + level * 0.08);
  octagon(group, radius * 0.78, radius * 0.85, 0.19, stone, 0.02);
  octagon(group, radius * 1.12, radius * 0.75, 0.064, stoneShade, 0.14);
  railRing(group, radius * 1.07, 0.11, stone, 0.012);
  for (let face = 0; face < 8; face++) {
    const angle = face * Math.PI / 4 + Math.PI / 8;
    const p = circle(radius * 0.88, angle);
    const niche = box(group, [radius * 0.25, 0.105, 0.008], stoneDark, [p[0], 0.025, p[2]]);
    niche.rotation.y = angle;
    if (face % 2 === level % 2) {
      const statue = mesh(group, new THREE.ConeGeometry(0.022, 0.063, 10), gold, [p[0] * 1.015, 0.018, p[2] * 1.015]);
      statue.rotation.y = angle;
      mesh(group, new THREE.SphereGeometry(0.015, 8, 6), gold, [p[0] * 1.015, 0.065, p[2] * 1.015]);
    }
    const column = circle(radius * 0.92, angle + Math.PI / 8);
    rod(group, [column[0], -0.06, column[2]], [column[0], 0.12, column[2]], 0.013, stoneShade, 6);
  }
}

export function makeTower(): ExhibitModel {
  const model = newModel();
  const foundation = part(model, '塔基 · 八角台座', [0, -2.45, 0], [0, -1, 0], 0.36);
  octagon(foundation, 1.01, 1.10, 0.23, stoneShade);
  octagon(foundation, 1.04, 1.04, 0.055, stone, 0.14);
  const sumeru = part(model, '内塔须弥座 · 莲瓣与束腰', [0, -2.13, 0], [0.7, -0.25, 0], 0.58);
  octagon(sumeru, 0.46, 0.58, 0.14, stone, -0.04);
  octagon(sumeru, 0.48, 0.48, 0.085, stoneShade, 0.06);
  for (let i = 0; i < 24; i++) {
    const a = i * Math.PI * 2 / 24;
    const p = circle(0.5, a);
    const petal = mesh(sumeru, new THREE.SphereGeometry(1, 8, 6), stone, [p[0], 0.02, p[2]]);
    petal.scale.set(0.07, 0.085, 0.03);
    petal.rotation.y = a;
  }
  for (let level = 0; level < 5; level++) innerLevel(model, level);
  for (let level = 0; level < 7; level++) outerLevel(model, level);
  brackets(model);
  const finial = part(model, '塔刹 · 外塔顶饰', [0, 2.27, 0], [0, 1, 0], 0.62);
  rod(finial, [0, -0.15, 0], [0, 0.66, 0], 0.028, gold, 10);
  for (let i = 0; i < 7; i++) {
    mesh(finial, new THREE.SphereGeometry(0.075 - i * 0.006, 12, 8), gold, [0, 0.1 + i * 0.077, 0]);
  }
  mesh(finial, new THREE.ConeGeometry(0.062, 0.19, 12), gold, [0, 0.75, 0]);
  model.metadata = { outerLevels: 7, innerLevels: 5, outerSides: 8 };
  model.root.rotation.y = -0.22;
  return model;
}
