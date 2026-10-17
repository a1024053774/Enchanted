#!/usr/bin/env python3
"""Execute the unchanged bridge assertion and preload at the starting revision.

Pure check only: git show + Node VM, no Electron, daemon, PTY, ps, keys or model.
This isolates the existing assertion; it is not the full real-window suite.
"""
import ast
import json
from pathlib import Path
import subprocess
import sys

revision = '44bbb7828459d81fab0d46069a19d3dd515a7732'
output = Path(sys.argv[1])
preload = subprocess.check_output(['git', 'show', revision + ':workbench/app/preload.ts'], text=True)
test = subprocess.check_output(['git', 'show', revision + ':workbench/tests/test_electron_e2e.py'], text=True)
assertions = [node for node in ast.walk(ast.parse(test)) if isinstance(node, ast.Assert)
              and "value['bridge']" in ast.get_source_segment(test, node)]
assert len(assertions) == 1
assertion = ast.get_source_segment(test, assertions[0])
js = """
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
let bridge;
const context = vm.createContext({Object});
const module = new vm.SourceTextModule(stripTypeScriptTypes(process.argv[1], {mode:'strip'}), {context});
await module.link(() => new vm.SyntheticModule(['contextBridge','ipcRenderer'], function() {
  this.setExport('contextBridge', {exposeInMainWorld(name, value) {bridge = value;}});
  this.setExport('ipcRenderer', {invoke() {throw new Error('No IPC allowed in this pure check');}});
}, {context}));
await module.evaluate();
process.stdout.write(JSON.stringify({bridge:Object.keys(bridge),node:'undefined'}));
"""
argv = ['node', '--experimental-vm-modules', '--input-type=module', '-e', js, preload]
executed = subprocess.run(argv, text=True, capture_output=True, check=True)
value = json.loads(executed.stdout)
result = {'status': 'INCOMPLETE', 'revision': revision, 'scope': __doc__.strip(),
          'assertion': assertion, 'actual': value, 'node_stderr': executed.stderr,
          'full_window_suite_run': False, 'gui_daemon_pty_starts': 0, 'model_turns': 0}
try:
    exec(compile(assertion, 'baseline-test_electron_e2e.py', 'exec'), {'value': value, 'sorted': sorted})
except AssertionError:
    result.update(status='PASS', baseline_assertion_result='FAIL', expected_failure_observed=True)
else:
    result.update(baseline_assertion_result='PASS', expected_failure_observed=False)
with output.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=False))
raise SystemExit(0 if result['expected_failure_observed'] else 1)
