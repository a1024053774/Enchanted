#!/usr/bin/env python3
"""Save static checks and controlled-Panes evidence before the outside gate."""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
EVIDENCE = ROOT / 'evidence/2026-10-11-batch13/T-077'
sys.path.insert(0, str(ROOT / 'workbench/tests'))
import audit_s3_assertions as audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    out = args.output.resolve()
    commands = []
    for argv in (
        *(['node', '--check', str(ROOT / name)] for name in (
            'workbench/src/gates/core.ts', 'workbench/src/contracts/a2aGates.ts', 'workbench/src/panes.ts',
            'workbench/tests/conflict_acceptance_host.ts', 'workbench/tests/test_conflict_panes.ts',
            'workbench/tests/test_native_final_read.ts', 'workbench/tests/test_pane_dispatch_state.ts')),
        ['bash', '-n', str(EVIDENCE / 'outside-sandbox.sh')],
        ['git', 'diff', '--check'], ['git', 'rev-parse', 'HEAD'], ['git', 'rev-parse', 'main'],
        ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'],
    ):
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        commands.append({'argv': argv, 'cwd': str(ROOT), 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    for path in (ROOT / 'workbench/tests').glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
    scope = audit.audit_checkout(audit.INITIAL)
    scope['self_check'] = audit.self_check()
    baseline = json.loads((EVIDENCE / 'baseline-conflict-red-01.json').read_text(encoding='utf-8'))
    equal, changed = [], []
    with tarfile.open(baseline['source_archive'], 'r:gz') as archive:
        for name in baseline['byte_equal_to_git_show']:
            with archive.extractfile(name) as saved:
                matches = (Path(baseline['product_root']) / name).read_bytes() == saved.read()
            (equal if matches else changed).append(name)
    panes = []
    for phase in ('red', 'green'):
        record = json.loads((EVIDENCE / ('panes-conflict-' + phase + '-01.json')).read_text(encoding='utf-8'))
        fixture = Path(record['root']).resolve(strict=True)
        if fixture.parent != Path('/tmp').resolve() or not fixture.name.startswith('s3-pane-'):
            raise RuntimeError('Panes fixture path is not owned by this probe')
        with tarfile.open(out / ('panes-' + phase + '-fixtures.tar.gz'), 'x:gz') as archive:
            archive.add(fixture, arcname=fixture.name)
        panes.append(record)
    pane_red = len(panes[0]['tests']) == 4 and all(not t['pass'] and t.get('assertion') for t in panes[0]['tests'])
    pane_green = len(panes[1]['tests']) == 4 and all(t['pass'] for t in panes[1]['tests'])
    cli_red = json.loads((EVIDENCE / 'outside-conflict-red-01/run.json').read_text(encoding='utf-8'))
    cli_red_ok = (cli_red['red_confirmed'] is True and len(cli_red['cases']) == 7 and
                  all(c['business_red'] and c['errors'] == 0 for c in cli_red['cases']))
    paths = sorted((ROOT / 'workbench/src').rglob('*.ts'))
    paths += sorted((ROOT / 'workbench/tests').glob('*.py')) + sorted((ROOT / 'workbench/tests').glob('*.ts'))
    paths += [ROOT / 'workbench/README.md', EVIDENCE / 'PLAN.md', EVIDENCE / 'outside-sandbox.sh',
              EVIDENCE / 'PANES-BOUNDARY.md', EVIDENCE / 'HANDOFF-conflict-green-01.md', Path(__file__)]
    encoding = []
    with tarfile.open(out / 'candidate-source.tar.gz', 'x:gz') as archive:
        for path in paths:
            relative = str(path.relative_to(ROOT))
            raw = path.read_bytes()
            content = raw.decode('utf-8')
            encoding.append({'path': relative, 'utf8_no_bom_lf': not raw.startswith(b'\xef\xbb\xbf') and '\r' not in content and '\ufffd' not in content})
            archive.add(path, arcname=relative, recursive=False)
    diff = subprocess.run(['git', 'diff', '--', 'workbench/src', 'workbench/tests', 'workbench/README.md'],
                          cwd=ROOT, capture_output=True, check=True).stdout
    (out / 'candidate.patch').write_bytes(diff)
    passed = (all(c['exit'] == 0 for c in commands) and scope['status'] == 'PASS' and scope['self_check']['status'] == 'PASS'
              and equal and not changed and pane_red and pane_green and cli_red_ok and all(e['utf8_no_bom_lf'] for e in encoding))
    record = {'status': 'PASS' if passed else 'NO_GO', 'scope': 'Static checks and isolated Panes only',
              'argv': sys.argv, 'commands': commands, 'scope_audit': scope, 'python_ast': 'PASS',
              'baseline_product': baseline['product_root'], 'baseline_byte_equal_files': equal,
              'baseline_changed_files': changed, 'encoding': encoding, 'panes': panes,
              'panes_business_red': pane_red, 'panes_green': pane_green, 'cli_business_red': cli_red_ok,
              'cli_green': 'INCOMPLETE: outside run pending', 'real_codex_turns': 0}
    with (out / 'run.json').open('x', encoding='utf-8') as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({k: record[k] for k in ('status', 'panes_business_red', 'panes_green', 'cli_business_red', 'cli_green', 'real_codex_turns')}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
