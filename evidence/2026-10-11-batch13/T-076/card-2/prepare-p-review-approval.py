"""Freeze an unapproved P-review bundle and read saved evidence; no live probes."""
import argparse
import ast
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import traceback

CARD = Path(__file__).resolve().parent
ROOT = CARD.parents[3]
BUNDLE = CARD / 'p-review-02'
LEGACY = CARD / 'outside-legacy-green-06'


def read_json(path):
    return json.loads(path.read_bytes() if path.exists() else gzip.decompress(Path(str(path) + '.gz').read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--freeze-bundle', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('Choose a new preparation report path; preserve earlier reports.')
    report = dict(status='INCOMPLETE', product_status='INCOMPLETE', argv=sys.argv, commands=[],
                  real_model_started=False, auth_copied=False)

    def command(argv):
        result = subprocess.run(list(map(str, argv)), cwd=ROOT, capture_output=True, text=True)
        report['commands'].append(dict(argv=list(map(str, argv)), exit=result.returncode,
                                       stdout=result.stdout, stderr=result.stderr))
        if result.returncode:
            raise RuntimeError('Static command failed: ' + str(argv))
        return result.stdout.strip()

    try:
        policy = read_json(BUNDLE / 'launch-policy.json')
        if (BUNDLE / 'APPROVED.json').exists() or (CARD / 'real-turn-budget.jsonl').exists():
            raise RuntimeError('Approval or real budget exists; do not regenerate this instance.')
        if Path(policy['root']).exists() or Path(policy['root']).is_symlink():
            raise RuntimeError('The real fixture root already exists.')
        if not Path('/Volumes/WD-Elements').is_mount():
            raise RuntimeError('External disk is not mounted.')
        report['head'] = command(['git', 'rev-parse', 'HEAD'])
        report['fixture_root_exists'] = False
        report['approval_present'] = False
        report['model_budget_entries'] = 0
        paths = sorted(p for folder in ('src', 'hooks', 'tests') for p in (ROOT / 'workbench' / folder).rglob('*')
                       if p.is_file() and '__pycache__' not in p.parts and p.name != '.DS_Store')
        paths += [ROOT / 'workbench' / name for name in ('package.json', 'package-lock.json', 'LICENSE.synara')]
        names = sorted(str(p.relative_to(ROOT)) for p in paths)
        production = [n for n in names if n.startswith(('workbench/src/', 'workbench/hooks/'))]
        approved_changes = {
            'workbench/src/panes.ts': [
                ('"-c", `model_reasoning_effort=${JSON.stringify(effort)}`, "-c", \'service_tier="fast"\',',
                 '"-c", `model_reasoning_effort=${JSON.stringify(effort)}`,'),
                ('service_tier_requested: "fast"', 'service_tier_requested: "default"')],
            'workbench/src/gates/core.ts': [('requested_service_tier: "fast"', 'requested_service_tier: "default"')],
        }
        with tarfile.open(LEGACY / 'candidate-and-harness.tar.gz', 'r:gz') as previous:
            for name in production:
                expected = previous.extractfile(name).read()
                for before, after in approved_changes.get(name, []):
                    if expected.count(before.encode()) != 1: raise RuntimeError('Non-unique approved tier edit: ' + name)
                    expected = expected.replace(before.encode(), after.encode())
                if expected != (ROOT / name).read_bytes():
                    raise RuntimeError('Production exceeds the #76 tier edits: ' + name)
        if args.freeze_bundle:
            with tarfile.open(BUNDLE / 'source-snapshot.tar.gz', 'w:gz', dereference=True) as archive:
                for name in names:
                    archive.add(ROOT / name, arcname=name, recursive=False)
            with tarfile.open(BUNDLE / 'approval-materials.tar.gz', 'w:gz') as archive:
                for name in ('launch-policy.json', 'ROLE.md', 'probe_write.py', 'config.toml'):
                    archive.add(BUNDLE / name, arcname=name, recursive=False)
            manifest = dict(head=report['head'], snapshot='source-snapshot.tar.gz', paths=names,
                            production_matches='outside-legacy-green-06/candidate-and-harness.tar.gz',
                            matched_production_paths=[p for p in production if p not in approved_changes],
                            approved_production_changes=approved_changes, authorization='controller #76', real_model_started=False,
                            auth_copied=False, fixture_root_exists=False)
            (BUNDLE / 'source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        for filename, base, expected in [('source-snapshot.tar.gz', ROOT, names),
                                        ('approval-materials.tar.gz', BUNDLE, ['ROLE.md', 'config.toml', 'launch-policy.json', 'probe_write.py'])]:
            with tarfile.open(BUNDLE / filename, 'r:gz') as archive:
                assert sorted(archive.getnames()) == expected
                for member in archive.getmembers():
                    assert member.isfile() and archive.extractfile(member).read() == (base / member.name).read_bytes(), member.name
        report['frozen_source_files'] = len(names)
        report['production_files_matching_legacy06'] = len(production) - len(approved_changes)
        report['approved_production_changes'] = approved_changes

        for path in [ROOT / 'workbench/tests/run_p_review.py', ROOT / 'workbench/tests/run_t076_launch_policy.py',
                     ROOT / 'workbench/tests/test_quality_tracer_e2e.py', ROOT / 'workbench/tests/run_pane_lifecycle.py',
                     ROOT / 'workbench/tests/run_t076_real.py', BUNDLE / 'probe_write.py', Path(__file__)]:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        command([policy['node'], '--check', ROOT / 'workbench/tests/p_review_host.ts'])
        command([policy['node'], '--check', ROOT / 'workbench/src/panes.ts'])
        command([policy['node'], '--check', ROOT / 'workbench/src/gates/core.ts'])
        command(['zsh', '-n', CARD / 'outside-sandbox.sh'])
        command(['git', 'diff', '--check'])
        command(['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'])
        assert shlex.split((BUNDLE / 'argv.txt').read_text(encoding='utf-8')) == policy['codex_argv']
        assert set(policy['dynamic_values']) == {'REVIEW_ID', 'LAUNCH_ID'}
        assert policy['turn_limit'] == policy['slot'] == 1
        assert policy['service_tier_requested'] == 'default'
        assert not any(arg.startswith('service_tier=') for arg in policy['codex_argv'])
        assert policy['codex_argv'][6:11] == ['never', '--sandbox', 'read-only', '-m', 'gpt-6.1-sol']
        assert policy['tool_input'] in (BUNDLE / 'ROLE.md').read_text(encoding='utf-8')
        expected_hook = "[{hooks=[{type=\"command\",command=" + json.dumps(policy['hooks']['Stop']) + ",timeout=10}]}]"
        for event in ('UserPromptSubmit', 'Stop', 'PermissionRequest'):
            assert policy['hooks'][event] == policy['hooks']['Stop']
            assert 'hooks.' + event + '=' + expected_hook in policy['codex_argv']
        assert (BUNDLE / 'config.toml').read_text(encoding='utf-8') == '[projects."' + policy['repo'] + '"]\ntrust_level="trusted"\n'
        for path in [CARD / 'RESULTS.md', CARD / 'P-REVIEW-APPROVAL-02.md', BUNDLE / 'ROLE.md', ROOT / 'workbench/README.md']:
            raw = path.read_bytes()
            assert not raw.startswith(b'\xef\xbb\xbf') and b'\r' not in raw and '\ufffd' not in raw.decode('utf-8'), str(path)
        report['static_policy_checks'] = 'PASS'

        run = read_json(LEGACY / 'run.json')
        assert run['status'] == 'PASS' and run['real_codex_turns'] == 0 and len(run['steps']) == 22
        assert run['changed_source_paths'] == run['oversize_files'] == []
        report['legacy06'] = dict(status=run['status'], product_status=run['product_status'], steps=[])
        for step in run['steps']:
            value = read_json(Path(step['report']))
            assert step['exit'] == step['expected_exit'], step['name']
            row = {**step, 'recorded_status': value.get('status'),
                   'test_counts': {k: value[k] for k in ('tests_run', 'failures', 'errors', 'skipped') if k in value and isinstance(value[k], int)}}
            if step['expected_exit'] == 0:
                assert value.get('status', 'PASS' if value.get('failure') is None else 'INCOMPLETE') == 'PASS'
            if step['name'] in ('coop', 'recovery', 'run'):
                assert value['tests_run'] == {'coop': 8, 'recovery': 9, 'run': 18}[step['name']]
                assert value['failures'] == value['errors'] == value['skipped'] == 0
            if 'cases' in value:
                row['cases'] = [{k: c.get(k) for k in ('case', 'outcome', 'failure_id', 'cleanup_failures')} for c in value['cases']]
            if step['name'] == 'f10-red':
                assert value['cases'][0]['failure_id'] == 'MANUAL-CLAIM-SOURCE'
                assert value['cases'][0]['outcome'] == 'contract_failure' and not value['cases'][0]['cleanup_failures']
            if step['name'] == 'w07-red':
                assert value['failures'] == 1 and value['errors'] == 0
                assert any('W07-MANUAL-SOURCE' in f['traceback'] for f in value['failure_text'])
                ref = [c for c in value['commands'] if c.get('label') == 'git' and c['argv'][-2:] == ['rev-parse', 'refs/heads/main']][-1]['stdout'].strip()
                row['B'] = value['artifacts'][0]['base_commit']; row['actual_ref'] = ref
                assert row['B'] != ref
            if step['name'] == 'stop-ordering-red':
                assert not value['errors'] and len(value['failures']) == 1
                row['witness'] = value['artifacts'][0]['shutdown_precompletion']
                assert row['witness']['violation'] == 'final_event_before_gate'
            if step['name'] in ('omitted_bytes', 'window_stops_daemon', 'unknown_is_idle', 'restart_success'):
                row['error'] = value['error']; assert row['error'].startswith('AssertionError(')
            if step['name'] == 'missing_volume_builds':
                assert value['classification'] == 'business-red' and value['command']['exit'] == 0
                row['classification'] = value['classification']
            report['legacy06']['steps'].append(row)
        report['legacy06']['consistency'] = [read_json(Path(c['consistency_report'])) for c in run['consistency']]
        report['oversize_files'] = [str(p.relative_to(CARD)) for p in CARD.rglob('*') if p.is_file() and p.stat().st_size > 5 * 1024 * 1024]
        assert not report['oversize_files']
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({k: report[k] for k in ('status', 'product_status', 'real_model_started', 'auth_copied')}))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
