import { mkdirSync, writeFileSync, copyFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ options: { slot: { type: 'string', default: 'local' } } });
if (!/^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(values.slot)) throw new Error('Invalid build slot');
const slot = join(tmpdir(), 'a2a-build-' + values.slot);
mkdirSync(slot); // Existing slots are preserved. A new build needs a new name.
const cacheDir = join(slot, 'vite-cache');
const temporary = join(slot, 'tmp');
const out = join(slot, 'dist');
mkdirSync(temporary); mkdirSync(out);
process.env.TMPDIR = temporary;
process.env.TMP = temporary;
process.env.TEMP = temporary;
const appRoot = dirname(fileURLToPath(import.meta.url));
const { build } = await import('vite');
const { default: react } = await import('@vitejs/plugin-react');
const common = { configFile: false, root: appRoot, cacheDir, publicDir: false, logLevel: 'warn' };
await build({ ...common, base: './', plugins: [react()], build: {
  outDir: join(out, 'renderer'), emptyOutDir: false, target: 'chrome142',
} });
for (const [entry, format, fileName] of [['main.ts', 'es', 'main.mjs'], ['preload.ts', 'cjs', 'preload.cjs']]) {
  await build({ ...common, build: {
    outDir: out, emptyOutDir: false, target: 'node22', minify: false,
    lib: { entry: join(appRoot, entry), formats: [format], fileName: () => fileName },
    rolldownOptions: { external: (id) => id === 'electron' || id.startsWith('node:') },
  } });
}
copyFileSync(join(appRoot, '../LICENSE.synara'), join(out, 'LICENSE.synara'));
const manifest = { schema: 1, out, main: join(out, 'main.mjs'), preload: join(out, 'preload.cjs'),
  renderer: join(out, 'renderer/index.html'), cacheDir, temporary, source: appRoot };
writeFileSync(join(out, 'build.json'), JSON.stringify(manifest, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify(manifest) + '\n');
