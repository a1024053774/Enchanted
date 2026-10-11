#!/usr/bin/env python3
"""Read-only preparation checks; never start a daemon or native worker."""
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
import audit_s3_assertions as scope


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    commands = []
    for argv in (
        ['node', '--check', str(ROOT / 'workbench/tests/conflict_acceptance_host.ts')],
        ['bash', '-n', str(EVIDENCE / 'outside-sandbox.sh')],
        ['git', 'rev-parse', 'HEAD'], ['git', 'rev-parse', 'main'],
        ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'],
    ):
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        commands.append({'argv': argv, 'cwd': str(ROOT), 'exit': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr})
    ast.parse((ROOT / 'workbench/tests/test_worktree_lifecycle_e2e.py').read_text(encoding='utf-8'))
    compared, changed = [], []
    archive_path = EVIDENCE / 'outside-regression-03-cards/sources.tar.gz'
    with tarfile.open(archive_path, 'r:gz') as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.startswith('workbench/src/'):
                continue
            with archive.extractfile(member) as saved:
                same = (ROOT / member.name).read_bytes() == saved.read()
            compared.append(member.name)
            if not same:
                changed.append(member.name)
    audit = scope.audit_checkout(scope.INITIAL)
    text_files = [ROOT / 'workbench/tests/conflict_acceptance_host.ts',
                  ROOT / 'workbench/tests/test_worktree_lifecycle_e2e.py',
                  EVIDENCE / 'outside-sandbox.sh', EVIDENCE / 'PLAN.md',
                  EVIDENCE / 'HANDOFF-conflict-red-01.md', Path(__file__)]
    encoding = []
    for path in text_files:
        data = path.read_bytes()
        text = data.decode('utf-8')
        encoding.append({'path': str(path), 'bytes': len(data),
                         'pass': not data.startswith(b'\xef\xbb\xbf') and '\ufffd' not in text and '\r' not in text})
    cards = json.loads((EVIDENCE / 'outside-regression-03-cards/run.json').read_text(encoding='utf-8'))
    receipt_ok = (cards['status'], cards['tests_run'], cards['failures'], cards['errors'],
                  cards['skipped'], cards['collection_errors'], cards['exit_code']) == ('PASS', 15, 0, 0, 0, [], 0)
    passed = (all(c['exit'] == 0 for c in commands) and bool(compared) and not changed and
              audit['status'] == 'PASS' and receipt_ok and all(e['pass'] for e in encoding))
    report = {'status': 'PASS' if passed else 'NO_GO', 'scope': 'Static conflict preparation only',
              'argv': sys.argv, 'commands': commands, 'python_ast': 'PASS', 'assertion_scope': audit,
              'source_archive': str(archive_path), 'byte_equal_product_files': compared,
              'changed_product_files': changed, 'encoding': encoding, 'cards_receipt_verified': receipt_ok,
              'real_codex_turns': 0, 'conflict_business_evidence': 'INCOMPLETE: outside run pending'}
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({'status': report['status'], 'product_files': len(compared),
                      'changed_product_files': changed, 'real_codex_turns': 0}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
