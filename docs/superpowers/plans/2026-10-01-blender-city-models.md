# Blender City Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace four photo-only city chapters with polished Blender-authored 3D scenes while retaining credited real-photo backdrops.

**Architecture:** A standalone Blender generator writes four editable scenes and GLBs whose named Empty nodes use the existing explosion metadata contract. The existing Three.js exhibit renderer loads these assets with city-specific framing and lighting. CityChapter owns photo switching and the expanded-stage UI; App owns scene controllers and scroll progress.

**Tech Stack:** Blender 4.2 Python API, glTF/GLB, Three.js, React, GSAP ScrollTrigger, Vitest, Vite.

**Spec:** `docs/superpowers/specs/2026-10-01-blender-city-models-design.md`

## Global Constraints

- Preserve the existing four craft/tower chapters.
- Retain and credit the eight existing Wikimedia city photographs.
- Label city models as interpretive; do not claim measured historic reconstruction.
- Keep local-only delivery until user approval.
- Honor reduced motion and mobile layouts.

---

### Task 1: Blender asset contract and four scenes

**Files:** Create `assets/blender/build_city.py`; create `src/tests/cityAssets.test.ts`; generate `assets/blender/sources/city-*.blend`, `assets/blender/previews/city-*.png`, `public/models/city-*.glb`.

**Interfaces:** Each GLB contains at least four movable named parent nodes with numeric `explodeDirection` and positive `explodeDistance`, embedded color/roughness/normal texture images, and camera/light-free geometry.

- [ ] Write tests that read the four GLB JSON chunks and assert geometry, part names, texture slots and source `.blend` presence.
- [ ] Run the new tests and confirm they fail because city GLBs are absent.
- [ ] Implement the four Blender scenes using repeated low-level geometry only where repetition conveys real construction (tiles, glazing, paving, bulbs).
- [ ] Run Blender headless, export GLBs and preview renders; inspect each preview and correct the entire asset batch once.
- [ ] Run the new tests and confirm they pass.

### Task 2: Model loading and chapter interaction

**Files:** Modify `src/modelAsset.ts`, `src/exhibits.ts`, `src/CityChapter.tsx`, `src/site.tsx`, `src/style.css`, `src/tests/modelAsset.test.ts`.

**Interfaces:** `ExhibitAssetKind` adds `yishang | dongwu | longemont | nanxun-city`; `CityChapter` takes `scene`, controller registration, expanded state and toggle callback. The shared scene controller still provides `setProgress`, `setExpanded`, and `resetRotation`.

- [ ] Write failing tests for the added city model paths and metadata contract.
- [ ] Reuse the existing Three.js scene in city stages; add city-specific framing and lighting without changing original exhibit behavior.
- [ ] Expose rotate, expand, close, and photo switch controls; route city scroll progress to the controller.
- [ ] Style model/photo composition on desktop, 768px, and narrow mobile; keep the photo visible behind the model.
- [ ] Run tests and build.

### Task 3: Evidence, visual QA, and local handoff

**Files:** Modify `DESIGN.md`, `PRODUCT.md`, `REFERENCE_RESEARCH.md`; update changed code as needed from QA.

- [ ] Document each interpretive model and its real-photo references; preserve license credits.
- [ ] Inspect all four scenes assembled and expanded on desktop and mobile, including reversibility, dragging, image change, overlap, and console.
- [ ] Fix issues in one batch and perform a single confirmation pass.
- [ ] Run `pnpm test`, `pnpm build`, and Impeccable detector, then provide only the local URL.
