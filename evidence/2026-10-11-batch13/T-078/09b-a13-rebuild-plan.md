# A-13 protocol rebuild after A-12 I1 settle contract

A-12 ideation I1 used one root and twelve Messages: the first tool_use reached Claude and the queued `inbox send` tool_result was retried because the fake API required a stop entry before the later Stop hook/relay could create one. A-12 is over the 4 roots/6 Messages budget; do not retry or reuse its root.

The product contract is asynchronous: `workbench/bin/inbox send` returns `{ok:true, queued:true, delivered:false, request_id, path}` in the controller's request directory. The later Claude Stop hook reads that request, relay validates the bound caller, `gates.inbox_send` creates the actual stop entry, and delivery/wake is then independently observed. The API must settle the queued receipt first; the oracle must subsequently require the actual stop entry, relay receipt and executor wake. It must never synthesize an entry id in tool_result or treat queued=true as delivered.

Offline end-to-end evidence is `09b-a12-i1-materials-01/i1-e2e-queued-green.json` with red mutants for missing queue receipt, mismatched request/path and foreign target. A-13 needs a fresh materials packet/root, B1 session and onboarding before any real I1.
