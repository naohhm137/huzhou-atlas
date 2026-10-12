# OJO Cinematic Scroll Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Rebuild the Huzhou Atlas experience as a cinematic, multi-stage OJO-style scroll narrative whose models, camera, lighting, materials, annotations, and decomposition advance together at every scroll segment.

**Architecture:** Each exhibit becomes a pinned `ScrollStory` with named story beats. GSAP ScrollTrigger drives one scrubbed timeline per exhibit; Three.js receives normalized progress and applies camera, group transforms, material exposure, and annotation visibility. Blender/Lux3D assets are prepared as semantic groups so every beat can reveal a meaningful structural detail rather than only rotating one monolithic model.

**Tech Stack:** React, TypeScript, Three.js, GSAP ScrollTrigger, Blender 4.2, Lux3D G1/G1-Turbo, Playwright, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-11-high-fidelity-redesign.md`, `docs/lux3d-hifi-review-2026-10-11.md`, the two supplied sample videos and PDFs.

## Global Constraints

- Preserve the Chinese cultural references and the existing four exhibits and four city chapters.
- Use a single scroll-linked timeline per exhibit; no independent scroll listeners for model, text, or camera.
- Use `scrub` for continuous progress, `pin` for the cinematic stage, `snap` only to named beat labels, and call `ScrollTrigger.refresh()` after dynamic assets/fonts load.
- Keep reduced-motion and WebGL fallback behavior functional for every new beat.
- Keep Lux3D credentials out of source, logs, manifests, and deliverables.
- Every final model must pass Blender import, browser load, interaction, and visual screenshot review.

## Story Design

### Fly英塔: nine beats

1. `establish`: misty distant silhouette, slow dolly-in, title and scale.
2. `surface`: exterior wood/roof/stone material reveal with grazing light.
3. `outer-levels`: seven outer levels illuminate one at a time.
4. `eaves`: camera enters the eaves; dougong, rafters, tiles, and corner details are isolated.
5. `micro-surface`: wood grain, worn lacquer, tile granularity, stone pores, moss and cracks.
6. `outer-disassembly`: roof, railings, dougong, and floors separate in a controlled sequence.
7. `inner-tower`: five-level stone inner pagoda emerges from the opened shell.
8. `section`: semi-transparent cutaway shows vertical alignment and tower-within-tower structure.
9. `reassemble`: parts return, camera pulls back, and the chapter resolves to the opening silhouette.

### Lake brush: five beats

1. silhouette and bamboo tube; 2. hair bundle and binding; 3. close-up fiber/roughness pass; 4. semantic separation of body, hair, base; 5. reassembly with ink-and-paper atmosphere.

### Shuanglin loom: seven beats

1. whole loom; 2. frame and mortise joints; 3. warp tension; 4. heddle/reed/shuttle path; 5. silk fiber and metal wear close-up; 6. exploded weaving cycle; 7. restored working loom.

### Guzhu tea: six beats

1. still-life composition; 2. tray and cup silhouette; 3. glaze/tea liquid/steam lighting; 4. tea buds and fiber detail; 5. layered exploded arrangement; 6. calm reassembly with lake reflection.

### City chapters

Keep the existing photographic references, but give each city scene a three-beat camera treatment: establish, architectural/material detail, and return/transition. Use the same progress contract as exhibit chapters so OJO-like pacing remains consistent across the whole site.

## Implementation Tasks

### Task 1: Story timeline contract

**Files:** Create `src/storyTimeline.ts`, `src/storyTimeline.test.ts`; modify `src/storyChapters.ts`.

- Define `StoryBeat { id, start, end, focus, caption, camera, exposure, groups }` and `ExhibitStory`.
- Store all beat labels and normalized progress ranges in data, not JSX conditionals.
- Add tests asserting monotonic ranges, complete `[0,1]` coverage, unique IDs, and reduced-motion fallback targets.

### Task 2: Semantic GLB hierarchy

**Files:** Create `assets/blender/prepare_hifi_assets.py`, modify `assets/blender/quality_report.py`, `public/asset-index.json`.

- Import each Lux3D GLB, normalize scale/origin, and create named groups for every story beat.
- For the tower require `outer-level-01` through `outer-level-07`, `outer-eaves`, `dougong`, `inner-tower-01` through `inner-tower-05`, `stone-base`, `roof-tiles`, and `railings`.
- For loom, brush, and tea create the groups listed in their story beats.
- Preserve embedded textures and export desktop and mobile GLBs without changing semantic names.
- Extend the quality report with mesh count, material count, texture dimensions, bounding box, and named-group coverage.

### Task 3: Camera and material look-dev

**Files:** Create `src/exhibitLookDev.ts`, `src/exhibitLookDev.test.ts`; modify the Three.js exhibit host.

- Configure ACES tone mapping, sRGB output, environment lighting, soft key/fill/rim lights, contact shadows, and per-material roughness ranges.
- Define camera poses per beat: distance, azimuth, elevation, target, focal length, and exposure.
- Use smooth interpolation between poses and never animate the pinned root itself; animate child groups and camera targets.
- Add a close-up diagnostic mode used only by screenshot QA to verify wood, tile, stone, bamboo, hair, silk, glaze, and tea-liquid reflections.

### Task 4: ScrollStory React component

**Files:** Create `src/ScrollStory.tsx`, `src/ScrollStory.css`; modify `src/ExhibitHost.tsx` and chapter components.

- Pin a full-viewport stage with a tall beat rail.
- Create one GSAP timeline per story, register ScrollTrigger once, use `scrub: 1`, `snap: "labels"`, and `pin: true`.
- On timeline update, call a typed Three.js `applyStoryProgress(progress)` function; update captions and annotations from the active beat.
- Clean up with `gsap.context()` and kill triggers on unmount.
- Support keyboard step navigation and touch/trackpad scrolling without changing the timeline contract.

### Task 5: OJO transition language

**Files:** Modify `src/site.tsx`, `src/CityChapter.tsx`, `src/styles.css`; create `src/transitionTokens.ts`.

- Add full-bleed image/video layers, masked reveals, slow parallax depth planes, chapter numbers, and beat progress markers.
- Use a restrained editorial type scale and one visual action per beat.
- Transition between exhibits through shared progress rather than abrupt route-like jumps.
- Keep the existing source credits visible in the final materials section.

### Task 6: Progressive loading and fallback

**Files:** Modify `src/modelAsset.ts`, `src/ExhibitHost.tsx`, `src/fallbackPoster.ts`.

- Load the first silhouette/LOD immediately, then promote to the high-fidelity GLB before the close-up beat.
- Keep a mobile GLB and poster fallback; never block the page on the highest-resolution asset.
- Preserve graphics-unavailable, asset-error, context-lost, reduced-motion, and retry states.

### Task 7: Verification and visual review

**Files:** Create `scripts/verify-story.mjs`, `src/tests/storyTimeline.test.ts`; update `docs/lux3d-hifi-review-2026-10-11.md`.

- Playwright test every beat at desktop and mobile widths, capture one screenshot per beat, rotate the model, and assert no page errors.
- Test WebGL fallback and reduced-motion with the same beat data.
- Run Blender import and quality reports for all four GLBs.
- Run `pnpm test`, `pnpm build`, and the full story verifier.
- Compare the resulting contact sheet against the two supplied sample videos and PDFs; revise any beat whose camera, texture, or hierarchy is not legible.

## Approval Gate

Do not implement these tasks until the user approves this plan. After approval, execute tasks in order and stop after Task 3 for a first visual checkpoint before completing the full site.
