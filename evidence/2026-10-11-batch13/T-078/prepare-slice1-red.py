"""Generate and verify one frozen red launch packet; start no services."""
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent


def main():
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if subprocess.check_output(['git', 'diff', 'HEAD', '--', 'workbench'], cwd=ROOT):
        raise RuntimeError('Freeze the workbench source before material generation.')
    if subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', 'workbench'], cwd=ROOT):
        raise RuntimeError('Untracked source must be frozen first.')
    out = BASE / 'p1-materials-slice1-red'
    if out.exists():
        raise RuntimeError('This material packet already exists; preserve it, do not regenerate.')
    subprocess.run([sys.executable, '-B', str(ROOT / 'workbench/tests/regenerate_t078_p1.py'),
                    '--label', out.name], cwd=ROOT, check=True)
    approval = json.loads((out / 'approval.json').read_bytes())
    scenario = json.loads((out / 'scenario.json').read_bytes())
    plane = json.loads((out / 'control-plane.json').read_bytes())
    root = Path(approval['input']['root'])
    assert approval['input']['code_revision'] == revision
    assert approval['input']['turn_limit'] == scenario['root_submit_budget'] == 1
    assert scenario['messages_request_budget'] == plane['messages_request_budget'] == 2
    assert plane['tool_call_budget'] == 1 and plane['real_vendor_model_budget'] == 0
    assert approval['launch']['env']['A2A_ROLE'] == 'controller'
    assert approval['launch']['preset'] == 'ideation' and approval['launch']['attempt'] is None
    assert 'A2A_OPERATOR_CREDENTIAL' not in approval['launch']['env']
    assert 'A2A_ATTEMPT' not in approval['launch']['env'] and 'A2A_FENCE' not in approval['launch']['env']
    assert not any(p.exists() for p in [root / 'api-ready.json', root / 'state/state.sqlite3'])
    assert not list((root / 'requests').iterdir())
    frozen = json.loads((out / 'source-files.json').read_bytes())
    assert 'workbench/bin/inbox' in frozen
    for name in ['run_t078_slice1.py', 't078_fake_inbox_tool.py', 't078_slice1_protocol.py']:
        assert 'workbench/tests/' + name in frozen
    with tarfile.open(out / 'sources.tar.gz') as archive:
        for name in frozen:
            data = (ROOT / name).read_bytes()
            assert archive.extractfile(name).read() == data
            assert subprocess.check_output(['git', 'show', revision + ':' + name], cwd=ROOT) == data
    for file in ['readiness-template.json', 'submit-approval-template.json', 'permission-approval-template.json']:
        template = json.loads((out / file).read_bytes())
        assert template.get('confirmed_by', template.get('approved_by')) is None
    result = {'status': 'PASS', 'scope': 'Frozen static material and byte readback; no launch/CLI/API/UI/model',
              'revision': revision, 'root': str(root), 'launch': approval['input']['launch'],
              'session': approval['input']['session'], 'thread': approval['input']['thread'],
              'source_files': len(frozen), 'real_cli_starts': 0, 'api_starts': 0, 'real_model_turns': 0,
              'root_submit_budget': 1, 'messages_request_budget': 2, 'tool_call_budget': 1,
              'approval': 'Only review the launch packet; startup keys, root and permission need separate approvals.'}
    with (out / 'static-check.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
