"""提交预检反例：代码/说明必须检查，原始证据保留，缺身份必须停；不操作 index。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

from commit_t081_closeout import commit_identity, whitespace_paths, REQUIRED_ENV, NATIVE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    prefix = 'evidence/2026-10-14-batch14/T-081/'
    code_docs = ['workbench/tests/commit_t081_closeout.py', 'acceptance/criterion.py',
                 'scripts/check', '.project-map/tickets/T-081.md', prefix + 'COMMIT-READY.md',
                 prefix + 'full-04/RESULTS.md', prefix + 'closeout-final-01/RESULTS.md']
    originals = [prefix + 'capability-run-03/traces/native/pty.raw',
                 prefix + 'capability-run-04/fixture_artifacts.py',
                 prefix + 'capability-review-03/FIRST-TURN.template.md',
                 prefix + 'capability-review-04/ROLE-BODY.md']
    checked, excluded = whitespace_paths(code_docs + originals)
    assert checked == code_docs and excluded == originals
    errors = []
    for label, env in [('missing-all', {}), ('wrong-native', {**os.environ, 'CODEX_THREAD_ID': 'wrong-native'}),
                       ('wrong-owner-session', {**os.environ, 'A2A_SESSION': 'wrong-session'})]:
        try:
            commit_identity(env)
        except RuntimeError as error:
            errors.append({'case': label, 'error': str(error)})
            if label == 'missing-all':
                assert all(name in str(error) for name in REQUIRED_ENV)
        else:
            raise AssertionError('错误身份必须停下：' + label)
    identity = commit_identity(os.environ)
    assert identity['agent'] == 's14-t081' and identity['native_session'] == NATIVE
    # Real Git flags source whitespace without creating a repository or index.
    with tempfile.TemporaryDirectory(prefix='t081-white-') as temporary:
        code = Path(temporary) / 'source.py'
        code.write_text('value = 1 \n', encoding='utf-8')
        result = subprocess.run(['git', 'diff', '--no-index', '--check', '--', '/dev/null', str(code)],
                                capture_output=True, text=True, check=False)
        assert result.returncode != 0 and 'trailing whitespace' in result.stdout
        whitespace = {'argv': result.args, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    report = {'status': 'PASS', 'scope': '分类、缺身份/错身份反例及真实 Git 空白错误；未 add、commit 或修改 index',
              'checked_examples': checked, 'raw_excluded_examples': excluded, 'identity_errors': errors,
              'valid_identity': identity, 'code_whitespace_counterexample': whitespace,
              'real_codex_turns': 0, 'raw_evidence_modified': False}
    (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'identity_negative_cases': len(errors), 'index_modified': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
