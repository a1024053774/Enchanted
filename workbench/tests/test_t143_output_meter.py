"""Check the actual e2e meter's completion boundary, never report synthetic performance.
Failure modes: buffer-only content completes without a render event; hidden output
completes; pending/rejected input completes; valid rendered output never completes.
"""
import argparse
import ast
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--summary', type=Path, required=True)
a = p.parse_args()
assert not a.summary.exists(), 'Use a new evidence path'
source = Path('workbench/tests/test_t139_t143_views_perf_e2e.py').read_text(encoding='utf-8')
expressions = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.JoinedStr)
               and any(isinstance(v, ast.Constant) and isinstance(v.value, str) and 'const subscription=t.onRender' in v.value for v in n.values)]
assert len(expressions) == 1, 'Use the actual e2e meter expression'
values = {'mount': 'document.querySelector(".terminal-mount")', 'json': json,
          'shell_key': 'fixture-key', 'command': 'fixture command\r'}
expression = ''.join(v.value if isinstance(v, ast.Constant) else str(eval(compile(ast.Expression(v.value), '<meter>', 'eval'), {}, values)) for v in expressions[0].values)
script = r'''
import vm from 'node:vm';
import assert from 'node:assert/strict';
const expression = EXPRESSION;
const checks=[];
async function setup() {
  let queue=[],render,now=0,admit,rejectInput,visible=true,marker=false,result='pending',disposed=false;
  const input=new Promise((yes,no)=>{admit=yes;rejectInput=no});
  const line={translateToString:()=>marker?'BENCH_04999':'unrelated'};
  const term={buffer:{active:{viewportY:0,getLine:()=>line}},onRender:callback=>{render=callback;return {dispose(){disposed=true}}}};
  const node={__testTerminal:term,getClientRects:()=>visible?[{}]:[],closest:()=>({dataset:{restoring:'false'}})};
  const context={document:{querySelector:()=>node},getComputedStyle:()=>({visibility:visible?'visible':'hidden'}),
    performance:{now:()=>now},requestAnimationFrame:callback=>queue.push(callback),window:{a2a:{input:()=>input}}};
  vm.runInNewContext(expression,context).then(()=>{result='resolved'},()=>{result='rejected'});
  const flush=()=>new Promise(resolve=>setImmediate(resolve));
  async function step(frames=1){for(let i=0;i<frames;i++){now+=16;const work=queue;queue=[];work.forEach(f=>f(now));await flush()}}
  return {step,flush,admit,rejectInput,render:()=>render({start:0,end:0}),
    setVisible:v=>{visible=v},setMarker:v=>{marker=v},state:()=>result,disposed:()=>disposed};
}
const x=await setup();x.admit();await x.flush();x.setMarker(true);await x.step(3);
assert.equal(x.state(),'pending');checks.push('buffer_without_render_event_does_not_complete');
x.setVisible(false);x.render();await x.step(3);
assert.equal(x.state(),'pending');checks.push('rendered_but_hidden_does_not_complete');
x.setVisible(true);await x.step();assert.equal(x.state(),'pending');
await x.step();assert.equal(x.state(),'pending');checks.push('completion_waits_for_paint_frames');
await x.step();assert.equal(x.state(),'resolved');assert(x.disposed());checks.push('visible_render_after_input_completes_and_disposes_listener');
const y=await setup();y.setMarker(true);y.render();await y.step(3);
assert.equal(y.state(),'pending');checks.push('pending_input_does_not_complete');
y.rejectInput(new Error('fixture rejection'));await y.flush();
assert.equal(y.state(),'rejected');assert(y.disposed());checks.push('rejected_input_rejects_and_disposes_listener');
const z=await setup();z.admit();await z.flush();z.render();await z.step(3);
assert.equal(z.state(),'pending');checks.push('unrelated_render_event_does_not_complete');
process.stdout.write(JSON.stringify({checks}));
'''.replace('EXPRESSION', json.dumps(expression))
r = subprocess.run(['node', '--input-type=module'], input=script, capture_output=True, text=True)
report = {'status': 'PASS' if r.returncode == 0 else 'NO_GO', 'scope': 'Actual e2e expression with supplied DOM/xterm/input/rAF boundaries; no Electron or performance claim', 'exit_code': r.returncode}
if r.returncode == 0:
    report.update(json.loads(r.stdout))
else:
    report['error'] = r.stderr
# Parse the same expression in Node without executing any simulated sampling.
syntax = subprocess.run(['node', '--check', '--input-type=module'], input='('+expression+');', capture_output=True, text=True)
report['js_syntax_exit'] = syntax.returncode
if syntax.returncode:
    report.update(status='NO_GO', syntax_error=syntax.stderr)
a.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
