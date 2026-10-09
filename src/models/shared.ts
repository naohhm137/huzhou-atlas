import * as THREE from 'three';

export type Vec3 = [number, number, number];
export type MovablePart = {
  group: THREE.Group;
  origin: THREE.Vector3;
  direction: THREE.Vector3;
  distance: number;
};
export type ExhibitModel = {
  root: THREE.Group;
  parts: MovablePart[];
  metadata: Record<string, number>;
};

export function displacedPosition(origin: Vec3, direction: Vec3, distance: number, amount: number): Vec3 {
  return [origin[0] + direction[0] * distance * amount, origin[1] + direction[1] * distance * amount, origin[2] + direction[2] * distance * amount];
}

export function newModel(): ExhibitModel {
  return { root: new THREE.Group(), parts: [], metadata: {} };
}

export function part(model: ExhibitModel, name: string, position: Vec3, direction: Vec3, distance: number, parent = model.root) {
  const group = new THREE.Group();
  group.name = name;
  group.position.set(...position);
  parent.add(group);
  model.parts.push({ group, origin: group.position.clone(), direction: new THREE.Vector3(...direction).normalize(), distance });
  return group;
}

export function mesh(parent: THREE.Object3D, geometry: THREE.BufferGeometry, material: THREE.Material, at: Vec3 = [0, 0, 0]) {
  const object = new THREE.Mesh(geometry, material);
  object.position.set(...at);
  object.castShadow = true;
  object.receiveShadow = true;
  parent.add(object);
  return object;
}

export function rod(parent: THREE.Object3D, from: Vec3, to: Vec3, radius: number, material: THREE.Material, segments = 8) {
  const a = new THREE.Vector3(...from);
  const b = new THREE.Vector3(...to);
  const object = mesh(parent, new THREE.CylinderGeometry(radius, radius, a.distanceTo(b), segments), material);
  object.position.copy(a).add(b).multiplyScalar(0.5);
  object.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.sub(a).normalize());
  return object;
}

export function box(parent: THREE.Object3D, size: Vec3, material: THREE.Material, at: Vec3 = [0, 0, 0]) {
  return mesh(parent, new THREE.BoxGeometry(...size), material, at);
}

export function lathe(parent: THREE.Object3D, points: [number, number][], material: THREE.Material, at: Vec3 = [0, 0, 0], segments = 64) {
  return mesh(parent, new THREE.LatheGeometry(points.map(([x, y]) => new THREE.Vector2(x, y)), segments), material, at);
}
