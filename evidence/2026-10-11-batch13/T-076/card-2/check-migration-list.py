"""Read-only checklist preparation; no backend or model execution."""
import argparse
import ast
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
card = Path(__file__).resolve().parent
root = card.parents[3]
if args.output.exists(): raise RuntimeError('Choose a new receipt path; do not overwrite evidence.')
record = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'real_codex_turns': 0,
          'scope': 'reviewer-green saved result, helper inventory and documentation only', 'commands': []}

def command(argv):
    p = subprocess.run(argv, cwd=root, text=True, capture_output=True, timeout=30)
    record['commands'].append({'argv': argv, 'cwd': str(root), 'exit': p.returncode,
                               'stdout': p.stdout, 'stderr': p.stderr})
    if p.returncode: raise RuntimeError('Read-only command failed: ' + repr(argv))
    return p.stdout

try:
    record['head'] = command(['git', 'rev-parse', 'HEAD']).strip()
    prior = command(['git', 'diff', 'd3f2c2cf3b838d8f56e8a57629a19b9d282ea64f', 'HEAD', '--', 'workbench', 'acceptance'])
    if prior: raise RuntimeError('Committed product changed since the previous checkpoint.')
    files = ['acceptance/test_coop_e2e.py', 'acceptance/test_recovery_e2e.py', 'acceptance/test_run_e2e.py',
             'workbench/tests/daemon_acceptance_adapter.py', 'workbench/tests/daemon_acceptance_host.ts',
             'workbench/tests/test_task_cards_e2e.py', 'workbench/tests/test_daemon_gates_e2e.py',
             'workbench/tests/test_multiturn_identity_e2e.py', 'workbench/tests/multiturn_identity_host.ts']
    if command(['git', 'diff', 'a7f4cc3033c16d5888de50d8352da516c941f8e9', '--', *files]):
        raise RuntimeError('Migration implementation began before checklist approval.')
    inventory = {}
    for file, owner, count in [(files[0], 'ManagedDeliveryCLI', 8), (files[1], 'RecoveryCLI', 9),
                               (files[2], 'RunCLI', 18), (files[5], 'TaskCardsCLI', 14)]:
        cls = next(n for n in ast.parse((root / file).read_text(encoding='utf-8')).body
                   if isinstance(n, ast.ClassDef) and n.name == owner)
        methods = {n.name: n.lineno for n in cls.body if isinstance(n, ast.FunctionDef)}
        if len([name for name in methods if name.startswith('test_')]) != count:
            raise RuntimeError('Frozen suite membership changed: ' + file)
        inventory[file] = methods
    record['method_inventory'] = inventory
    saved = card / 'outside-reviewer-green-01/run.json'
    previous = json.loads(saved.read_text(encoding='utf-8'))
    expected = [('reviewer-fault-green', 3), ('reviewer-normal-paths', 3), ('completed-review-score-recovery', 2)]
    if previous['status'] != 'PASS' or previous['real_codex_turns'] != 0 or previous['oversize_files']:
        raise RuntimeError('Saved reviewer checkpoint does not match controller report.')
    if [(s['name'], len(s['report']['cases'])) for s in previous['steps']] != expected:
        raise RuntimeError('Saved reviewer membership differs.')
    record['reviewer_green_readback'] = {'path': str(saved), 'steps': []}
    for step in previous['steps']:
        if step['exit'] or any(row['outcome'] != 'passed' or row['cleanup_failures'] for row in step['report']['cases']):
            raise RuntimeError('Saved reviewer case is not a clean pass.')
        record['reviewer_green_readback']['steps'].append({'name': step['name'], 'exit': step['exit'],
            'cases': [row['case'] for row in step['report']['cases']]})
    for file in ('F05-migration-list.md', 'RESULTS.md', 'assertion-hunks.md'):
        raw = (card / file).read_bytes()
        if raw.startswith(b'\xef\xbb\xbf') or '\ufffd' in raw.decode('utf-8'):
            raise RuntimeError('Document encoding readback failed: ' + file)
    command(['git', 'diff', '--check'])
    command(['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'])
    record['oversize_files'] = command(['find', str(card), '-size', '+5M']).splitlines()
    if record['oversize_files']: raise RuntimeError('Oversized evidence needs archival.')
    record['status'] = 'PASS'
except Exception as error:
    record['error'] = repr(error)
with args.output.open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({key: record[key] for key in ('status', 'product_status', 'real_codex_turns')}))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
