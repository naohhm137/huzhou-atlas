import * as THREE from 'three';
import { mesh, newModel, part, rod, type ExhibitModel } from './shared';

const bamboo = new THREE.MeshStandardMaterial({ color: 0xb59a68, roughness: 0.69 });
const bambooEdge = new THREE.MeshStandardMaterial({ color: 0x715638, roughness: 0.8 });
const silkCord = new THREE.MeshStandardMaterial({ color: 0x9a7960, roughness: 0.88 });
const purpleHair = new THREE.MeshStandardMaterial({ color: 0x40322d, roughness: 0.96 });
const creamHair = new THREE.MeshStandardMaterial({ color: 0xd3c6a9, roughness: 0.95 });

function hairLayer(group: THREE.Group, count: number, outerRadius: number, length: number, color: THREE.Material, phase = 0) {
  for (let i = 0; i < count; i++) {
    const theta = i * 2.399963 + phase;
    const radius = outerRadius * Math.sqrt((i + 0.5) / count);
    const x = Math.cos(theta) * radius;
    const z = Math.sin(theta) * radius;
    const path = new THREE.CatmullRomCurve3([
      new THREE.Vector3(x * 0.72, 0.29, z * 0.72),
      new THREE.Vector3(x * 1.23, 0.05, z * 1.23),
      new THREE.Vector3(x * 1.05, -length * 0.36, z * 1.05),
      new THREE.Vector3(x * 0.48, -length * 0.72, z * 0.48),
      new THREE.Vector3(0, -length, 0),
    ]);
    mesh(group, new THREE.TubeGeometry(path, 12, i % 5 === 0 ? 0.0035 : 0.0022, 3), color);
  }
}

export function makeBrush(): ExhibitModel {
  const model = newModel();
  const shaftLength = 3.42;
  const shaftDiameter = 0.18;
  model.metadata = { shaftLength, shaftDiameter };
  const shaft = part(model, '竹管 · 细长笔杆', [0, 0.67, 0], [0, 1, 0], 0.58);
  mesh(shaft, new THREE.CylinderGeometry(0.085, 0.09, shaftLength, 32), bamboo);
  for (const y of [-1.48, 1.5]) {
    mesh(shaft, new THREE.CylinderGeometry(0.091, 0.091, 0.055, 32), bambooEdge, [0, y, 0]);
  }
  const cap = part(model, '笔帽 · 竹筒', [0, 2.25, 0], [0.35, 1, 0], 0.7);
  mesh(cap, new THREE.CylinderGeometry(0.103, 0.103, 0.65, 32, 1, true), bamboo, [0, 0.28, 0]);
  mesh(cap, new THREE.CylinderGeometry(0.105, 0.105, 0.045, 32), bambooEdge, [0, 0.61, 0]);
  const socket = part(model, '管口 · 嵌接', [0, -1.12, 0], [-0.35, -0.3, 0], 0.48);
  mesh(socket, new THREE.CylinderGeometry(0.088, 0.112, 0.3, 32), bambooEdge);
  const cord = part(model, '毫根 · 丝线捆扎', [0, -1.32, 0], [0.7, 0.1, 0], 0.58);
  mesh(cord, new THREE.CylinderGeometry(0.106, 0.11, 0.18, 32), silkCord);
  for (let i = 0; i < 8; i++) {
    const y = -0.07 + i * 0.018;
    const ring = mesh(cord, new THREE.TorusGeometry(0.111, 0.0035, 4, 40), creamHair, [0, y, 0]);
    ring.rotation.x = Math.PI / 2;
  }
  const inner = part(model, '芯毫 · 兰蕊形腰', [0, -1.72, 0], [-0.35, -1, 0.2], 0.54);
  hairLayer(inner, 84, 0.082, 0.68, purpleHair, 0.3);
  const outerA = part(model, '外毫 · 第一束', [0, -1.72, 0], [1, -0.65, 0], 0.74);
  hairLayer(outerA, 94, 0.145, 0.66, creamHair);
  const outerB = part(model, '外毫 · 第二束', [0, -1.72, 0], [-0.8, -0.65, 0.3], 0.72);
  hairLayer(outerB, 92, 0.125, 0.74, purpleHair, 1.7);
  const point = part(model, '锋颖 · 透明尖端', [0, -2.23, 0], [0, -1, 0], 0.52);
  for (let i = 0; i < 38; i++) {
    const a = i * Math.PI * 2 / 38;
    rod(point, [Math.cos(a) * 0.038, 0.18, Math.sin(a) * 0.038], [0, -0.38, 0], 0.0018, i % 3 ? purpleHair : creamHair, 3);
  }
  model.root.rotation.z = -0.35;
  model.root.rotation.y = -0.23;
  return model;
}
