// usage: bun img.js <promptFile> <outPng> <size> <ref1> [ref2 ...]
const fs = require('fs'), path = require('path');
const [promptFile, out, size, ...refs] = process.argv.slice(2);
const token = fs.readFileSync(process.env.HOME_TOKEN, 'utf8').trim();
const prompt = fs.readFileSync(promptFile, 'utf8');
const fd = new FormData();
fd.append('model', process.env.IMG_MODEL || 'gpt-image-2');
fd.append('prompt', prompt);
fd.append('size', size);
fd.append('quality', 'high');
fd.append('n', '1');
for (const r of refs) {
  const buf = fs.readFileSync(r);
  const type = r.endsWith('.png') ? 'image/png' : 'image/jpeg';
  fd.append('image[]', new Blob([buf], { type }), path.basename(r));
}
const t0 = Date.now();
const res = await fetch('https://ailindo.com/v1/images/edits', { method: 'POST', headers: { Authorization: 'Bearer ' + token }, body: fd });
const txt = await res.text();
let j; try { j = JSON.parse(txt); } catch { console.error('HTTP', res.status, txt.slice(0, 800)); process.exit(1); }
if (!res.ok || !j.data) { console.error('HTTP', res.status, JSON.stringify(j).slice(0, 800)); process.exit(1); }
const d = j.data[0];
let bin;
if (d.b64_json) bin = Buffer.from(d.b64_json, 'base64');
else { const r2 = await fetch(d.url); bin = Buffer.from(await r2.arrayBuffer()); }
fs.writeFileSync(out, bin);
console.log('OK', out, bin.length, 'bytes', ((Date.now() - t0) / 1000).toFixed(0) + 's', d.revised_prompt ? 'revised' : '');
