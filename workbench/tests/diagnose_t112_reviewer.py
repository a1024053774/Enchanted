"""Compare recorded reviewer arguments and native sandbox behavior. No model calls.

The original assertion and production permissions are left unchanged. Python 3.9.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import traceback
from run_t112_native import extract_baseline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--metadata-only', action='store_true')
    args = parser.parse_args()
    assert not args.summary.exists(), 'Preserve earlier evidence'
    source = Path(__file__).resolve().parents[2]
    root = Path(tempfile.mkdtemp(prefix='t112-permission-', dir='/private/tmp'))
    report = dict(status='INCOMPLETE', model_calls=0, commands=[], records={}, probes=[], fixture=str(root))
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_'))}
    manager = root / 'manager'; manager.mkdir()
    env.update(HOME=str(manager), LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')
    env.pop('NODE_OPTIONS', None)
    old = Path('/Users/luckye/.codex/packages/app-server-daemon/releases/0.162.1-aarch64-apple-darwin/bin/codex')
    newer = Path('/Users/luckye/.codex/packages/app-server-daemon/releases/0.163.0-aarch64-apple-darwin/bin/codex')

    def run(argv, cwd=source, extra_env=None):
        result = subprocess.run(list(map(str, argv)), cwd=cwd, env={**env, **(extra_env or {})},
                                text=True, capture_output=True, timeout=60)
        record = dict(argv=list(map(str, argv)), exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
        report['commands'].append(record)
        return record

    def probe(label, record, case, profile=False, bad=False, binary=None):
        candidate = Path(record['worktree'])
        protected = case / 'protected.txt'; protected.write_text('unchanged\n', encoding='utf-8')
        writable = candidate / 'candidate-probe.txt'
        if writable.exists(): writable.unlink()
        prefix = [str(binary or record['argv'][0]), 'sandbox', '--cd', str(candidate)]
        if profile:
            prefix += ['--permission-profile', ':workspace']
        else:
            prefix += ['-c', 'sandbox_mode=' + json.dumps(record['argv'][record['argv'].index('--sandbox') + 1])]
        for index, arg in enumerate(record['argv']):
            if arg == '-c' and not record['argv'][index + 1].startswith('hooks.'):
                prefix += ['-c', record['argv'][index + 1]]
        if bad:
            prefix += ['-c', 'sandbox_workspace_write.writable_roots=' + json.dumps([str(case)])]
        code = ('from pathlib import Path; Path(' + repr(str(writable)) + ').write_text("candidate-only"); '
                'Path(' + repr(str(protected)) + ').write_text("forbidden")')
        result = run(prefix + ['--', '/usr/bin/python3', '-I', '-S', '-B', '-c', code],
                     cwd=candidate, extra_env={'CODEX_HOME': record['env']['CODEX_HOME']})
        allowed = writable.exists() and writable.read_text(encoding='utf-8') == 'candidate-only'
        protected_value = protected.read_text(encoding='utf-8')
        oracle = allowed and result['exit'] != 0 and protected_value == 'unchanged\n' and 'PermissionError' in result['stderr']
        report['probes'].append(dict(label=label, command=result, candidate_write=allowed,
                                    protected_value=protected_value, boundary_oracle_passed=oracle))
        return oracle

    try:
        head = run(['git', 'rev-parse', 'HEAD'])['stdout'].strip()
        baseline = 'e3102389eda8952ea92cae4b373e14eaff898314'
        report.update(source_head=head, baseline=baseline)
        for binary in (old, newer):
            for suffix in (['--version'], ['--help'], ['sandbox', '--help']):
                assert run([binary, *suffix])['exit'] == 0
        shutil.copytree(source / 'workbench/node_modules', root / 'node_modules', symlinks=False,
                        ignore=shutil.ignore_patterns('.bin', 'win32-*', 'linux-*'))
        (root / 'node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper').chmod(0o755)
        helper = source / 'workbench/tests/t112_reviewer_record.mjs'
        for label, revision in [('baseline', baseline), ('candidate', head)]:
            tree = root / label
            archive = subprocess.check_output(['git', 'archive', revision, 'workbench'], cwd=source, env=env)
            extract_baseline(archive, tree)
            case = root / (label + '-case'); case.mkdir()
            result = run(['node', helper, tree / 'workbench', case, old, revision])
            assert result['exit'] == 0, result
            record = json.loads((case / 'record.json').read_text(encoding='utf-8'))
            report['records'][label] = record
            assert 'launch' in record, record
            assert record['launch']['cli_version'] == 'codex-cli 0.162.1'
            if not args.metadata_only:
                probe(label + '_old_profile_probe', record['launch'], case, profile=True)
                probe(label + '_legacy_workspace_write', record['launch'], case)
                probe(label + '_known_bad_parent_writable', record['launch'], case, bad=True)
                probe(label + '_legacy_with_0163_binary_only', record['launch'], case, binary=newer)
        rejected = root / 'version-rejection'; rejected.mkdir()
        result = run(['node', helper, root / 'candidate/workbench', rejected, newer, head])
        assert result['exit'] == 0, result
        report['records']['candidate_0163_attempt'] = json.loads((rejected / 'record.json').read_text(encoding='utf-8'))
        assert 'launch' not in report['records']['candidate_0163_attempt']
        assert 'codex_version_mismatch' in report['records']['candidate_0163_attempt']['error']['message']
        if args.metadata_only:
            report['classification'] = 'native_sandbox_probes_not_run'
        else:
            probes = {row['label']: row for row in report['probes']}
            for label in ('baseline', 'candidate'):
                for suffix in ('_old_profile_probe', '_legacy_workspace_write'):
                    assert probes[label + suffix]['candidate_write'], 'Sandbox setup failed: ' + label + suffix
                bad = probes[label + '_known_bad_parent_writable']
                assert bad['candidate_write'] and bad['protected_value'] == 'forbidden' and bad['command']['exit'] == 0 and not bad['boundary_oracle_passed'], bad
            base_ok = probes['baseline_legacy_workspace_write']['boundary_oracle_passed']
            candidate_ok = probes['candidate_legacy_workspace_write']['boundary_oracle_passed']
            def unsafe(label):
                row = probes[label + '_legacy_workspace_write']
                return row['candidate_write'] and row['protected_value'] == 'forbidden' and row['command']['exit'] == 0
            if base_ok and candidate_ok:
                report['classification'] = 'profile_probe_does_not_match_legacy_reviewer_permissions'
                assert all(probes[label + '_old_profile_probe']['protected_value'] == 'forbidden' for label in ('baseline', 'candidate'))
                report['status'] = 'PASS'
            elif unsafe('baseline') and unsafe('candidate'):
                report['classification'] = 'preexisting_boundary_failure_requires_blocking_permission_issue'
            elif base_ok and unsafe('candidate'):
                report['classification'] = 'candidate_boundary_regression'
            else:
                report['classification'] = 'mixed_results_require_investigation'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        shutil.rmtree(root)
        report['fixture_removed'] = not root.exists()
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(status=report['status'], summary=str(args.summary), classification=report.get('classification'))))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
