// Browser check for the six whole-model exhibits: each loads, renders, and opens a close-up.
// usage: bun scripts/verify-items.mjs [baseUrl] [width] [height]
import { chromium } from 'playwright';
const base = process.argv[2] || 'http://127.0.0.1:5173/';
const viewport = { width: Number(process.argv[3] || 1440), height: Number(process.argv[4] || 810) };
const tag = viewport.width < 720 ? 'mobile' : 'desktop';
const b = await chromium.launch({ channel: 'msedge', headless: true, args: ['--enable-gpu', '--ignore-gpu-blocklist'] });
const page = await b.newPage({ viewport });
const errors = []; page.on('pageerror', (e) => errors.push(String(e))); page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
await page.goto(base, { waitUntil: 'domcontentloaded' });
let fails = 0;
for (const id of ['brush', 'silk', 'tea', 'yishang', 'dongwu', 'nanxun-city']) {
  await page.evaluate((id) => { const el = document.getElementById(id); scrollTo(0, el.getBoundingClientRect().top + scrollY + (el.offsetHeight - innerHeight) * 0.35); }, id);
  try { await page.waitForFunction((id) => document.querySelector(`#${id} .exhibit-host`)?.classList.contains('is-ready'), id, { timeout: 60000 }); }
  catch { console.log('FAIL', id, 'did not load'); fails++; continue; }
  await page.waitForTimeout(900);
  await page.screenshot({ path: `artifacts/qa-items/${tag}-${id}.png` });
  await page.locator(`#${id} .text-button`).click(); await page.waitForTimeout(1300);
  await page.screenshot({ path: `artifacts/qa-items/${tag}-${id}-close.png` });
  await page.keyboard.press('Escape'); await page.waitForTimeout(400);
  console.log('PASS', id);
}
console.log(errors.length ? `FAIL page errors: ${errors.slice(0, 3).join(' | ')}` : 'PASS no page errors');
await b.close(); process.exit(fails || errors.length ? 1 : 0);
