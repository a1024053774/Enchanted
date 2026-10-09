import { makeAgentGatewaySessionRegistry } from "/Users/luckye/Documents/Code/synara/apps/server/src/agentGateway/Layers/AgentGatewaySessionRegistry.ts";
import { filterToolsByCapability } from "/Users/luckye/Documents/Code/synara/apps/server/src/agentGateway/toolRuntime.ts";
import { a2aSubmitTool, a2aRaiseTool, a2aDispositionTool } from "/Users/luckye/Documents/Code/synara/apps/server/src/a2a/tools.ts";

// This probe constructs real definitions and credentials. It calls no handler,
// starts no provider, and prints no bearer or session identity.
const registry = makeAgentGatewaySessionRegistry();
const issued = registry.issue("t058-preflight-worker" as never, "codex", {
  additionalCapabilities: [],
});
const tools = [a2aSubmitTool(null as never), a2aRaiseTool(null as never), a2aDispositionTool(null as never)];
const visible = filterToolsByCapability(tools, issued.capabilities)
  .map((tool) => tool.definition.name).sort();
const expected = ["a2a_raise", "a2a_submit"];
console.log(JSON.stringify({
  requirement: "T-058 / spec section 1: worker can use only a2a_submit and a2a_raise",
  scope: "Existing a2a definitions only; this is a preflight probe, not full tools/list acceptance",
  capabilities: [...issued.capabilities].sort(),
  expected, observed: visible,
  match: JSON.stringify(visible) === JSON.stringify(expected),
}, null, 2));
registry.revoke(issued.token);
if (JSON.stringify(visible) !== JSON.stringify(expected)) process.exitCode = 1;
