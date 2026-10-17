import assert from "node:assert/strict";
import { createServer } from "node:http";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { ClaudeForwarder } from "../src/claudeForwarder.ts";
import { credentialHits, credentialVariants, countForwarderRecords, homeReferences, preflightObserved, safeTerminal, scanCredentialFiles } from "../src/claudeLoginFacts.ts";

const output = process.argv[2]; assert(output);
const root = mkdtempSync("/private/tmp/t093-forwarder-"), token = "synthetic-only/" + randomUUID();
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
  assert.equal(credentialHits(ledger, [token]), 0); assert(!ledger.includes("independent fixture prompt"));
  checks.push("each retry and failure journaled before upstream; no header or body persisted");
  assert.deepEqual(homeReferences({ argv: ["cli", "/fixture-real-home/private"] }, "/fixture-real-home"), [{ field: "launch.argv[1]", occurrences: 1 }]);
  checks.push("real HOME launch path injection reported");
  const leak = join(root, "synthetic-leak.txt");
  for (const variant of credentialVariants([token])) {
    writeFileSync(leak, variant); assert(scanCredentialFiles(root, [token]).hits > 0);
  }
  rmSync(leak); assert.equal(scanCredentialFiles(root, [token]).hits, 0);
  checks.push("raw JSON URL base64 credential injections detected; fixture removed");
  writeFileSync(relay.ledger, ledger.split("\n").filter(line => !line.includes('"kind":"request","sequence":2')).join("\n"));
  assert.equal(countForwarderRecords(relay.ledger, 2).counts_match, false);
  checks.push("dropped request row detected against independent upstream and ingress counts");
  for (const variant of credentialVariants([token])) {
    const raw = "start " + variant.slice(0, 5) + "\x1b[31m" + variant.slice(5) + " end\n";
    let published = "";
    for (let n = 0; n <= raw.length; n++) {
      const safe = safeTerminal(raw.slice(0, n), [token]);
      assert(safe.startsWith(published)); assert.equal(credentialHits(safe.replace(/\x1b\[[0-9;]*m/g, ""), [token]), 0);
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
      assert(safe.startsWith(published)); assert.equal(credentialHits(safe, [token]), 0);
      published = safe;
    }
  }
  checks.push("raw public bytes contain no credential in OSC title, OSC8, DCS or CSI across every split");
  writeFileSync(output, JSON.stringify({ status: "PASS", task: "T-093", checks, upstream_requests: observed.length,
    real_upstream_requests: 0, synthetic_credential_files_removed: true }, null, 2) + "\n", { flag: "wx" });
  console.log(JSON.stringify({ status: "PASS", checks: checks.length }));
} finally {
  await relay!?.close(); upstream.closeAllConnections(); await new Promise<void>(resolve => upstream.close(() => resolve()));
  rmSync(root, { recursive: true });
}
