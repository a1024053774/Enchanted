import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";

const fork = process.argv[2]!;
const output = process.argv[3]!;
const { CodexAppServerManager } = await import(`${fork}/apps/server/src/codexAppServerManager.ts`);
const inputs = JSON.parse(readFileSync(new URL("./catalog-inputs.json", import.meta.url), "utf8"));
const results = [];
for (const tool of inputs.names as string[]) {
  const row: Record<string, unknown> = { tool };
  for (const explicit of [true, false]) {
    const manager: any = new CodexAppServerManager();
    const context: any = {
      session: {
        provider: "codex", status: "running", threadId: "managed-worker",
        runtimeMode: "full-access", activeTurnId: "active-turn",
        resumeCursor: { threadId: "native-worker" },
        createdAt: "2026-10-09T00:00:00.000Z", updatedAt: "2026-10-09T00:00:00.000Z",
      },
      account: { type: "unknown", planType: null, sparkEnabled: true },
      pending: new Map(), pendingApprovals: new Map(), pendingUserInputs: new Map(),
      collabReceiverTurns: new Map(), collabReceiverParents: new Map(), reviewTurnIds: new Set(),
      gatewayCredentialRetired: false, nextRequestId: 1, stopping: false,
      enableComputerControl: false, activeInteractionMode: "default", autoApproveSynaraTools: false,
      gatewaySessionLease: { release() {} },
    };
    let response: unknown;
    manager.emitEvent = () => {};
    manager.updateSession = () => {};
    manager.requireSession = () => context;
    manager.writeMessage = async (_context: unknown, message: unknown) => { response = message; };
    await manager.handleServerRequest(context, {
      id: 19, method: "mcpServer/elicitation/request",
      params: {
        threadId: "native-worker", turnId: "active-turn", serverName: "synara", mode: "form",
        message: `Allow the synara MCP server to run tool "${tool}"?`,
        requestedSchema: { type: "object", properties: {} },
        _meta: {
          codex_approval_kind: "mcp_tool_call", persist: ["session"],
          ...(explicit ? { tool_name: tool } : {}),
        },
      },
    });
    row[explicit ? "explicit" : "native_message"] = {
      response: response ?? null, pending: context.pendingApprovals.size,
    };
  }
  results.push(row);
}
writeFileSync(output, JSON.stringify({ inputSource: inputs.source_revision, results }, null, 2) + "\n", { flag: "wx" });
// The catalog supplies the inputs. The existing contract independently says
// a live, authorized gateway call accepts once, without persistent metadata.
for (const row of results) {
  assert.deepEqual(row.explicit, {
    response: { id: 19, result: { action: "accept", content: null, _meta: null } }, pending: 0,
  });
}
console.log(JSON.stringify({ tools: results.length, promptingWithoutName: results.filter((row: any) => row.native_message.pending === 1).map((row) => row.tool) }));
