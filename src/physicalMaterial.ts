import * as THREE from 'three';
export function toPhysicalMaterial(material: THREE.MeshStandardMaterial) {
  const physical = new THREE.MeshPhysicalMaterial();
  // GLTF commonly provides Standard materials. Physical.copy also reads
  // Physical-only fields, so copy the shared PBR fields through the base class.
  THREE.MeshStandardMaterial.prototype.copy.call(physical, material);
  Object.assign(physical, { defines: { STANDARD: '', PHYSICAL: '' } });
  physical.clearcoat = 0.22;
  physical.clearcoatRoughness = 0.3;
  physical.sheen = 0.08;
  return physical;
}
