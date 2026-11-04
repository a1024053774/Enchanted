import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

// One release pin for development, tests and packaging. Never use a PATH hc.
export const hcRelease = Object.freeze({
  version: '0.1.15',
  url: 'https://releases.herdr.dev/core/0.1.15/herdr-core-macos-aarch64.tar.gz',
  sha256: '47eba8367e0626a1efced8795fcb03d5434b2541c5a84d78c50cc02c8fb49fc8',
});
export const hcFiles = ['herdr-core', 'LICENSE', 'THIRD-PARTY-NOTICES'];

export async function installHc(destination) {
  if (process.platform !== 'darwin' || process.arch !== 'arm64') throw new Error('hc requires macOS arm64');
  const filename = `herdr-core-${hcRelease.version}-macos-aarch64.tar.gz`;
  const cache = process.env.ENCHANTED_HC_CACHE_DIR ?? fileURLToPath(new URL('../../../hc-cache/', import.meta.url));
  const cached = join(cache, filename);
  // Missing cache is the only download case. A corrupt cache is always an error.
  const bytes = existsSync(cached) ? readFileSync(cached) : Buffer.from(await (async () => {
    const response = await fetch(hcRelease.url, { signal: AbortSignal.timeout(60_000) });
    if (!response.ok) throw new Error(`hc download: HTTP ${response.status}`);
    return response.arrayBuffer();
  })());
  if (createHash('sha256').update(bytes).digest('hex') !== hcRelease.sha256) throw new Error('hc archive SHA-256 mismatch');
  const temporary = mkdtempSync(join(tmpdir(), 'enchanted-hc-install-'));
  try {
    const archive = join(temporary, filename);
    writeFileSync(archive, bytes, { mode: 0o600 });
    mkdirSync(destination, { recursive: true, mode: 0o700 });
    execFileSync('/usr/bin/tar', ['-xzf', archive, '-C', destination, ...hcFiles]);
  } finally {
    rmSync(temporary, { recursive: true });
  }
  return join(destination, 'herdr-core');
}

// The development install of this pin under a data directory's hc/ (tests find it by this prefix).
export const hcInstallName = `herdr-core-${hcRelease.version}-${hcRelease.sha256.slice(0, 8)}`;

export async function hcBinary(root) {
  const packaged = fileURLToPath(new URL('../hc/herdr-core', import.meta.url));
  // Packaged resources were verified from the pinned archive and codesigned.
  if (existsSync(packaged)) return packaged;
  // T-244: a core outlives the daemon and starts its holders from the file it was started from; a holder from another
  // file (inode) is refused. So each pin has its own directory, published by one rename and never written again: a
  // running core keeps its file across daemon restarts and pin changes, of two daemons installing on one fresh data
  // directory the later rename fails and uses the first install, and an interrupted extraction is never published.
  // A file damaged afterwards fails at exec (hc is code signed) and stops the daemon start, as a corrupt archive does.
  const parent = join(root, 'hc'), install = join(parent, hcInstallName), binary = join(install, 'herdr-core');
  if (existsSync(binary)) return binary;
  mkdirSync(parent, { recursive: true, mode: 0o700 });
  // An interrupted install leaves this directory unused; it goes with the data directory.
  const staging = mkdtempSync(join(parent, '.install-'));
  try {
    await installHc(staging);
    try { renameSync(staging, install); }
    // Only another daemon's finished install may take the place; an incomplete directory there is an error to see.
    catch (error) { if (!['ENOTEMPTY', 'EEXIST'].includes(error.code) || !existsSync(binary)) throw error; }
  } finally {
    rmSync(staging, { recursive: true, force: true });
  }
  return binary;
}
