import * as THREE from 'three';
import { box, mesh, newModel, part, rod, type ExhibitModel } from './shared';

const oak = new THREE.MeshStandardMaterial({ color: 0x876744, roughness: 0.78 });
const oakDark = new THREE.MeshStandardMaterial({ color: 0x503c2b, roughness: 0.86 });
const silk = new THREE.MeshPhysicalMaterial({ color: 0xf2deb0, roughness: 0.43, sheen: 0.9, sheenColor: new THREE.Color(0xffedca) });
const silkShadow = new THREE.MeshPhysicalMaterial({ color: 0xbfa27a, roughness: 0.47, sheen: 0.65 });
const brass = new THREE.MeshStandardMaterial({ color: 0xb3945b, metalness: 0.6, roughness: 0.33 });

export function makeLoom(): ExhibitModel {
  const model = newModel();
  const frame = part(model, '机架 · 水平木构', [0, 0, 0], [0, -1, 0], 0.35);
  for (const x of [-1.55, 1.55]) {
    for (const z of [-1.42, 1.42]) {
      box(frame, [0.13, 2.18, 0.13], oakDark, [x, -0.22, z]);
      mesh(frame, new THREE.SphereGeometry(0.09, 12, 10), oak, [x, 0.92, z]);
    }
    box(frame, [0.13, 0.13, 3], oak, [x, -0.82, 0]);
    box(frame, [0.12, 0.12, 3], oak, [x, 0.42, 0]);
  }
  for (const z of [-1.42, 1.42]) {
    box(frame, [3.24, 0.13, 0.14], oak, [0, -0.8, z]);
    box(frame, [3.24, 0.1, 0.12], oakDark, [0, 0.42, z]);
  }
  const warpBeam = part(model, '经轴 · 送经', [0, -0.23, -1.36], [0, 0, -1], 0.72);
  rod(warpBeam, [-1.38, 0, 0], [1.38, 0, 0], 0.19, oak, 24);
  for (const x of [-1.4, 1.4]) {
    mesh(warpBeam, new THREE.CylinderGeometry(0.28, 0.28, 0.055, 24), oakDark, [x, 0, 0]).rotation.z = Math.PI / 2;
  }
  const clothBeam = part(model, '卷布轴 · 成绫', [0, -0.23, 1.36], [0, 0, 1], 0.75);
  rod(clothBeam, [-1.38, 0, 0], [1.38, 0, 0], 0.19, oak, 24);
  for (const x of [-1.4, 1.4]) {
    mesh(clothBeam, new THREE.CylinderGeometry(0.28, 0.28, 0.055, 24), oakDark, [x, 0, 0]).rotation.z = Math.PI / 2;
  }
  const heddleFront = part(model, '综片 · 提经前组', [0, 0.23, -0.17], [0, 1, -0.5], 0.8);
  const heddleRear = part(model, '综片 · 提经后组', [0, 0.42, -0.55], [0, 1, 0.5], 0.8);
  for (const [group, z] of [[heddleFront, 0], [heddleRear, 0]] as const) {
    for (const y of [-0.28, 0.28]) box(group, [3.05, 0.065, 0.08], oakDark, [0, y, z]);
    for (const x of [-1.43, 1.43]) box(group, [0.065, 0.62, 0.08], oakDark, [x, 0, z]);
    for (let i = 0; i < 36; i++) {
      const x = (i - 17.5) * 0.078;
      rod(group, [x, -0.24, 0], [x, 0.24, 0], 0.003, brass, 4);
    }
  }
  const reed = part(model, '筘 · 打纬密排', [0, 0.1, 0.51], [0, 1, 0.8], 0.8);
  for (const y of [-0.3, 0.3]) box(reed, [3.1, 0.09, 0.1], oakDark, [0, y, 0]);
  for (let i = 0; i < 74; i++) {
    const x = (i - 36.5) * 0.04;
    rod(reed, [x, -0.26, 0], [x, 0.26, 0], 0.0028, brass, 4);
  }
  const warpCount = 72;
  for (let i = 0; i < warpCount; i++) {
    const x = (i - (warpCount - 1) / 2) * 0.039;
    const rise = i % 2 === 0 ? 0.055 : -0.055;
    const strand = part(model, `经丝 ${String(i + 1).padStart(2, '0')}`, [x, 0.06, 0], [x / 1.4, 0.22 + (i % 2) * 0.2, 0], 0.35);
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0, -0.12, -1.32),
      new THREE.Vector3(0, rise, -0.65),
      new THREE.Vector3(0, rise, -0.15),
      new THREE.Vector3(0, 0.02, 0.5),
      new THREE.Vector3(0, -0.11, 1.32),
    ]);
    mesh(strand, new THREE.TubeGeometry(curve, 18, 0.006, 4), i % 7 === 0 ? silkShadow : silk);
  }
  const weft = part(model, '纬丝 · 穿梭交织', [0, 0.06, 0.52], [0, 0.45, 1], 0.65);
  for (let row = 0; row < 17; row++) {
    const z = row * 0.046;
    const points: THREE.Vector3[] = [];
    for (let i = 0; i <= 72; i++) {
      points.push(new THREE.Vector3(-1.39 + i * 0.039, (i + row) % 2 ? 0.02 : 0.065, z));
    }
    mesh(weft, new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), 76, 0.006, 4), row % 5 ? silk : silkShadow);
  }
  const shuttle = part(model, '梭 · 木梭与纡管', [0.1, -0.04, 0.36], [1, 0.35, 0.5], 1.05);
  const hull = mesh(shuttle, new THREE.SphereGeometry(1, 24, 12), oak, [0, 0, 0]);
  hull.scale.set(0.52, 0.09, 0.16);
  rod(shuttle, [-0.25, 0.06, 0], [0.25, 0.06, 0], 0.035, silkShadow, 12);
  for (let i = 0; i < 12; i++) {
    const x = (i - 5.5) * 0.04;
    rod(shuttle, [x, 0.095, -0.034], [x, 0.095, 0.034], 0.0028, silk, 4);
  }
  const cloth = part(model, '织物 · 绫绢组织', [0, -0.1, 0.95], [0, -0.55, 1], 0.65);
  for (let i = 0; i < 72; i++) {
    const x = (i - 35.5) * 0.039;
    rod(cloth, [x, 0, -0.35], [x, 0, 0.35], 0.005, silk, 4);
  }
  for (let i = 0; i < 25; i++) {
    const z = (i - 12) * 0.029;
    rod(cloth, [-1.4, 0.002, z], [1.4, 0.002, z], 0.005, i % 6 ? silk : silkShadow, 4);
  }
  model.metadata = { warpCount };
  model.root.rotation.y = -0.38;
  return model;
}
