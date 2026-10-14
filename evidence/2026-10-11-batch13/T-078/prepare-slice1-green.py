"""Freeze a new green launch packet after passing regression; start no services."""
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent

def main():
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    freeze = json.loads((BASE / 'controller-green-code-freeze.json').read_bytes())
    regression = json.loads((BASE / 'controller-green-outside-01/result.json').read_bytes())
    assert revision == freeze['revision'] == regression['revision'] and regression['status'] == 'PASS'
    assert not subprocess.check_output(['git', 'diff', 'HEAD', '--', 'workbench'], cwd=ROOT)
    assert not subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', 'workbench'], cwd=ROOT)
    out = BASE / 'p1-materials-slice1-green'
    assert not out.exists(), 'Preserve existing material; no regeneration'
    subprocess.run([sys.executable, '-B', str(ROOT / 'workbench/tests/regenerate_t078_p1.py'), '--label', out.name], cwd=ROOT, check=True)
    approval = json.loads((out / 'approval.json').read_bytes())
    scenario = json.loads((out / 'scenario.json').read_bytes())
    plane = json.loads((out / 'control-plane.json').read_bytes())
    manifest = approval['input']; root = Path(manifest['root']); launch = approval['launch']
    assert manifest['code_revision'] == revision
    assert manifest['turn_limit'] == scenario['root_submit_budget'] == plane['root_submit_budget'] == 2
    assert scenario['messages_request_budget'] == plane['messages_request_budget'] == 3
    assert plane['tool_call_budget'] == 1 and plane['real_vendor_model_budget'] == plane['launch_input_budget'] == 0
    assert launch['preset'] == 'ideation' and launch['attempt'] is None
    assert launch['env']['A2A_ROLE'] == 'controller' and launch['env']['A2A_SPEC_REV'] == '1'
    assert not any(k in launch['env'] for k in ['A2A_ATTEMPT', 'A2A_FENCE', 'A2A_OPERATOR_CREDENTIAL'])
    assert [e['to'] for e in scenario['inbox_fixture']] == ['ideation', 'executor']
    assert scenario['inbox_fixture_origin'].startswith('Predeclared incoming inputs;')
    assert len({e['id'] for e in scenario['inbox_fixture']}) == 2
    old = json.loads((BASE / 'p1-materials-slice1-red/input.json').read_bytes())
    assert all(manifest[k] != old[k] for k in ['root', 'launch', 'session', 'thread'])
    assert not any(p.exists() for p in [root / 'api-ready.json', root / 'state/state.sqlite3'])
    assert not list((root / 'requests').iterdir())
    frozen = json.loads((out / 'source-files.json').read_bytes())
    assert 'workbench/bin/inbox' in frozen and 'workbench/tests/test_t078_slice1_green_protocol.py' in frozen
    with tarfile.open(out / 'sources.tar.gz') as archive:
        for name in frozen:
            data = (ROOT / name).read_bytes()
            assert archive.extractfile(name).read() == data
            assert subprocess.check_output(['git', 'show', revision + ':' + name], cwd=ROOT) == data
    for file in ['readiness-template.json', 'screen-key-approval-template.json', 'submit-approval-template.json', 'permission-approval-template.json']:
        template = json.loads((out / file).read_bytes())
        assert template.get('confirmed_by', template.get('approved_by')) is None
    facts = {'status': 'PASS', 'scope': 'Frozen static materials and byte readback only; no launch', 'revision': revision,
             'root': str(root), 'launch': manifest['launch'], 'session': manifest['session'], 'thread': manifest['thread'],
             'source_files': len(frozen), 'real_cli_starts': 0, 'api_starts': 0, 'real_model_turns': 0,
             'root_submit_budget': 2, 'messages_request_budget': 3, 'tool_call_budget': 1,
             'approval': 'Launch only; screen keys, submit and permission need separate instance-bound approval'}
    with (out / 'static-check.json').open('x', encoding='utf-8') as stream:
        json.dump(facts, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(facts, ensure_ascii=False))

if __name__ == '__main__': main()
