import { createRequire } from 'node:module';
import { mkdir, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const require = createRequire(pathToFileURL(join(process.env.HUZHOU_RUNTIME_MODULES || process.cwd(), 'package.json')));
const { chromium } = require('playwright');
const root = resolve(process.argv[2] || process.cwd());
const out = join(root, 'artifacts/qa-2026-10-08');
await mkdir(out, { recursive: true });
const report = [];
const browser = await chromium.launch({ channel: 'msedge', headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const base = process.env.HUZHOU_PREVIEW_URL || 'http://127.0.0.1:4173/';

async function chapter(page, id) {
  await page.locator(`#${id}`).evaluate((el) => window.scrollTo(0, el.offsetTop + (el.offsetHeight - window.innerHeight) * 0.3));
  await page.locator(`#${id} .exhibit-host`).waitFor({ state: 'visible' });
}

try {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport, reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.goto(base, { waitUntil: 'domcontentloaded' });
    for (const id of ['brush', 'silk', 'tea', 'tower', 'yishang', 'dongwu', 'longemont', 'nanxun-city']) {
      await chapter(page, id);
      const host = page.locator(`#${id} .exhibit-host`);
      await host.locator('canvas').waitFor();
      await page.waitForFunction(id => document.querySelector(`#${id} .exhibit-host`)?.classList.contains('is-ready'), id, { timeout: 45000 });
      assert.equal(await host.getAttribute('data-failure'), null, `${id} initialized`);
      if (['yishang', 'dongwu', 'nanxun-city'].includes(id)) await page.screenshot({ path: join(out, `${viewport.width}-${id}-assembled.png`) });
      await page.locator(`#${id} .text-button`).click();
      assert.equal(await page.locator(`#${id}`).evaluate(el => /(?:chapter|city)--expanded/.test(el.className)), true);
      await page.screenshot({ path: join(out, `${viewport.width}-${id}-expanded.png`) });
      const canvas = host.locator('canvas');
      const rect = await canvas.boundingBox();
      const before = await canvas.screenshot();
      await page.mouse.move(rect.x + rect.width * 0.45, rect.y + rect.height * 0.52);
      await page.mouse.down();
      await page.mouse.move(rect.x + rect.width * 0.65, rect.y + rect.height * 0.45, { steps: 12 });
      await page.mouse.up();
      const after = await canvas.screenshot();
      assert.notEqual(Buffer.compare(before, after), 0, `${id} renders drag rotation`);
      await page.locator(`#${id} .stage-close`).click();
      assert.equal(await page.locator(`#${id}`).evaluate(el => /(?:chapter|city)--expanded/.test(el.className)), false);
      report.push({ mode: 'WebGL', width: viewport.width, id, ready: true, rotate: true, splitAndClose: true });
    }
    assert.deepEqual(errors, []);
    await page.close();
  }

  // Reproduce the in-app browser's unavailable graphics context, at our boundary.
  const fallback = await browser.newPage({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
  await fallback.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(kind, ...args) {
      if (['webgl', 'webgl2', 'experimental-webgl'].includes(kind)) return null;
      return original.call(this, kind, ...args);
    };
  });
  await fallback.goto(base, { waitUntil: 'domcontentloaded' });
  for (const width of [1440, 390]) {
    await fallback.setViewportSize({ width, height: width === 390 ? 844 : 900 });
    for (const id of ['brush', 'silk', 'tea', 'tower', 'yishang', 'dongwu', 'longemont', 'nanxun-city']) {
      await chapter(fallback, id);
      await fallback.locator(`#${id} .exhibit-host[data-failure="graphics"]`).waitFor();
      const poster = fallback.locator(`#${id} .exhibit-poster`);
      await fallback.waitForFunction(id => {
        const img = document.querySelector(`#${id} .exhibit-poster`);
        return img?.complete && img.naturalWidth > 0;
      }, id);
      await fallback.locator(`#${id} .text-button`).click();
      assert.match(await poster.getAttribute('src'), /-expanded\.webp$/);
      await fallback.waitForFunction(id => document.querySelector(`#${id} .exhibit-poster`)?.complete, id);
      await fallback.screenshot({ path: join(out, `${width}-${id}-fallback.png`) });
      await fallback.locator(`#${id} .stage-close`).click();
      assert.doesNotMatch(await poster.getAttribute('src'), /-expanded\.webp$/);
      report.push({ mode: 'graphics-unavailable', width, id, imageLoaded: true, splitAndClose: true });
    }
  }
  await fallback.close();

  const recovery = await browser.newPage({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
  await recovery.route('**/models/tea.glb', route => route.fulfill({ status: 404, body: 'missing' }));
  await recovery.goto(base, { waitUntil: 'domcontentloaded' });
  await chapter(recovery, 'tea');
  await recovery.locator('#tea .exhibit-host[data-failure="asset"]').waitFor();
  await recovery.locator('#tea .text-button').click();
  await recovery.unroute('**/models/tea.glb');
  await recovery.locator('#tea .exhibit-status button').click();
  await recovery.waitForFunction(() => document.querySelector('#tea .exhibit-host')?.classList.contains('is-ready'), { timeout: 45000 });
  assert.equal(await recovery.locator('#tea .exhibit-host').getAttribute('data-failure'), null);
  assert.equal(await recovery.locator('#tea').evaluate(el => el.classList.contains('chapter--expanded')), true);
  // The expanded state must also reach the replacement scene, not just its UI.
  await recovery.screenshot({ path: join(out, 'tea-recovered-expanded.png') });
  await recovery.locator('#tea canvas').evaluate(canvas => canvas.getContext('webgl2').getExtension('WEBGL_lose_context').loseContext());
  await recovery.locator('#tea .exhibit-host[data-failure="context-lost"]').waitFor();
  assert.match(await recovery.locator('#tea .exhibit-poster').getAttribute('src'), /-expanded\.webp$/);
  report.push({ mode: 'recovery', assetFailureDistinguished: true, retryLoaded: true, expandedPreserved: true, contextLossFallback: true });
  await recovery.close();
  await writeFile(join(out, 'display-report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ checks: report.length, report: join(out, 'display-report.json') }));
} finally {
  await browser.close();
}
