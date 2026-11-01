import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
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

export async function hcBinary(root) {
  const packaged = fileURLToPath(new URL('../hc/herdr-core', import.meta.url));
  // Packaged resources were verified from the pinned archive and codesigned.
  if (existsSync(packaged)) return packaged;
  return installHc(join(root, 'hc', 'bin'));
}
