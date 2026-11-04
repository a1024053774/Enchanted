// Review-3 (non-blocking): the pin's install directory exists, is not empty, but has no herdr-core.
// hcBinary must not return a path to a missing file. Usage: node partial_install_probe.mjs <hcDistribution.mjs>
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
const { hcBinary, hcInstallName } = await import(pathToFileURL(process.argv[2]).href);
const root = mkdtempSync('/private/tmp/t244-partial-');
mkdirSync(join(root, 'hc', hcInstallName), { recursive: true });
writeFileSync(join(root, 'hc', hcInstallName, 'LICENSE'), 'left over\n');
let result;
try { const path = await hcBinary(root); result = { returned: path, exists: existsSync(path) }; }
catch (error) { result = { threw: error.code ?? String(error) }; }
rmSync(root, { recursive: true });
console.log(JSON.stringify(result));
