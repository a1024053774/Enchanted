import { randomUUID } from "node:crypto";
import { chmodSync, existsSync, mkdirSync, readFileSync, readdirSync, renameSync, unlinkSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

// Where the desktop app keeps its operator credential (T-126, user's choice A in T-125): a 0600 file outside the
// daemon's data directory, which project terminals are never told about. The release and test apps each use the
// Application Support folder named after the product; an explicitly given data directory has its own sibling folder.
export function desktopCredentialDirectory(state: string, explicitState: boolean, product: string): string {
  return explicitState ? `${state}-credentials` : join(homedir(), "Library/Application Support", product);
}

const descriptor = "desktop-connection.json";
const credentialName = /^desktop-operator-[0-9a-f-]{36}\.json$/;

// The credential the last daemon start issued, if its descriptor is here. A descriptor naming any other file is refused.
export function desktopConnection(directory: string): string | undefined {
  const path = join(directory, descriptor);
  if (!existsSync(path)) return undefined;
  const { credential } = JSON.parse(readFileSync(path, "utf8"));
  if (typeof credential !== "string" || dirname(credential) !== directory || !credentialName.test(credential.slice(directory.length + 1)))
    throw new Error("Invalid desktop connection descriptor");
  return credential;
}

export function newDesktopCredential(directory: string): string {
  mkdirSync(directory, { recursive: true, mode: 0o700 });
  chmodSync(directory, 0o700);
  return join(directory, `desktop-operator-${randomUUID()}.json`);
}

export function saveDesktopConnection(directory: string, credential: string) {
  const pending = join(directory, `desktop-connection-${randomUUID()}.json`);
  writeFileSync(pending, JSON.stringify({ credential }) + "\n", { flag: "wx", mode: 0o600 });
  renameSync(pending, join(directory, descriptor));
}

// An install from before T-126 kept the descriptor and credentials in the data directory. The current credential
// moves here (the daemon may still be running with it), then every old credential file and the old descriptor are
// removed. Each step is safe to repeat, so a start interrupted part way finishes on the next one.
export function migrateDesktopCredential(state: string, directory: string) {
  const old = join(state, descriptor);
  if (existsSync(old) && !existsSync(join(directory, descriptor))) {
    const current = desktopConnection(state)!;
    const moved = newDesktopCredential(directory);
    writeFileSync(moved, readFileSync(current), { flag: "wx", mode: 0o600 });
    saveDesktopConnection(directory, moved);
  }
  for (const name of readdirSync(state)) if (credentialName.test(name)) unlinkSync(join(state, name));
  if (existsSync(old)) unlinkSync(old);
}
