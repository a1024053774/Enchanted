import { execFileSync } from "node:child_process";
import { mergeConfig } from "/Users/luckye/Documents/Code/synara/node_modules/vitest/dist/config.js";
import base from "/Users/luckye/Documents/Code/synara/apps/server/vitest.config.ts";
const fork = "/Users/luckye/Documents/Code/synara";
export default mergeConfig(base, { plugins: [{ name: "t064-stop-before-fix", enforce: "pre", load(id: string) {
  if (id === fork+"/apps/server/src/a2a/tools.ts") return execFileSync("git",["show","7c04fb3fef801bf9f41a0d17f9290e13e173c45a:apps/server/src/a2a/tools.ts"],{cwd:fork,encoding:"utf8"});
} }] });
