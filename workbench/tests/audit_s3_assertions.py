#!/usr/bin/env python3
"""Check T-077's approved assertion edit locations; do not judge test semantics."""
import argparse
import difflib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
INITIAL = '14b57d22a84bcaebfa91c5051b9909b53a570fac'
# Inclusive ORIGINAL line intervals from approved PLAN 12. Insertion-only
# entries use the line immediately before the insertion, with operation=insert.
RULES = {
    'acceptance/test_coop_e2e.py': [
        (161, 162, 'W13/W16', None), (173, 178, 'W16', None), (322, 322, 'W12', 'insert'),
        (343, 348, 'W02', None), (456, 474, 'W01', None)],
    'acceptance/test_run_e2e.py': [
        (219, 219, 'W03', 'insert'), (236, 247, 'W03', None), (324, 333, 'W04', None),
        (425, 427, 'W05', None), (442, 450, 'W06', None), (526, 526, 'W13', None),
        (531, 531, 'W13', None), (536, 539, 'W07', None), (546, 546, 'W13', None),
        (565, 567, 'W07/W13', None)],
    'workbench/tests/test_task_cards_e2e.py': [
        (152, 152, 'W08', None), (287, 287, 'W10', None), (295, 296, 'W10', None),
        (390, 400, 'W09', None)],
    'workbench/tests/test_cas_race.py': [(1, 5, 'W11', None), (20, 35, 'W11', None)],
    'workbench/tests/daemon_acceptance_adapter.py': [(291, 294, 'W14', None)],
}
# Task card permits fixture-error repairs without changing business assertions.
# These exact substitutions complete synthetic rollout metadata; any additional
# edit (including an assertion edit) in either file still fails the audit.
FIXTURE_METADATA = {
    'workbench/tests/test_native_final_read.ts': (
        'payload: { id: native, source: "cli" }', 'payload: { id: native, source: "cli", cwd: root }'),
    'workbench/tests/test_pane_dispatch_state.ts': (
        'payload: { source: "cli", id: "native" }', 'payload: { source: "cli", id: "native", cwd: root }'),
}
# Controller #58 authorizes this host-only repair after a real rollout proof.
# The original startup/shutdown test and every assertion remain unchanged.
STARTUP_HOST = 'workbench/tests/startup_shutdown_host.ts'
STARTUP_HOST_BASE = '457e02a867bfdc5d8b06a9d14214eb7a429c48c2'
STARTUP_HOST_EDITS = (
    ('exports: { spawn: () => {', 'exports: { spawn: (_shell: string, _argv: string[], options: { cwd: string }) => {'),
    ('payload: { id: native, source: "cli" }', 'payload: { id: native, source: "cli", cwd: options.cwd }'),
)


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, check=True).stdout


def audit_text(name, before, after):
    if name == STARTUP_HOST:
        expected = before
        unique = True
        for old, new in STARTUP_HOST_EDITS:
            unique = unique and expected.count(old) == 1
            expected = expected.replace(old, new, 1)
        allowed = unique and after == expected
        return {'file': name, 'allowed': allowed, 'fixture_metadata_only': allowed,
                'authority': 'Controller #58: use real CLI cwd evidence; repair metadata only',
                'diff': ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                                  fromfile='baseline/' + name, tofile='candidate/' + name))}
    if name in FIXTURE_METADATA:
        old, new = FIXTURE_METADATA[name]
        allowed = before.count(old) == 1 and after == before.replace(old, new, 1)
        return {'file': name, 'allowed': allowed, 'fixture_metadata_only': allowed,
                'authority': 'Task card: fixture errors may be repaired and recorded; no assertion change',
                'diff': ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                                  fromfile='baseline/' + name, tofile='candidate/' + name))}
    changes = []
    left, right = before.splitlines(keepends=True), after.splitlines(keepends=True)
    for op, a, b, c, d in difflib.SequenceMatcher(None, left, right, autojunk=False).get_opcodes():
        if op == 'equal':
            continue
        matched = []
        for lo, hi, rule, kind in RULES.get(name, []):
            if kind is not None and kind != op:
                continue
            if op == 'insert':
                allowed = a == lo if kind == 'insert' else lo - 1 <= a <= hi
            else:
                allowed = lo <= a + 1 and b <= hi
            if allowed:
                matched.append(rule)
        changes.append({'operation': op, 'original_lines': [a + 1, b], 'candidate_lines': [c + 1, d],
                        'whitelist': matched, 'allowed': bool(matched),
                        'before': ''.join(left[a:b]), 'after': ''.join(right[c:d])})
    return {'file': name, 'allowed': all(c['allowed'] for c in changes), 'changes': changes,
            'diff': ''.join(difflib.unified_diff(left, right, fromfile='baseline/' + name, tofile='candidate/' + name))}


def audit_checkout(base):
    tracked = git('ls-tree', '-r', '--name-only', base, '--', 'acceptance', 'workbench/tests').decode().splitlines()
    names = git('diff', '--name-only', base, '--', 'acceptance', 'workbench/tests').decode().splitlines()
    if base != INITIAL:
        for name in RULES:
            if git('show', base + ':' + name) != git('show', INITIAL + ':' + name):
                raise RuntimeError('Upstream changed the original whitelist coordinates: ' + name)
    records = []
    for name in names:
        if name not in tracked and name.startswith('workbench/tests/'):
            records.append({'file': name, 'allowed': True, 'new_test_artifact': True})
            continue
        before = git('show', base + ':' + name).decode('utf-8') if name in tracked else ''
        path = ROOT / name
        after = path.read_text(encoding='utf-8') if path.is_file() else ''
        records.append(audit_text(name, before, after))
    return {'status': 'PASS' if all(r['allowed'] for r in records) else 'NO_GO',
            'scope': 'Approved original edit coordinates only; semantic review and business evidence are separate.',
            'base': base, 'root': str(ROOT), 'files': records}


def self_check():
    cases = []
    probes = []
    name = 'acceptance/test_recovery_e2e.py'
    before = git('show', INITIAL + ':' + name).decode('utf-8')
    needle = 'self.check(self.ref() == self.base'
    if needle not in before:
        raise RuntimeError('Protected recovery assertion is unavailable for the audit counterexample')
    bad = before.replace(needle, 'self.check(self.ref() != self.base', 1)
    probes.append((name, before, bad))
    audit = audit_text(name, before, bad)
    cases.append({'name': 'reject_modified_recovery_assertion', 'expected_allowed': False,
                  'observed_allowed': audit['allowed'], 'audit': audit})
    name = 'acceptance/test_coop_e2e.py'
    before = git('show', INITIAL + ':' + name).decode('utf-8')
    needle = 'self.assertEqual(len(winners), 1, outcomes)'
    if before.count(needle) != 1:
        raise RuntimeError('Protected unique-claim assertion is unavailable')
    bad = before.replace(needle, 'self.assertEqual(len(winners), 4, outcomes)', 1)
    probes.append((name, before, bad))
    audit = audit_text(name, before, bad)
    cases.append({'name': 'reject_modified_unique_claim_assertion', 'expected_allowed': False,
                  'observed_allowed': audit['allowed'], 'audit': audit})
    for name, (old, new) in FIXTURE_METADATA.items():
        before = git('show', INITIAL + ':' + name).decode('utf-8')
        if before.count(old) != 1:
            raise RuntimeError('Fixture metadata repair is not uniquely bound: ' + name)
        good = before.replace(old, new, 1)
        needle = 'assert.equal(pane.native, native)' if name.endswith('test_native_final_read.ts') else 'assert.equal(writes.length, 0,'
        if before.count(needle) != 1:
            raise RuntimeError('Protected pane assertion is unavailable: ' + name)
        bad = good.replace(needle, needle.replace('assert.equal', 'assert.notEqual'), 1)
        probes.append((name, before, bad))
        audit = audit_text(name, before, bad)
        cases.append({'name': 'reject_assertion_edit_with_metadata_repair:' + name, 'expected_allowed': False,
                      'observed_allowed': audit['allowed'], 'audit': audit})
    before = git('show', STARTUP_HOST_BASE + ':' + STARTUP_HOST).decode('utf-8')
    bad = before
    for old, new in STARTUP_HOST_EDITS:
        if bad.count(old) != 1:
            raise RuntimeError('Startup fixture repair is not uniquely bound')
        bad = bad.replace(old, new, 1)
    bad = bad.replace('cwd: options.cwd', 'cwd: control', 1)
    probes.append((STARTUP_HOST, before, bad))
    audit = audit_text(STARTUP_HOST, before, bad)
    cases.append({'name': 'reject_wrong_cwd_in_startup_fixture', 'expected_allowed': False,
                  'observed_allowed': audit['allowed'], 'audit': audit})
    # Known-bad auditor: treating every edit as allowed must fail the independent
    # protected-scope examples. These checks do not test the product gate.
    def allow_all_mutant(_name, _before, _after):
        return {'allowed': True}
    mutant_results = [{'case': case['name'], 'expected_allowed': case['expected_allowed'],
                       'observed_allowed': allow_all_mutant(*probe)['allowed']}
                      for case, probe in zip(cases, probes)]
    bad_auditor_rejected = all(item['observed_allowed'] != item['expected_allowed'] for item in mutant_results)
    return {'status': 'PASS' if all(c['observed_allowed'] is c['expected_allowed'] for c in cases) and bad_auditor_rejected else 'NO_GO',
            'known_bad_allow_all_rejected': bad_auditor_rejected, 'mutant_results': mutant_results, 'cases': cases}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default=INITIAL)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = audit_checkout(args.base)
    report['auditor_self_check'] = self_check()
    if report['auditor_self_check']['status'] != 'PASS':
        report['status'] = 'NO_GO'
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({'status': report['status'], 'files': len(report['files']),
                      'auditor_self_check': report['auditor_self_check']['status']}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
