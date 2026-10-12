# Lux3D high-fidelity review · 2026-10-11

## Generated assets

| Exhibit | Route | File | Blender import check |
|---|---|---|---|
| 湖笔 | Lux3D G1 image-to-3D | `public/models/brush-lux3d.glb` | passed: 1 object, 1 material |
| 双林织机 | Lux3D G1 text+image-to-3D | `public/models/loom-lux3d.glb` | passed: 1 object, 1 material |
| 顾渚茶器 | Lux3D G1 image-to-3D | `public/models/tea-lux3d.glb` | passed: 2 objects, 1 material |
| 飞英塔 | Lux3D G1-Turbo text+image-to-3D | `public/models/tower-lux3d.glb` | passed: 2 objects, 1 material |

## Material and reference gates

All four generation prompts require reference-constrained silhouette, physically based materials, roughness/normal/AO detail, believable wear and scale, and no plastic/cartoon artifacts. The reference set is recorded in `public/asset-index.json` and the site footer links to the Palace Museum, China Silk Museum, Feiying Pagoda structural references, and source photography.

## Verification

- `pnpm test`: 11 files, 41 tests passed.
- `pnpm build`: passed.
- Blender 4.2.16 background GLB import: all four Lux3D files passed.
- Lux3D task status: all four core tasks reached terminal success status 3.
