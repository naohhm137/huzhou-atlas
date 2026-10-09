import * as THREE from 'three';
import { lathe, mesh, newModel, part, rod, type ExhibitModel } from './shared';

const celadon = new THREE.MeshPhysicalMaterial({ color: 0xa8b9a4, roughness: 0.25, metalness: 0.02, clearcoat: 0.85, clearcoatRoughness: 0.17, side: THREE.DoubleSide });
const celadonDark = new THREE.MeshPhysicalMaterial({ color: 0x718f7c, roughness: 0.32, clearcoat: 0.65, side: THREE.DoubleSide });
const glazeLine = new THREE.MeshStandardMaterial({ color: 0xd8dbbd, roughness: 0.33 });
const tea = new THREE.MeshPhysicalMaterial({ color: 0x9eae55, roughness: 0.11, transparent: true, opacity: 0.74, transmission: 0.25, thickness: 0.2, ior: 1.33, side: THREE.DoubleSide, depthWrite: false });
const teaSurface = new THREE.MeshPhysicalMaterial({ color: 0xb4bd72, roughness: 0.12, transparent: true, opacity: 0.79, side: THREE.DoubleSide, depthWrite: false });
const leafGreen = new THREE.MeshStandardMaterial({ color: 0x687d43, roughness: 0.59, side: THREE.DoubleSide });
const leafLight = new THREE.MeshStandardMaterial({ color: 0x899558, roughness: 0.55, side: THREE.DoubleSide });
const vein = new THREE.MeshStandardMaterial({ color: 0xb0ae74, roughness: 0.68 });

function makeLeaf(parent: THREE.Group, length: number, width: number, material: THREE.Material) {
  const vertices = new Float32Array([
    0, 0, -length * 0.48,
    -width * 0.65, 0.015, -length * 0.18,
    -width, 0.038, length * 0.07,
    0, 0.10, length * 0.49,
    width, 0.038, length * 0.07,
    width * 0.65, 0.015, -length * 0.18,
  ]);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
  geometry.setIndex([0, 1, 5, 1, 2, 3, 1, 3, 5, 5, 3, 4]);
  geometry.computeVertexNormals();
  mesh(parent, geometry, material);
  rod(parent, [0, 0.005, -length * 0.46], [0, 0.105, length * 0.47], 0.004, vein, 4);
  for (const side of [-1, 1]) {
    for (let n = 0; n < 3; n++) {
      const z = -length * 0.23 + n * length * 0.17;
      rod(parent, [0, 0.055, z + length * 0.13], [side * width * (0.66 + n * 0.08), 0.043, z], 0.002, vein, 3);
    }
  }
}

export function makeTea(): ExhibitModel {
  const model = newModel();
  model.metadata = { bowlDiameter: 2.0, saucerDiameter: 2.72 };
  const saucer = part(model, '盏托 · 大折沿承盏', [0, -0.82, 0], [0, -1, 0], 0.82);
  lathe(saucer, [
    [0, -0.12], [0.55, -0.12], [0.59, -0.08], [0.58, 0.02],
    [0.83, 0.06], [1.08, 0.08], [1.34, 0.27], [1.36, 0.30],
    [1.31, 0.33], [1.02, 0.16], [0.78, 0.15], [0.56, 0.11], [0, 0.08],
  ], celadon, [0, 0, 0], 96);
  const saucerFoot = part(model, '盏托圈足 · 剖层示意', [0, -0.96, 0], [0.6, -0.8, 0], 0.42);
  lathe(saucerFoot, [[0.48, -0.09], [0.58, -0.09], [0.59, 0.07], [0.49, 0.07]], celadonDark);
  const bowl = part(model, '青瓷盏身 · 深腹与内壁', [0, -0.12, 0], [0, 0.7, 0], 0.75);
  lathe(bowl, [
    [0, -0.46], [0.39, -0.46], [0.50, -0.40], [0.63, -0.23],
    [0.81, 0.08], [0.95, 0.43], [0.99, 0.50], [1.0, 0.53],
    [0.955, 0.55], [0.91, 0.50], [0.77, 0.13], [0.59, -0.19],
    [0.47, -0.35], [0.36, -0.37], [0, -0.37],
  ], celadon, [0, 0, 0], 96);
  const lip = part(model, '盏口 · 薄釉唇', [0, 0.405, 0], [0.55, 0.45, 0], 0.32);
  const lipRing = mesh(lip, new THREE.TorusGeometry(0.975, 0.025, 10, 96), glazeLine);
  lipRing.rotation.x = Math.PI / 2;
  const bowlFoot = part(model, '盏身圈足 · 剖层示意', [0, -0.59, 0], [-0.65, -0.5, 0], 0.49);
  lathe(bowlFoot, [[0.34, -0.07], [0.45, -0.07], [0.47, 0.08], [0.38, 0.08]], celadonDark);
  const infusion = part(model, '茶汤 · 有体积的澄黄液层', [0, 0.02, 0], [0, 1, 0], 0.92);
  lathe(infusion, [
    [0, -0.25], [0.49, -0.25], [0.58, -0.16], [0.70, 0.01],
    [0.83, 0.24], [0.835, 0.26], [0.79, 0.27], [0.62, 0.245], [0.32, 0.24], [0, 0.245],
  ], tea, [0, 0, 0], 80);
  const meniscus = mesh(infusion, new THREE.CircleGeometry(0.81, 80), teaSurface, [0, 0.255, 0]);
  meniscus.rotation.x = -Math.PI / 2;
  const rim = mesh(infusion, new THREE.TorusGeometry(0.82, 0.009, 6, 80), glazeLine, [0, 0.254, 0]);
  rim.rotation.x = Math.PI / 2;
  for (let i = 0; i < 7; i++) {
    const a = i * 2.39996;
    const r = 0.11 + (i % 3) * 0.18;
    const group = part(model, `芽叶 ${i + 1} · 一芽一叶`, [Math.cos(a) * r, 0.30 + i * 0.005, Math.sin(a) * r], [Math.cos(a), 0.78 + i * 0.05, Math.sin(a)], 0.42 + i * 0.055);
    group.rotation.y = a;
    group.rotation.x = -0.08 + i * 0.025;
    makeLeaf(group, 0.28 + (i % 3) * 0.035, 0.064, i % 2 ? leafGreen : leafLight);
    const bud = mesh(group, new THREE.SphereGeometry(1, 12, 8), leafLight, [0.04, 0.045, -0.16]);
    bud.scale.set(0.028, 0.022, 0.105);
    bud.rotation.y = -0.28;
    rod(group, [0, 0, -0.2], [0.04, 0.045, -0.16], 0.008, vein, 5);
  }
  model.root.rotation.y = -0.17;
  return model;
}
