import { transformWithOxc } from '/Users/luckye/Documents/Code/a2a/workbench/node_modules/vite/dist/node/index.js';
import { readFileSync } from 'node:fs';
const src = readFileSync('/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx','utf8');
const r = await transformWithOxc(src, 'renderer.tsx', { lang: 'tsx' });
console.log('ok', r.code.length, (r.warnings||[]).length);
