import { readFileSync, realpathSync } from "node:fs";
import { join } from "node:path";
import { countForwarderRecords } from "./claudeLoginFacts.ts";

// A read-only fact command. Its exit code reports parsing/I/O only; facts do
// not grant or reject permission to run a model turn.
const preflight = process.argv[2] === "--preflight";
if (process.argv.length !== (preflight ? 4 : 3)) throw new Error("usage: claudeLoginCheck.ts [--preflight] AUDIT_DIRECTORY");
const directory = realpathSync(process.argv[preflight ? 3 : 2]);
const saved = JSON.parse(readFileSync(join(directory, preflight ? "preflight.json" : "facts.json"), "utf8"));
if (saved.schema !== 2 || saved.ledger !== "forwarder/journal/requests.jsonl") throw new Error("unsupported_login_facts_schema");
const counts = countForwarderRecords(join(directory, saved.ledger), saved.forwarder.received);
console.log(JSON.stringify({ ...saved, counts,
  check: { read_at: new Date().toISOString(), credential_scan_is_historical: true,
    saved_ingress_is_historical: true,
    notice: "This command recounts current journal bytes. Saved ingress and credential scans are historical. No model permission is granted." } }, null, 2));
