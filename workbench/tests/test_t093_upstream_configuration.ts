// URL configuration only. No server, DNS, vendor CLI, auth or network.
import assert from "node:assert/strict";
import { writeFileSync } from "node:fs";
import { upstreamUrl } from "../src/claudeForwarder.ts";

const checks: { input: string; pass: boolean; failure?: string }[] = [];
for (const value of ["https://configured-one.invalid:9443/", "https://configured-two.invalid:8443/", "http://127.0.0.1:52123/"]) {
  try { assert.equal(upstreamUrl(value).href, value, "The configured upstream address must be preserved."); checks.push({ input: value, pass: true }); }
  catch (error: any) { checks.push({ input: value, pass: false, failure: error.code ?? error.message }); }
}
for (const value of ["http://unconfigured.invalid:80/", "https://rejected-user:rejected-password@configured.invalid/",
  "https://configured.invalid/path", "https://configured.invalid/?q=1", "https://configured.invalid/#fragment", "https://configured.invalid:0/"]) {
  try { assert.throws(() => upstreamUrl(value)); checks.push({ input: value, pass: true }); }
  catch { checks.push({ input: value, pass: false, failure: "The invalid address was accepted." }); }
}
const result = { status: checks.every(x => x.pass) ? "PASS" : "INCOMPLETE", scope: "URL parsing only. No network or service.", checks };
writeFileSync(process.argv[2], JSON.stringify(result, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify({ status: result.status, failed: checks.filter(x => !x.pass).map(x => x.failure) }));
process.exitCode = result.status === "PASS" ? 0 : 2;
