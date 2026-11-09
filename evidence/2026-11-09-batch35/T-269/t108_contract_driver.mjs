// T-269 regression: the T-108 contract files only export functions (test_t108_questions.mjs calls them), so running a
// file alone executes nothing. This driver calls one exported function and writes each case's outcome.
// Usage: Enchanted (ELECTRON_RUN_AS_NODE=1) t108_contract_driver.mjs <module path> <export name> <new summary.json>
import { writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const [modulePath, exportName, out] = process.argv.slice(2);
const cases = await (await import(pathToFileURL(resolve(modulePath)).href))[exportName]();
const failed = cases.filter(item => item.status !== 'PASS').map(item => item.name);
// No case run is not a pass: the summary says how many ran.
const status = cases.length > 0 && failed.length === 0 ? 'PASS' : 'FAIL';
writeFileSync(out, JSON.stringify({ status, module: modulePath, export: exportName, cases: cases.length, failed }, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ status, cases: cases.length, failed: failed.length }));
