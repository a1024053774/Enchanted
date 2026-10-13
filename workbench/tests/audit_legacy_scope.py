"""Scope audit against controller decisions 01/03; not a behavioral oracle."""
import ast
import subprocess

BASELINE = 'a7f4cc3033c16d5888de50d8352da516c941f8e9'
ALLOWED = {
    'acceptance/test_coop_e2e.py': {
        'create': 'F14: executor.model only',
        'test_good_candidate_uses_oracle_snapshot_and_integrates_once': 'F05/W03',
        'test_baseline_change_after_verification_rejects_integration': 'F05/W03',
        'test_submit_requires_clean_head_and_cannot_replace_frozen_candidate': 'W07'},
    'acceptance/test_run_e2e.py': {
        'test_run_entry_point_completes_registered_task': 'W02/F07',
        'test_fixture_existing_dispatch_submit_oracle_integration_and_reclaim': 'W02/F07',
        'test_concurrent_duplicate_run_has_one_prompt_and_one_attempt': 'F07',
        'test_matching_reclaim_guard_is_idempotent_after_automatic_success': 'W02/F07',
        'test_oracle_failure_is_not_success_and_reclaims_only_owned_thread': 'W01'},
    'acceptance/test_recovery_e2e.py': {},
}


def audit(root):
    scopes = []
    for file, allowed in ALLOWED.items():
        before = subprocess.run(['git', 'show', BASELINE + ':' + file], cwd=root,
                                text=True, capture_output=True, check=True).stdout
        after = (root / file).read_text(encoding='utf-8')
        def masked(source):
            tree = ast.parse(source)
            functions = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in allowed}
            if set(functions) != set(allowed): raise RuntimeError('Approved method missing: ' + file)
            lines = source.splitlines(keepends=True)
            for name, node in sorted(functions.items(), key=lambda row: row[1].lineno, reverse=True):
                lines[node.lineno - 1:node.end_lineno] = ['    # APPROVED METHOD: ' + name + '\n']
            return ''.join(lines), functions
        original, old_methods = masked(before); current, methods = masked(after)
        if original != current: raise RuntimeError('Change outside approved acceptance methods: ' + file)
        for name in allowed:
            old, new = old_methods[name], methods[name]
            if ast.dump(old.args) != ast.dump(new.args): raise RuntimeError('Method signature changed: ' + name)
        if file.endswith('test_coop_e2e.py'):
            old, new = old_methods['create'], methods['create']
            old_create = ''.join(before.splitlines(keepends=True)[old.lineno - 1:old.end_lineno])
            new_create = ''.join(after.splitlines(keepends=True)[new.lineno - 1:new.end_lineno])
            model = '"model": "fixture"'
            if old_create.count(model) != 1 or new_create != old_create.replace(model, '"model": "gpt-6.1-sol"', 1):
                raise RuntimeError('F14 permits only the create helper model value change.')
            name = 'test_submit_requires_clean_head_and_cannot_replace_frozen_candidate'
            old, new = old_methods[name], methods[name]
            old_text = ''.join(before.splitlines(keepends=True)[old.lineno - 1:old.end_lineno])
            new_text = ''.join(after.splitlines(keepends=True)[new.lineno - 1:new.end_lineno])
            prefix = old_text[:old_text.index('        self.cli("integrate", "--task", self.task)')]
            if not new_text.startswith(prefix): raise RuntimeError('W07 changed a protected frozen-candidate check.')
        scopes.append({'file': file, 'allowed_methods': allowed, 'recovery_unchanged': before == after if not allowed else None})
    patch = subprocess.run(['git', 'diff', BASELINE, '--', *ALLOWED], cwd=root, text=True, capture_output=True, check=True).stdout
    frozen = root / 'evidence/2026-10-11-batch13/T-076/card-2/legacy-acceptance-hunks.diff'
    if patch != frozen.read_text(encoding='utf-8'):
        raise RuntimeError('Acceptance diff differs from the concrete handoff hunks.')
    file = 'workbench/tests/test_task_cards_e2e.py'
    before = subprocess.run(['git', 'show', BASELINE + ':' + file], cwd=root,
                            text=True, capture_output=True, check=True).stdout
    after = (root / file).read_text(encoding='utf-8')
    def f13_method(source):
        node = next(n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef)
                    and n.name == 'test_non_fast_forward_git_result_cannot_integrate')
        return ''.join(source.splitlines(keepends=True)[node.lineno - 1:node.end_lineno])
    original = f13_method(before)
    if original.count('a = self.create()') != 1 or f13_method(after) != original.replace('a = self.create()', 'a = self.create_managed()', 1):
        raise RuntimeError('F13 permits only its one preparation-call change; Git assertions must be unchanged.')
    return {'baseline': BASELINE, 'scopes': scopes, 'patch': patch,
            'f13': 'one preparation call; original assertions unchanged',
            'f14': 'create helper matches baseline with only model fixture -> gpt-6.1-sol'}
