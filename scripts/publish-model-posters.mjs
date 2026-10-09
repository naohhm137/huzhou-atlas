import { createRequire } from 'node:module';
import { mkdir, readdir } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';

// Use the supplied workspace runtime, or a locally installed sharp.
const modules = process.env.HUZHOU_RUNTIME_MODULES || process.cwd();
const require = createRequire(pathToFileURL(join(modules, 'package.json')));
const sharp = require('sharp');
const root = resolve(process.argv[2] || process.cwd());
const source = join(root, 'assets/blender/previews');
const target = join(root, 'public/media/models');
await mkdir(target, { recursive: true });
for (const name of await readdir(source)) {
  if (!name.endsWith('.png') || name.includes('-detail') || name.includes('-reference')) continue;
  await sharp(join(source, name)).webp({ quality: 93, alphaQuality: 100, effort: 6 })
    .toFile(join(target, name.replace(/\.png$/, '.webp')));
}
console.log('Published Blender model posters.');
