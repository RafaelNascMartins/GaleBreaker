import * as THREE from 'three';

// Textures are owned by the arena and shared between otherwise independent models.
export function disposeObjectResources(root: THREE.Object3D) {
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  root.traverse(object => {
    if (object instanceof THREE.Mesh) {
      geometries.add(object.geometry);
      for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
        materials.add(material);
      }
      if (object instanceof THREE.InstancedMesh) object.dispose();
    }
    if (object instanceof THREE.Light && 'shadow' in object) {
      (object.shadow as THREE.LightShadow | undefined)?.dispose();
    }
  });
  for (const geometry of geometries) geometry.dispose();
  for (const material of materials) material.dispose();
}
