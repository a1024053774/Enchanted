// T-126 review 01 (P2): a daemon start that fails after making the terminal socket's directory leaves nothing in the
// system temporary directory. Nothing in the data directory names that directory, so no later start could remove it.
// Real daemon entry; each case fails at a named step, checked from the error, so a start failing earlier proves nothing.
// Usage: node --experimental-strip-types tests/test_t126_failed_start_cleanup.ts OUTPUT.json [SRC_DIR]
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [output, source = resolve(import.meta.dirname, "../src")] = process.argv.slice(2);
const result: Record<string, unknown> = { status: "INCOMPLETE", source, cases: {} };
try {
  const { createOperatorCredential } = await import(pathToFileURL(join(resolve(source), "credentials.ts")).href);
  // A stale PID record: both sockets listen, then the exclusive PID write fails.
  // A temporary directory with a long path: the directory is made, then the socket path is too long to bind.
  // (An occupied control socket is refused before the directory is made, so it is not a case here.)
  const cases: Record<string, [(state: string) => void, string, string]> = {
    pid_write_fails: [(state) => writeFileSync(join(state, "daemon.pid"), "999999\n"), "EEXIST", "tmp"],
    socket_path_too_long: [() => undefined, "terminal socket path exceeds 103 bytes", "t".repeat(70)],
  };
  for (const [name, [prepare, expected, folder]] of Object.entries(cases)) {
    const root = mkdtempSync("/private/tmp/t126-start-"), state = join(root, "state"), temporary = join(root, folder);
    mkdirSync(state, { mode: 0o700 }); mkdirSync(temporary);
    process.env.A2A_OPERATOR_CREDENTIAL = join(root, "operator.json");
    createOperatorCredential(state);
    prepare(state);
    const run = spawnSync(process.execPath, [join(resolve(source), "daemon.ts"), state, "{}"], { encoding: "utf8", timeout: 30000,
      env: { ...process.env, TMPDIR: temporary + "/" } });
    const left = readdirSync(temporary).filter((entry) => entry.startsWith("enchanted-"));
    rmSync(root, { recursive: true, force: true }); // holds an operator credential; the result above is the record
    (result.cases as Record<string, unknown>)[name] = { exit: run.status, failed_at: expected, error_seen: run.stderr.includes(expected), left };
    assert.notEqual(run.status, 0, `${name}: the start must fail`);
    assert.ok(run.stderr.includes(expected), `${name}: failed somewhere other than ${expected}: ${run.stderr.slice(-400)}`);
    assert.deepEqual(left, [], `${name}: terminal socket directory left behind`);
  }
  result.status = "PASS";
} catch (error) {
  result.error = String(error);
}
writeFileSync(output, JSON.stringify(result, null, 2) + "\n");
process.exitCode = result.status === "PASS" ? 0 : 1;
