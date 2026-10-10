import { join } from "node:path";
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
const fork = "/Users/luckye/Documents/Code/synara";
const sdkPath = join(fork, "apps/server/node_modules/@anthropic-ai/claude-agent-sdk");
const { query, createSdkMcpServer } = await import(join(sdkPath, "sdk.mjs"));
const sdkVersion = JSON.parse(readFileSync(join(sdkPath, "package.json"), "utf8")).version;
const root = process.env.T064_PROBE_ROOT!;
let finish: (() => void) | undefined;
const pending = new Promise<void>((resolve) => { finish = resolve; });
let sentMessages = 0;
async function* input() {
  await pending;
  // Never yield a user message: this tests the CLI control protocol only.
  sentMessages += 0;
}
const session = query({
  prompt: input(),
  options: {
    pathToClaudeCodeExecutable: "/Users/luckye/.local/bin/claude",
    cwd: root,
    env: {
      HOME: join(root, "os-home"),
      CLAUDE_CONFIG_DIR: join(root, "claude-empty"),
      PATH: process.env.PATH,
      DISABLE_AUTOUPDATER: "1",
      CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1",
    },
    settingSources: [],
    persistSession: false,
    permissionMode: "bypassPermissions",
    allowDangerouslySkipPermissions: true,
    tools: [],
    mcpServers: { synara: createSdkMcpServer({ name: "synara", tools: [] }) },
  },
});
const timer = setTimeout(() => { session.close(); }, 20000);
try {
  const tightened = await session.setMcpPermissionModeOverride("synara", "default");
  const cleared = await session.setMcpPermissionModeOverride("synara", null);
  assert.equal(sentMessages, 0);
  console.log(JSON.stringify({ sdk_version: sdkVersion, tightened, cleared, user_messages: sentMessages,
    model_turns: 0, actual_cli_control_responses: true }));
} finally {
  clearTimeout(timer);
  finish!();
  session.close();
}
