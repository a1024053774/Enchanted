// T-126 desktop credential location and migration, files only (no Electron, no daemon). Expected layouts follow the
// ticket: the credential is a 0600 file outside the data directory; after migration no old credential file remains.
// Usage: node --experimental-strip-types tests/test_t126_desktop_credentials.ts OUTPUT.json [MODULE_TS]
import assert from "node:assert/strict";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [output, module = resolve(import.meta.dirname, "../src/desktopCredentials.ts")] = process.argv.slice(2);
const checks: string[] = [];
const result: Record<string, unknown> = { status: "INCOMPLETE", module, checks };
const mode = (path: string) => statSync(path).mode & 0o777;
const uuid = (n: number) => `0000000${n}-0000-4000-8000-000000000000`;

function oldInstall() {
  // The layout desktop.mjs wrote before T-126: the descriptor and every start's credential in the data directory.
  const root = mkdtempSync("/tmp/t126-credentials-"), state = join(root, "state");
  mkdirSync(state, { mode: 0o700 });
  const current = join(state, `desktop-operator-${uuid(1)}.json`);
  writeFileSync(current, '{"kind":"operator","token":"current"}\n', { mode: 0o600 });
  writeFileSync(join(state, `desktop-operator-${uuid(2)}.json`), '{"kind":"operator","token":"earlier start"}\n', { mode: 0o600 });
  writeFileSync(join(state, "desktop-connection.json"), JSON.stringify({ credential: current }) + "\n", { mode: 0o600 });
  writeFileSync(join(state, "state.sqlite3"), "");
  return { root, state, current };
}
const leftovers = (state: string) => readdirSync(state).filter(name => name.startsWith("desktop-"));
function check(name: string, run: () => void) { run(); checks.push(name); }

try {
  const credentials = await import(pathToFileURL(resolve(module)).href);
  check("directory_outside_data_directory", () => {
    const state = "/Users/x/Library/Application Support/a2a-orchestrator-test";
    const isolated = credentials.desktopCredentialDirectory(state, true, "Enchanted Test");
    assert.ok(!isolated.startsWith(state + "/") && isolated !== state, isolated);
    const product = credentials.desktopCredentialDirectory(state, false, "Enchanted Test");
    assert.ok(product.endsWith("/Library/Application Support/Enchanted Test") && !product.startsWith(state + "/"), product);
    assert.notEqual(credentials.desktopCredentialDirectory(state, false, "Enchanted"), product);
  });

  const install = oldInstall(), directory = join(install.root, "credentials");
  credentials.migrateDesktopCredential(install.state, directory);
  const moved = credentials.desktopConnection(directory);
  result.moved = moved;
  check("current_credential_moved_private", () => {
    assert.ok(moved && moved.startsWith(directory + "/"), moved);
    assert.equal(readFileSync(moved, "utf8"), '{"kind":"operator","token":"current"}\n');
    assert.equal(mode(moved), 0o600);
    assert.equal(mode(directory), 0o700);
    assert.equal(mode(join(directory, "desktop-connection.json")), 0o600);
  });
  check("no_old_credential_left", () => assert.deepEqual(leftovers(install.state), []));
  check("data_directory_otherwise_untouched", () => assert.ok(existsSync(join(install.state, "state.sqlite3"))));
  credentials.migrateDesktopCredential(install.state, directory);
  check("repeat_changes_nothing", () => { assert.equal(credentials.desktopConnection(directory), moved); assert.equal(readdirSync(directory).length, 2); });

  // A start that wrote the new descriptor and stopped before removing the old files.
  const interrupted = oldInstall(), target = join(interrupted.root, "credentials");
  const already = credentials.newDesktopCredential(target);
  writeFileSync(already, '{"kind":"operator","token":"moved"}\n', { mode: 0o600 });
  credentials.saveDesktopConnection(target, already);
  credentials.migrateDesktopCredential(interrupted.state, target);
  check("interrupted_migration_finished", () => {
    assert.deepEqual(leftovers(interrupted.state), []);
    assert.equal(credentials.desktopConnection(target), already);
  });

  check("descriptor_outside_directory_refused", () => {
    const elsewhere = join(install.root, "elsewhere");
    mkdirSync(elsewhere);
    writeFileSync(join(elsewhere, "desktop-connection.json"), JSON.stringify({ credential: join(install.state, `desktop-operator-${uuid(3)}.json`) }));
    assert.throws(() => credentials.desktopConnection(elsewhere), /Invalid desktop connection descriptor/);
  });
  check("invalid_old_descriptor_kept", () => {
    const bad = oldInstall();
    writeFileSync(join(bad.state, "desktop-connection.json"), JSON.stringify({ credential: "/tmp/desktop-operator-x.json" }));
    assert.throws(() => credentials.migrateDesktopCredential(bad.state, join(bad.root, "credentials")));
    assert.deepEqual(leftovers(bad.state).sort(), ["desktop-connection.json", `desktop-operator-${uuid(1)}.json`, `desktop-operator-${uuid(2)}.json`]);
  });
  check("fresh_install_has_no_connection", () => {
    const root = mkdtempSync("/tmp/t126-credentials-"), state = join(root, "state");
    mkdirSync(state);
    credentials.migrateDesktopCredential(state, join(root, "credentials"));
    assert.equal(credentials.desktopConnection(join(root, "credentials")), undefined);
  });
  result.status = "PASS";
} catch (error) {
  result.error = String(error);
}
writeFileSync(output, JSON.stringify(result, null, 2) + "\n");
process.exitCode = result.status === "PASS" ? 0 : 1;
