// Separate discovery probe: actual manager, controlled native I/O. No model.
// T-055 changes only the catalog and must preserve a2a_submit's current policy.
import assert from "node:assert/strict";
import { writeFileSync } from "node:fs";
const { CodexAppServerManager } = await import("/Users/luckye/Documents/Code/synara/apps/server/src/codexAppServerManager.ts");
const results = [];
for (const tool of ["a2a_submit", "a2a_raise"]) {
 const manager: any = new CodexAppServerManager();
 const context: any = {
  session:{provider:"codex",status:"running",threadId:"managed-worker",runtimeMode:"full-access",activeTurnId:"active-turn",resumeCursor:{threadId:"native-worker"},createdAt:"2026-10-09T00:00:00.000Z",updatedAt:"2026-10-09T00:00:00.000Z"},
  account:{type:"unknown",planType:null,sparkEnabled:true},pending:new Map(),pendingApprovals:new Map(),pendingUserInputs:new Map(),collabReceiverTurns:new Map(),collabReceiverParents:new Map(),reviewTurnIds:new Set(),gatewayCredentialRetired:false,nextRequestId:1,stopping:false,enableComputerControl:false,activeInteractionMode:"default",autoApproveSynaraTools:false,gatewaySessionLease:{release(){}}
 };
 let accepted = false;
 manager.emitEvent=()=>{}; manager.updateSession=()=>{}; manager.requireSession=()=>context;
 manager.writeMessage=async()=>{accepted=true;};
 await manager.handleServerRequest(context,{id:19,method:"mcpServer/elicitation/request",params:{threadId:"native-worker",turnId:"active-turn",serverName:"synara",mode:"form",message:`Allow the synara MCP server to run tool "${tool}"?`,requestedSchema:{type:"object",properties:{}},_meta:{codex_approval_kind:"mcp_tool_call",persist:["session"]}}});
 results.push({tool,accepted,pending:context.pendingApprovals.size});
}
writeFileSync(process.argv[2],JSON.stringify({results,source:"controlled protocol frame without tool_name",baselineSourceUnchanged:"codexAppServerManager.ts"},null,2)+"\n");
assert.equal(results[0]!.accepted,results[1]!.accepted,"T-055 must retain the existing submit policy");
assert.equal(results[0]!.accepted,true,"Separate existing parser defect: native generated names containing digits");
