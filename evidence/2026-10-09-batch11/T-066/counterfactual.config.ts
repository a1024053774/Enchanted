import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";
const fork = "/Users/luckye/Documents/Code/synara";
const { mergeConfig } = await import(join(fork,"node_modules/vitest/dist/config.js"));
const base = (await import(join(fork,"apps/server/vitest.config.ts"))).default;
const mode = process.env.T066_MUTANT!;
export default mergeConfig(base, { plugins: [{ name: "t066-counterfactual", enforce: "pre", load(id: string) {
  if (mode === "parent-tools" && id === join(fork,"apps/server/src/a2a/tools.ts")) {
    return execFileSync("git",["show","49cae984f22924de006e0f8358cb447eb881aaf6:apps/server/src/a2a/tools.ts"],{cwd:fork,encoding:"utf8"});
  }
  if (id !== join(fork,"packages/a2a-gates/src/core.ts")) return;
  const source = readFileSync(id,"utf8");
  const substitutions: Record<string, [string,string]> = {
    "ack-without-lock": ['const lock = this.operationLock(`inbox-${original.id}`);','const lock = { close() {} };'],
    "missing-capability": ['requireGate(caller.capabilities?.has("a2a:stop"), "stop_capability_required");','requireGate(true, "stop_capability_required");'],
  };
  const mutation = substitutions[mode];
  if (!mutation) return;
  if (!source.includes(mutation[0])) throw new Error("Mutation target changed");
  return source.replace(mutation[0], mutation[1]);
} }] });
