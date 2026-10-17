import { readFileSync, realpathSync } from "node:fs";
import { join } from "node:path";
import { countForwarderRecords } from "./claudeLoginFacts.ts";

// A read-only fact command. Its exit code reports parsing/I/O only; facts do
// not grant or reject permission to run a model turn.
const directory = realpathSync(process.argv[2]);
const saved = JSON.parse(readFileSync(join(directory, "facts.json"), "utf8"));
const counts = countForwarderRecords(join(directory, "requests.jsonl"), saved.forwarder.received);
console.log(JSON.stringify({ ...saved, counts,
  check: { read_at: new Date().toISOString(), credential_scan_is_historical: true,
    notice: "Credential scan was performed in memory at session finalization. This command does not read auth." } }, null, 2));
