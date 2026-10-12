// Tutorial 5.7 browser checks for the Feiying chapter: load, nav, continuity, reverse scroll,
// explode return, free view, mobile, frame rate. Screenshots go to artifacts/qa-feiying/.
// usage: bun scripts/verify-feiying.mjs [baseUrl]
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { chromium } from 'playwright';

const base = process.argv[2] || 'http://127.0.0.1:5173/';
const out = join(process.cwd(), 'artifacts/qa-feiying');
await mkdir(out, { recursive: true });
const report = [];
const ok = (name, pass, detail = '') => { report.push({ name, pass, detail }); console.log(`${pass ? 'PASS' : 'FAIL'}  ${name}${detail ? ' — ' + detail : ''}`); };

const browser = await chromium.launch({ channel: 'msedge', headless: true, args: ['--enable-gpu', '--ignore-gpu-blocklist', '--use-angle=d3d11'] });
const scrollTo = (page, p) => page.evaluate((p) => {
  const el = document.getElementById('tower');
  const top = el.getBoundingClientRect().top + window.scrollY;
  window.scrollTo(0, top + (el.offsetHeight - innerHeight) * p);
}, p);
const state = (page) => page.evaluate(() => {
  const el = document.getElementById('tower');
  const cam = window.__feiyingDebug?.();
  return { s: Number(el.style.getPropertyValue('--s')), cls: el.className,
    active: [...el.querySelectorAll('.feiying__nav button')].findIndex((b) => b.hasAttribute('aria-current')), cam };
});
const settle = (page, ms = 1400) => page.waitForTimeout(ms);

try {
  for (const viewport of [{ width: 1440, height: 810, tag: 'desktop' }, { width: 390, height: 844, tag: 'mobile' }]) {
    const page = await browser.newPage({ viewport, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(base, { waitUntil: 'domcontentloaded' });
    await scrollTo(page, 0.02);
    const t0 = Date.now();
    await page.waitForFunction(() => document.getElementById('tower')?.classList.contains('feiying--ready'), null, { timeout: 90000 });
    ok(`${viewport.tag}: model loads`, true, `${((Date.now() - t0) / 1000).toFixed(1)}s`);

    const stops = [0.04, 0.2, 0.37, 0.54, 0.7, 0.98];
    const forward = [];
    for (const [i, p] of stops.entries()) {
      await scrollTo(page, p); await settle(page);
      const st = await state(page);
      forward.push(st);
      await page.screenshot({ path: join(out, `${viewport.tag}-0${i + 1}.png`) });
      ok(`${viewport.tag}: screen ${i + 1} active`, st.active === i, `s=${st.s.toFixed(2)} nav=${st.active}`);
    }
    // Reverse: same progress must reproduce the same state (tutorial 5.5.2).
    for (const [i, p] of [...stops.entries()].reverse()) {
      await scrollTo(page, p); await settle(page);
      const st = await state(page);
      const same = Boolean(st.cam) && Math.abs(st.s - forward[i].s) < 1e-3 && JSON.stringify(st.cam) === JSON.stringify(forward[i].cam);
      ok(`${viewport.tag}: reverse to screen ${i + 1} matches forward`, same);
    }
    // Fast scrubbing then return to the start: parts back at their origin.
    for (let k = 0; k < 12; k += 1) { await scrollTo(page, Math.random()); await page.waitForTimeout(60); }
    await scrollTo(page, 0.02); await settle(page, 2200);
    const home = await page.evaluate(() => window.__feiyingDebug?.());
    ok(`${viewport.tag}: parts return to origin after fast scrubbing`, typeof home?.maxOffset === 'number' && home.maxOffset < 1e-4, `max offset ${home?.maxOffset}`);

    // Nav click lands on the matching screen.
    if (viewport.tag === 'desktop') {
      await page.locator('.feiying__nav button').nth(3).click(); await settle(page, 2500);
      ok('desktop: nav click → 斗栱', (await state(page)).active === 3);
      // Free view: orbit drag changes the camera, Escape restores scroll pose.
      await scrollTo(page, 0.04); await settle(page);
      await page.locator('.feiying__free').click(); await settle(page, 600);
      const before = await page.evaluate(() => window.__feiyingDebug?.().camera);
      await page.mouse.move(720, 420); await page.mouse.down(); await page.mouse.move(900, 400, { steps: 8 }); await page.mouse.up();
      await settle(page, 800);
      const after = await page.evaluate(() => window.__feiyingDebug?.().camera);
      ok('desktop: free view drag rotates the camera', JSON.stringify(before) !== JSON.stringify(after));
      await page.screenshot({ path: join(out, 'desktop-free.png') });
      await page.keyboard.press('Escape'); await settle(page);
      ok('desktop: Escape leaves free view', !(await state(page)).cls.includes('feiying--free'));
      // Frame rate while scrolling through the chapter.
      const fps = await page.evaluate(async () => {
        const el = document.getElementById('tower'); const top = el.getBoundingClientRect().top + scrollY; const travel = el.offsetHeight - innerHeight;
        let frames = 0; const t = performance.now();
        await new Promise((done) => { const step = () => { frames += 1; const k = (performance.now() - t) / 3000; scrollTo(0, top + travel * Math.min(1, k)); k < 1 ? requestAnimationFrame(step) : done(); }; requestAnimationFrame(step); });
        return frames / 3;
      });
      ok('desktop: scroll frame rate', fps > 40, `${fps.toFixed(0)} fps (headless Edge)`);
    } else {
      const overlap = await page.evaluate(() => {
        const copy = document.querySelector('.feiying__copy[data-screen="1"] h2')?.getBoundingClientRect();
        return copy ? copy.top > innerHeight * 0.45 : false;
      });
      ok('mobile: copy sits in the lower half, below the model', overlap);
    }
    ok(`${viewport.tag}: no page errors`, errors.length === 0, errors.slice(0, 3).join(' | '));
    await page.close();
  }
} finally {
  await browser.close();
  await writeFile(join(out, 'report.json'), JSON.stringify(report, null, 1));
}
const failed = report.filter((r) => !r.pass);
console.log(`\n${report.length - failed.length}/${report.length} checks passed`);
process.exit(failed.length ? 1 : 0);
