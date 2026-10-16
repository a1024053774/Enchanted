// Real filesystem/process probe. Expectations are the ready-file contract,
// not the publisher's implementation: no partial final path, exact payload,
// and no replacement of an earlier publication.
import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { randomUUID } from "node:crypto";

const [sourceArg, outputArg] = process.argv.slice(2);
if (!sourceArg || !outputArg || process.argv.length !== 4) throw new Error("Expected source and output paths.");
const source = resolve(sourceArg), output = resolve(outputArg);
mkdirSync(output, { recursive: true });
if (existsSync(join(output, "run.json"))) throw new Error("Probe output already exists.");
const fixture = mkdtempSync("/private/tmp/t090-ready-");
const env = Object.fromEntries(Object.entries(process.env).filter(([key]) =>
  !key.startsWith("A2A_") && !key.startsWith("GIT_") && key !== "NODE_OPTIONS"));
const payload = { pid: 17, root: "/independent/fixture", nonce: randomUUID(), values: [1, "完整 JSON"] };
const report: any = { status: "INCOMPLETE", artifact_root: fixture, source, payload, checks: [], children: [] };
const childCode = `
import fs from "node:fs";
import { syncBuiltinESMExports } from "node:module";
import { pathToFileURL } from "node:url";
const [module, path, value, pause] = process.argv.slice(1);
if (pause === "pause") {
  const original = fs.writeFileSync;
  fs.writeFileSync = (target, data, options) => {
    const fd = fs.openSync(target, options.flag);
    fs.writeSync(1, JSON.stringify({stage:"opened", target}) + "\\n");
    if (fs.readSync(0, Buffer.alloc(1), 0, 1, null) !== 1) throw new Error("Missing observer release");
    try { original(fd, data); } finally { fs.closeSync(fd); }
  };
  syncBuiltinESMExports();
}
const { publishReady } = await import(pathToFileURL(module).href);
try { publishReady(path, JSON.parse(value)); }
catch (error) { console.error(error.code ?? String(error)); process.exitCode = 1; }
`;
function argv(module: string, path: string, pause = "run") {
  return ["--input-type=module", "-e", childCode, module, path, JSON.stringify(payload), pause];
}
function check(id: string, passed: boolean, actual: unknown) {
  report.checks.push({ id, passed, actual });
  if (!passed) throw new Error(id);
}
async function visibility(module: string, name: string) {
  const ready = join(fixture, name + ".json"), args = argv(module, ready, "pause");
  const record: any = { argv: [process.execPath, ...args], stdout: "", stderr: "", ready };
  report.children.push(record);
  const child = spawn(process.execPath, args, { env, stdio: ["pipe", "pipe", "pipe"] });
  record.pid = child.pid;
  child.stdout.on("data", (data) => {
    record.stdout += data.toString();
    if (!record.observed && record.stdout.includes("\n")) {
      record.observed = JSON.parse(record.stdout.split("\n")[0]);
      // The writer is blocked after opening its actual target and before
      // writing any content. This observation is outside the writer process.
      record.visible_before_content = existsSync(ready);
      child.stdin.end("\n");
    }
  });
  child.stderr.on("data", (data) => { record.stderr += data.toString(); });
  record.exit = await new Promise((done, reject) => { child.once("error", reject); child.once("close", done); });
  if (record.exit !== 0 || !record.observed) throw new Error("Probe process failed: " + JSON.stringify(record));
  record.final = JSON.parse(readFileSync(ready, "utf8"));
  record.payload_equal = JSON.stringify(record.final) === JSON.stringify(payload);
  record.outcome = !record.visible_before_content && record.payload_equal ? "passed" : "contract_failure";
  return record;
}
try {
  const bad = join(fixture, "direct-write.mjs");
  writeFileSync(bad, 'import {writeFileSync} from "node:fs";\nexport function publishReady(path,value) { writeFileSync(path, JSON.stringify(value)+"\\n", {flag:"wx"}); }\n', { flag: "wx" });
  const old = await visibility(bad, "known-bad");
  check("READY-KNOWN-BAD-REJECTED", old.outcome === "contract_failure" && old.visible_before_content && old.payload_equal, old);
  const module = join(source, "workbench/tests/ready_file.ts");
  const fixed = await visibility(module, "candidate");
  check("READY-NO-PARTIAL-PUBLICATION", fixed.outcome === "passed", fixed);
  check("READY-PENDING-REMOVED", !existsSync(fixed.ready + ".pending"), fixed.ready);
  const ready = join(fixture, "existing.json"), sentinel = '{"owner":"earlier-publication"}\n';
  writeFileSync(ready, sentinel, { flag: "wx" });
  const args = argv(module, ready), conflict = spawnSync(process.execPath, args, { env, encoding: "utf8" });
  report.children.push({ argv: [process.execPath, ...args], exit: conflict.status, stdout: conflict.stdout, stderr: conflict.stderr });
  check("READY-EXISTING-PRESERVED", conflict.status === 1 && conflict.stderr.trim() === "EEXIST"
    && readFileSync(ready, "utf8") === sentinel && existsSync(ready + ".pending"), { exit: conflict.status, stderr: conflict.stderr });
  const blocked = join(fixture, "blocked.json");
  mkdirSync(blocked + ".pending");
  const blockedArgs = argv(module, blocked), failure = spawnSync(process.execPath, blockedArgs, { env, encoding: "utf8" });
  report.children.push({ argv: [process.execPath, ...blockedArgs], exit: failure.status, stdout: failure.stdout, stderr: failure.stderr });
  check("READY-CREATE-FAILURE-PRESERVED", failure.status === 1 && failure.stderr.trim() === "EEXIST"
    && !existsSync(blocked) && existsSync(blocked + ".pending"), { exit: failure.status, stderr: failure.stderr });
  report.status = "PASS";
} catch (error) { report.error = String(error); process.exitCode = 1; }
writeFileSync(join(output, "run.json"), JSON.stringify(report, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify({ status: report.status, artifact_root: fixture, checks: report.checks.map((c: any) => ({ id: c.id, passed: c.passed })) }));
