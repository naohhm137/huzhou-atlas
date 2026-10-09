# Huzhou City Chapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the approved four-object Huzhou atlas with four real-location chapters and fix the brush caption overlap, keeping all work local for user acceptance.

**Architecture:** Keep `site.tsx` as the story conductor and add focused city data/scene components. A single existing ScrollTrigger computes normalized progress for both object scenes and new photographic scenes. CSS handles composition; React owns discrete view switches and the accessible Nanxun comparison control.

**Tech Stack:** Vite, React 19, TypeScript, GSAP ScrollTrigger, CSS, Vitest, existing Three.js exhibits.

**Spec:** `docs/superpowers/specs/2026-10-01-city-chapters-design.md`

## Global Constraints

- Preserve existing four GLBs, exhibition controls, and opening film behavior.
- All new real photos have individual Commons source and license credits.
- Native reversible scrolling, no Lenis, reduced-motion readable fallback.
- Local preview only; no GitHub or public deployment.
- This directory is not a Git repository, so commit steps do not apply.

---

### Task 1: Photo assets and story map

**Files:**
- Create: `src/cityScenes.ts`
- Create: `src/tests/cityScenes.test.tsx`
- Add: `public/media/city-*.jpg`
- Modify: `REFERENCE_RESEARCH.md`

**Interfaces:**
- Produces `CITY_SCENES`, an ordered array of four typed chapters with `id`, `title`, `place`, `body`, `primaryImage`, `secondaryImage`, `sourceLabel`, `motion`.
- IDs are `yishang`, `dongwu`, `longemont`, `nanxun-city`.

- [ ] Step 1: Write a failing test rendering the later `App` story, checking four section IDs and working source links; separately check the data's four unique IDs and image paths.
- [ ] Step 2: Run `pnpm test` and confirm the new assertions fail before implementation.
- [ ] Step 3: Copy seven researched Commons thumbnails to `public/media/city-*.jpg` without touching old assets; record author, license, image URL and exact visual role in `REFERENCE_RESEARCH.md`.
- [ ] Step 4: Implement `CITY_SCENES` with conservative claims and separate scene image roles.
- [ ] Step 5: Run tests until the new data checks pass; the App-render checks remain red until Task 2.

### Task 2: Four photographic place chapters and controls

**Files:**
- Create: `src/CityChapter.tsx`
- Create: `src/cityInteraction.ts`
- Create: `src/tests/cityInteraction.test.ts`
- Modify: `src/site.tsx`
- Modify: `src/storyTiming.ts`
- Modify: `src/style.css`

**Interfaces:**
- `CityChapter` accepts `scene`, `progress`, and `reducedMotion`; it renders place-specific visual variants.
- `cityInteraction.ts` exports a pure `adjustCompare(value, key)` helper; ArrowLeft/Right alter by 5 points, Home/End choose 0/100, unknown keys do not alter value.
- Story section IDs expand to four city IDs while old time ranges stay fixed; city sections hold the ending video frame.

- [ ] Step 1: Write failing tests for compare keyboard boundaries, city IDs/anchors in static `App` markup, and old story media-time invariance.
- [ ] Step 2: Run `pnpm test`; confirm each new contract fails for the expected missing behavior.
- [ ] Step 3: Add four different compositions: perspective street/bridge switch, twin-tower aperture, Longemont circus iris, Nanxun photo comparison. Each has semantic headings, controls, image alt text and local credits.
- [ ] Step 4: Extend the one scroll measurement array and pass progress to city scenes. Keep media time fixed for the new chapters; do not create a second scroll controller or block wheel scrolling.
- [ ] Step 5: Implement place-specific scroll-linked CSS properties and reduced-motion static states. Update navigation to include destinations without horizontal overflow.
- [ ] Step 6: Run all tests and build; fix only failures caused by the new implementation.

### Task 3: Overlap repair and visual verification

**Files:**
- Modify: `src/style.css`
- Modify: `src/site.tsx`
- Modify: `README.md`, `PRODUCT.md`, `DESIGN.md`
- Modify: `src/tests/chapterExpanded.test.tsx` if a regression assertion is warranted.

**Interfaces:**
- At widths 601–900px, exhibit photo caption never occupies the text block; the photo remains credited in the footer.
- New chapter navigation has a compact mobile route selector or equivalent accessible layout.

- [ ] Step 1: Reproduce the 601–900px caption overlap in the browser and measure the subtitle/caption rectangles.
- [ ] Step 2: Move/hide that redundant in-frame credit in the affected breakpoint and verify no intersection at 768px; retain source attribution.
- [ ] Step 3: Test 1440, 1024, 768, 390 and 360px; inspect each new scene plus the four original objects, opened stage, forward/reverse scroll, navigation, keyboard comparison and reduced motion.
- [ ] Step 4: Make one consolidated visual correction pass, recapture failed viewports, run `pnpm test` and `pnpm build`, inspect console and all local image responses.
- [ ] Step 5: Run `impeccable detect` once on changed UI targets, resolve any material findings, and document implemented behavior and source credits.
- [ ] Step 6: Keep the local preview reachable on `127.0.0.1:4173`, provide screenshots and ask the user to accept before any public release.

## Self-review

The plan covers four named places, differentiated interactions, source integrity, caption overlap, responsive/reduced-motion behavior and local-only delivery. No model rebuild is included because the brief explicitly preserves the approved four objects. No public release is included because the user reserved GitHub publication for a later acceptance step.
