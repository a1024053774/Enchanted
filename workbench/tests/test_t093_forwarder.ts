import assert from "node:assert/strict";
import { createServer } from "node:http";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { spawnSync } from "node:child_process";
import { ClaudeForwarder } from "../src/claudeForwarder.ts";
import { countForwarderRecords, homeReferences, preflightObserved, safeTerminal, scanCredentialFiles } from "../src/claudeLoginFacts.ts";

const output = process.argv[2]; assert(output);
const retained = process.argv[3];
if (retained) assert.equal(existsSync(retained), false, "preserve earlier records");
const root = mkdtempSync("/private/tmp/t093-forwarder-"), token = 'synthetic-only/"\\' + randomUUID();
// Acceptance inputs come from standard encodings, independently of the
// production enumerator and scanner. Quotes/backslash distinguish JSON.
const fixtureVariants = [
  { name: "raw", value: token },
  { name: "json", value: JSON.stringify(token).slice(1, -1) },
  { name: "url", value: encodeURIComponent(token).replace(/[!'()*]/g, c => "%" + c.charCodeAt(0).toString(16).toUpperCase()) },
  { name: "base64", value: Buffer.from(token).toString("base64") },
  { name: "base64_unpadded", value: Buffer.from(token).toString("base64").replace(/=+$/, "") },
  { name: "base64url", value: Buffer.from(token).toString("base64url") },
];
const assertCredentialFree = (text: string) => {
  for (const fixture of fixtureVariants) assert(!text.includes(fixture.value), "public bytes must not contain the independent credential fixture");
};
const observed: number[] = [], checks: string[] = [];
let relay: ClaudeForwarder;
const upstream = createServer((req, res) => {
  const rows = readFileSync(relay.ledger, "utf8").split("\n").filter(Boolean).map(JSON.parse);
  const sequence = observed.length + 1;
  assert(rows.some(row => row.kind === "request" && row.sequence === sequence), "durable record must precede upstream receipt");
  assert.equal(req.headers.authorization, "Bearer " + token);
  let body = ""; req.on("data", data => body += data); req.on("end", () => {
    assert.deepEqual(JSON.parse(body), { messages: [{ role: "user", content: "independent fixture prompt" }] });
    observed.push(sequence); res.writeHead(sequence === 1 ? 400 : 200).end("{}");
  });
});
await new Promise<void>(resolve => upstream.listen(0, "127.0.0.1", resolve));
try {
  assert(fixtureVariants.length > 0, "credential injection cases must not be empty");
  relay = await ClaudeForwarder.start({ directory: join(root, "ledger"), upstream_url: `http://127.0.0.1:${(upstream.address() as any).port}`,
    access_token: token, secrets: [token] });
  for (const expected of [400, 200]) {
    const response = await fetch(relay.url + "/v1/messages", { method: "POST", headers: { authorization: "Bearer " + token },
      body: JSON.stringify({ messages: [{ role: "user", content: "independent fixture prompt" }] }) });
    assert.equal(response.status, expected); await response.text();
  }
  await relay.close();
  assert.deepEqual(observed, [1, 2]); assert.equal(relay.counters.received, 2);
  assert.deepEqual(countForwarderRecords(relay.ledger, 2), { received_requests: 2, ledger_requests: 2, model_requests: 2, counts_match: true, outcomes: 2 });
  const ledger = readFileSync(relay.ledger, "utf8");
  assertCredentialFree(ledger); assert(!ledger.includes("independent fixture prompt"));
  checks.push("each retry and failure journaled before upstream; no header or body persisted");
  const injectedHome = homeReferences({ argv: ["cli", "/fixture-real-home/private"] }, "/fixture-real-home");
  assert.deepEqual(injectedHome, [{ field: "launch.argv[1]", occurrences: 1 }]);
  checks.push("real HOME launch path injection reported");
  const leak = join(root, "synthetic-leak.txt");
  const injections: { variant: string; hits: number }[] = [];
  for (const fixture of fixtureVariants) {
    writeFileSync(leak, fixture.value);
    assert(existsSync(leak), "credential injection file must exist");
    assert(readFileSync(leak, "utf8") === fixture.value, "credential injection must write the independent fixture");
    const hits = scanCredentialFiles(root, [token]).hits;
    assert(hits > 0, "credential injection must be detected");
    injections.push({ variant: fixture.name, hits });
  }
  assert(injections.length > 0, "credential injection must execute at least one case");
  assert.equal(injections.length, fixtureVariants.length, "credential injection must execute every case");
  rmSync(leak); assert.equal(scanCredentialFiles(root, [token]).hits, 0);
  checks.push("raw JSON URL base64 credential injections detected; fixture removed");
  writeFileSync(relay.ledger, ledger.split("\n").filter(line => !line.includes('"kind":"request","sequence":2')).join("\n"));
  const missing = countForwarderRecords(relay.ledger, 2);
  assert.equal(missing.counts_match, false);
  checks.push("dropped request row detected against independent upstream and ingress counts");
  for (const { value: variant } of fixtureVariants) {
    const raw = "start " + variant.slice(0, 5) + "\x1b[31m" + variant.slice(5) + " end\n";
    let published = "";
    for (let n = 0; n <= raw.length; n++) {
      const safe = safeTerminal(raw.slice(0, n), [token]);
      assert(safe.startsWith(published)); assertCredentialFree(safe.replace(/\x1b\[[0-9;]*m/g, ""));
      published = safe;
    }
    assert(published.includes("<CREDENTIAL>"));
  }
  assert(preflightObserved("Unable to connect to Anthropic services\nFailed to connect to api.anthropic.com: ENOTFOUND"));
  assert.equal(preflightObserved("ordinary terminal output"), false);
  checks.push("split ANSI credentials withheld and redacted; bypass preflight classified");
  for (const control of ["\x1b]0;" + token + "\x07", "\x1b]8;;https://local/" + token + "\x1b\\link\x1b]8;;\x1b\\", "\x1bP" + token + "\x1b\\", "\x1b[" + token]) {
    const raw = "before " + control + " after\n";
    let published = "";
    for (let n = 0; n <= raw.length; n++) {
      const safe = safeTerminal(raw.slice(0, n), [token]);
      assert(safe.startsWith(published)); assertCredentialFree(safe);
      published = safe;
    }
  }
  checks.push("raw public bytes contain no credential in OSC title, OSC8, DCS or CSI across every split");
  let retainedScan: { hits: number; files: number } | null = null, gitIndexHits: number | null = null;
  if (retained) {
    mkdirSync(retained, { mode: 0o700 });
    mkdirSync(join(retained, "missing-row"), { mode: 0o700 });
    const facts = { schema: 1, task: "T-093", scope: "independent forwarding run; not product-chain-03", forwarder: relay.counters,
      upstream_requests: observed.length, credential_scan: { hits: 0, scope: "retained metadata records; synthetic token" } };
    writeFileSync(join(retained, "requests.jsonl"), ledger, { flag: "wx", mode: 0o600 });
    writeFileSync(join(retained, "facts.json"), JSON.stringify(facts, null, 2) + "\n", { flag: "wx", mode: 0o600 });
    writeFileSync(join(retained, "missing-row/requests.jsonl"), readFileSync(relay.ledger), { flag: "wx", mode: 0o600 });
    writeFileSync(join(retained, "missing-row/facts.json"), JSON.stringify(facts, null, 2) + "\n", { flag: "wx", mode: 0o600 });
    retainedScan = scanCredentialFiles(retained, [token]); assert.equal(retainedScan.hits, 0);
    const scan = spawnSync("git", ["grep", "--cached", "--quiet", "-F", "-f", "-", "--"],
      { input: fixtureVariants.map(fixture => fixture.value).join("\n") + "\n", encoding: "utf8" });
    assert.equal(scan.status, 1, "synthetic credential must not occur in the current Git index"); gitIndexHits = 0;
  }
  const report = { status: "PASS", task: "T-093", checks, upstream_requests: observed.length, retained_records: retained ?? null,
    counterexamples: { home_references: injectedHome, credential_injections: injections, missing_record: missing },
    evidence_credential_scan: retainedScan, git_index_synthetic_credential_hits: gitIndexHits,
    real_upstream_requests: 0, synthetic_credential_files_removed: true };
  assertCredentialFree(JSON.stringify(report));
  writeFileSync(output, JSON.stringify(report, null, 2) + "\n", { flag: "wx" });
  console.log(JSON.stringify({ status: "PASS", checks: checks.length }));
} finally {
  await relay!?.close(); upstream.closeAllConnections(); await new Promise<void>(resolve => upstream.close(() => resolve()));
  rmSync(root, { recursive: true });
}
