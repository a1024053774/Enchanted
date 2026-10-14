"""Freeze a new green launch packet after passing regression; start no services."""
import json
import argparse
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', type=Path, default=BASE / 'controller-green-code-freeze.json')
    parser.add_argument('--regression', type=Path, default=BASE / 'controller-green-outside-01')
    parser.add_argument('--label', choices=['p1-materials-slice1-green', 'p1-materials-slice1-green-3'], default='p1-materials-slice1-green')
    args = parser.parse_args()
    freeze_file = args.freeze.resolve(); regression_dir = args.regression.resolve()
    assert freeze_file.parent == BASE and freeze_file.name in ['controller-green-code-freeze.json', 'controller-green-2-code-freeze.json', 'controller-green-3-code-freeze.json']
    assert regression_dir.parent == BASE and regression_dir.name.startswith('controller-green-outside-')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    freeze = json.loads(freeze_file.read_bytes())
    regression = json.loads((regression_dir / 'result.json').read_bytes())
    assert revision == freeze['revision'] and regression['status'] == 'PASS'
    if freeze.get('reused_regression_revision'):
        assert regression['revision'] == freeze['reused_regression_revision']
        unchanged = ['workbench/src', 'workbench/app', 'workbench/hooks', 'workbench/bin', 'acceptance', 'scripts',
                     'workbench/tests/test_t078_controller_inbox_entry.ts', 'workbench/tests/test_t078_empty_declaration_entry.ts',
                     'workbench/tests/test_t078_input_entry.py', 'workbench/tests/electron_driver.mjs',
                     'workbench/tests/electron_client.py', 'workbench/tests/t078_runtime_scenario.py',
                     'workbench/tests/t078_terminal_receiver.py', 'workbench/tests/t078_native_receiver.c']
        assert not subprocess.check_output(['git', 'diff', regression['revision'], revision, '--', *unchanged], cwd=ROOT)
    else:
        assert revision == regression['revision']
    assert not subprocess.check_output(['git', 'diff', 'HEAD', '--', 'workbench'], cwd=ROOT)
    assert not subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', 'workbench'], cwd=ROOT)
    out = BASE / args.label
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
    old_label = 'p1-materials-slice1-green' if args.label == 'p1-materials-slice1-green-3' else 'p1-materials-slice1-red'
    old = json.loads((BASE / old_label / 'input.json').read_bytes())
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
             'regression_revision': regression['revision'], 'regression_reused': revision != regression['revision'],
             'approval': 'Launch only; screen keys, submit and permission need separate instance-bound approval'}
    with (out / 'static-check.json').open('x', encoding='utf-8') as stream:
        json.dump(facts, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(facts, ensure_ascii=False))

if __name__ == '__main__': main()
