import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { runInNewContext } from "node:vm";

const fork = "/Users/luckye/Documents/Code/synara";
const out = dirname(import.meta.filename);
const label = process.argv[2] ?? "origin-probe-02";
assert(/^[A-Za-z0-9_-]+$/.test(label), "Invalid evidence label");
const ts = await import(join(fork, "apps/server/node_modules/typescript/lib/typescript.js"));
const { Schema } = await import(join(fork, "apps/server/node_modules/effect/dist/index.js"));
const { ClientOrchestrationCommand } = await import(join(fork, "packages/contracts/src/orchestration.ts"));
const thread = "00000000-0000-4000-8000-000000000056";
const command = "00000000-0000-4000-8000-000000000002";
const time = "2026-10-09T13:20:00.000Z";
class ProbeDate extends Date {
  constructor() { super(time); }
}

// Execute the actual object expressions passed to dispatchCommand in the UI.
// Fix only UUID/time to show an identical legal RPC input can come from either
// origin. In a real run these differ randomly, without identifying the origin.
function observe(path: string, type: string) {
  const source = readFileSync(join(fork, path), "utf8");
  const ast = ts.createSourceFile(path, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const matches: any[] = [];
  function visit(node: any) {
    if (matches.length === 0 && ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression) &&
        node.expression.name.text === "dispatchCommand" && node.arguments.length === 1) {
      const expression = node.arguments[0];
      if (ts.isObjectLiteralExpression(expression) && expression.properties.some((property: any) =>
          ts.isPropertyAssignment(property) && property.name.getText(ast) === "type" &&
          ts.isStringLiteral(property.initializer) && property.initializer.text === type)) {
        const text = expression.getText(ast);
        const code = ts.transpileModule(`const value = (${text});`, {
          compilerOptions: { target: ts.ScriptTarget.ES2022 },
        }).outputText;
        const captured = runInNewContext(code + "\nvalue", {
          newCommandId: () => command,
          Date: ProbeDate,
          ThreadId: { makeUnsafe: (id: string) => id },
          threadId: thread,
          activeThread: { id: thread },
          temporaryThreadId: thread,
        });
        matches.push({ path, line: ast.getLineAndCharacterOfPosition(expression.getStart(ast)).line + 1,
          expression: text, rpc: Schema.decodeUnknownSync(ClientOrchestrationCommand)(JSON.parse(JSON.stringify(captured))) });
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(ast);
  assert(matches.length > 0, `Missing source constructor: ${path} ${type}`);
  return matches[0];
}
const explicitInterrupt = observe("apps/web/src/components/ChatView.tsx", "thread.turn.interrupt");
const derivedInterrupt = observe("apps/web/src/components/RunningChatsQuitCoordinator.tsx", "thread.turn.interrupt");
const explicitStop = observe("apps/web/src/components/ChatView.tsx", "thread.session.stop");
const derivedStop = observe("apps/web/src/hooks/useTemporaryThreadLifecycle.ts", "thread.session.stop");
const pairs = [
  { name: "interrupt", explicit: explicitInterrupt, derived: derivedInterrupt },
  { name: "stop", explicit: explicitStop, derived: derivedStop },
].map((pair) => ({ ...pair, identicalRPC: JSON.stringify(pair.explicit.rpc) === JSON.stringify(pair.derived.rpc) }));
writeFileSync(join(out, `${label}.json`), JSON.stringify({
  purpose: "Can the existing dispatchCommand contract distinguish explicit UI input from UI-derived commands?",
  controlled: ["UUID", "timestamp", "same target thread"], pairs,
  result: pairs.every((pair) => pair.identicalRPC) ? "BLOCKED: indistinguishable RPC inputs" : "INCOMPLETE",
  limitations: "Source constructors and actual contract codec executed; not a browser interaction or real user input. No content classifier or new command field.",
}, null, 2) + "\n", { flag: "wx" });
console.log(JSON.stringify(pairs.map((pair) => ({ name: pair.name, identicalRPC: pair.identicalRPC }))));
assert(pairs.every((pair) => !pair.identicalRPC), "Existing RPC fields do not distinguish explicit and UI-derived origins");
