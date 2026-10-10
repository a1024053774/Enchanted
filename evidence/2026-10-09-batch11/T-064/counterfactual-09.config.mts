import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { mergeConfig } from "/Users/luckye/Documents/Code/synara/node_modules/vitest/dist/config.js";
import base from "/Users/luckye/Documents/Code/synara/apps/server/vitest.config.ts";
const fork = "/Users/luckye/Documents/Code/synara";
const mode = process.env.T064_COUNTERFACTUAL!;
const native = "apps/server/src/codexAppServerManager.ts";
const domain = "packages/a2a-gates/src/rolePermissions.ts";
export default mergeConfig(base, { plugins: [{ name: "t064-counterfactual", enforce: "pre", load(id: string) {
  if (mode === "parent-native" && id === join(fork,native)) return execFileSync("git",["show","7a3a13249e562bf2d7f9ff4cb024f39b13d62434:"+native],{cwd:fork,encoding:"utf8"});
  if (mode === "missing-input" && id === join(fork,domain)) {
    const source = readFileSync(id,"utf8");
    if (!source.includes("saveInput({")) throw new Error("Mutation no longer matches");
    return source.replace("saveInput({","void ({");
  }
} }] });
