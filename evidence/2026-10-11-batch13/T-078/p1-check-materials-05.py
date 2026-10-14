"""Check the frozen P1-05 materials without starting a vendor CLI or service."""
import argparse
import ast
import json
import subprocess
import tarfile
from pathlib import Path

SOURCE = Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
MATERIALS = BASE / 'p1-materials-05'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=BASE / 'p1-preparation-check-05.json')
args = parser.parse_args()
record = {'status': 'INCOMPLETE', 'scope': 'Static checks only',
          'real_cli_starts': 0, 'api_starts': 0, 'real_vendor_model_turns': 0,
          'commands': [], 'checks': []}

def command(argv):
    p = subprocess.run(argv, cwd=SOURCE, capture_output=True, text=True, encoding='utf-8')
    record['commands'].append({'argv': argv, 'cwd': str(SOURCE), 'exit_code': p.returncode,
                               'stdout': p.stdout, 'stderr': p.stderr})
    if p.returncode:
        raise RuntimeError({'failed_command': argv, 'exit_code': p.returncode})
    return p.stdout

try:
    old = json.loads((BASE / 'p1-materials-03/approval.json').read_text(encoding='utf-8'))
    new = json.loads((MATERIALS / 'approval.json').read_text(encoding='utf-8'))
    pairs = [(old['input'][field], new['input'][field])
             for field in ['root', 'task', 'launch', 'session', 'thread', 'source_snapshot']]

    def rebind(value):
        if isinstance(value, str):
            for before, after in pairs:
                value = value.replace(before, after)
            return value
        if isinstance(value, list):
            return [rebind(item) for item in value]
        if isinstance(value, dict):
            return {key: rebind(item) for key, item in value.items()}
        return value

    for field in ['argv', 'shell_argv', 'settings', 'role_text', 'node_executable', 'node_version']:
        assert new['launch'][field] == rebind(old['launch'][field]), field
    assert new['launch']['env'] == {**rebind(old['launch']['env']), 'IS_DEMO': '1'}
    record['checks'].append({'name': 'argv_and_hooks_unchanged_from_03', 'status': 'PASS',
                             'allowed_environment_addition': {'IS_DEMO': '1'}})
    root = Path(new['input']['root'])
    assert root.is_dir()
    assert new['input']['api_url'] == 'http://127.0.0.1:0'
    settings = (root / 'claude/settings.json').read_bytes()
    assert settings == (MATERIALS / 'isolated-settings.json').read_bytes()
    assert json.loads(settings) == {'theme': 'dark'}
    for name in ['input.json', 'role.md', 'nonce.txt']:
        assert (root / name).read_bytes() == (MATERIALS / name).read_bytes(), name
    for parent in ['home', 'claude']:
        assert not (root / parent / '.claude.json').exists()
    record['checks'].append({'name': 'theme_only_isolated_materials', 'status': 'PASS', 'root': str(root)})
    files = json.loads((MATERIALS / 'source-files.json').read_text(encoding='utf-8'))
    with tarfile.open(MATERIALS / 'sources.tar.gz') as archive:
        for name in files:
            data = (SOURCE / name).read_bytes()
            assert data == archive.extractfile(name).read(), name
            if name.endswith('.py'):
                ast.parse(data, filename=name)
    record['checks'].append({'name': 'source_snapshot_and_python_syntax', 'status': 'PASS', 'files': len(files)})
    node = new['launch']['node_executable']
    for name in ['workbench/src/claudeLaunch.ts', 'workbench/src/panes.ts', 'workbench/src/daemon.ts',
                 'workbench/src/gates/cli.ts', 'workbench/tests/prepare_t078_p1.ts',
                 'workbench/tests/test_t078_p1_bootstrap.ts']:
        command([node, '--check', str(SOURCE / name)])
    command(['bash', '-n', str(BASE / 'outside-sandbox.sh')])
    command(['git', 'diff', '--check'])
    for name in ['workbench/README.md', 'evidence/2026-10-11-batch13/T-078/RESULTS.md',
                 'evidence/2026-10-11-batch13/T-078/P1-APPROVAL-05.md']:
        data = (SOURCE / name).read_bytes()
        data.decode('utf-8')
        assert not data.startswith(b'\xef\xbb\xbf') and b'\r' not in data, name
    record['checks'].append({'name': 'syntax_and_utf8', 'status': 'PASS'})
    oversized = command(['find', str(BASE), '-type', 'f', '-size', '+5M']).strip()
    assert not oversized, oversized
    status = command(['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py',
                      'status', '--root', '.'])
    record['checks'].append({'name': 'evidence_size_and_project_status', 'status': 'PASS', 'project_status': status})
    record['status'] = 'PASS'
except Exception as error:
    record['error'] = repr(error)
with args.output.open('x', encoding='utf-8') as output:
    json.dump(record, output, ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
