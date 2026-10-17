from pathlib import Path
import re

pattern=re.compile(r'^<<<<<<< HEAD\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]+\n',re.M|re.S)
def resolve(name, expected, choose):
    p=Path(name);source=p.read_text(encoding='utf-8');blocks=list(pattern.finditer(source));assert len(blocks)==expected,(name,len(blocks))
    index=iter(range(expected))
    result=pattern.sub(lambda m:choose(next(index),m.group(1),m.group(2)),source)
    assert not re.search(r'^(<<<<<<<|=======|>>>>>>>)',result,re.M)
    p.write_text(result,encoding='utf-8')

resolve('workbench/src/gates/core.ts',1,lambda i,head,incoming:head+incoming)
resolve('workbench/src/daemon.ts',2,lambda i,head,incoming:head+'    }\n'+incoming if i==0 else incoming)
p=Path('workbench/src/daemon.ts');s=p.read_text(encoding='utf-8')
s=s.replace('return { source: `worker:${pane.record.thread}`, kind: "launch" };',
            'return { source: pane.record.role === "worker" ? `worker:${pane.record.thread}` : pane.record.role, kind: "launch" };')
p.write_text(s,encoding='utf-8')

def panes(i,head,incoming):
    if i==0:return incoming.replace('turn: null, active: null','turn: null, nativeEnded: false, active: null')
    # Keep main's feedback/session-facts methods and T-078's single input stream.
    methods=head[:head.index('  async dispatch(')]
    methods=methods.replace('{ kind: "quality-repair", rejection_id: repair.id });','undefined, { kind: "quality-repair", rejection_id: repair.id });')
    incoming=incoming.replace('inbox?: { id: string; sender: string }) {','inbox?: { id: string; sender: string }, context?: { kind: string; rejection_id: string }) {')
    incoming=incoming.replace('this.store.register(pane.record.id, text, source, inbox);','this.store.register(pane.record.id, text, source, context, inbox);')
    return methods+incoming
resolve('workbench/src/panes.ts',2,panes)

def relay(i,head,incoming):
    worker=incoming[incoming.index('      const allowed:'):]
    worker=worker.replace('      const allowed: Record<string, string[]> = {','        : {',1)
    return ('      const allowed: Record<string, string[]> = binding.role === "reviewer"\n'
            '        ? { review_submit: ["review_id", "candidate_commit", "verdict", "findings"] }\n'+worker)
resolve('workbench/src/relay.ts',1,relay)

def store(i,head,incoming):
    incoming=incoming.replace('inbox?: { id: string; sender: string }): DispatchItem {','context?: { kind: string; rejection_id: string }, inbox?: { id: string; sender: string }): DispatchItem {')
    incoming=incoming.replace('JSON.stringify({ text, registered_at, source,','JSON.stringify({ text, registered_at, source, ...(context ? { context } : {}),')
    incoming=incoming.replace('registered_at,\n      ...(inbox','registered_at, ...(context ? { context } : {}),\n      ...(inbox')
    return incoming
resolve('workbench/src/store.ts',1,store)
p=Path('workbench/src/store.ts');s=p.read_text(encoding='utf-8').replace('  inbox_entry?: string; sender?: string };','  inbox_entry?: string; sender?: string; context?: { kind: string; rejection_id: string } };');p.write_text(s,encoding='utf-8')

def host(i,head,incoming):
    if i==0:return 'import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";\n'
    return 'mkdirSync(state, { recursive: true, mode: 0o700 });\ncreateOperatorCredential(state);\n'+head
resolve('workbench/tests/daemon_acceptance_host.ts',2,host)
print('PASS: resolved six files by retaining both sides; no Git mutation')
