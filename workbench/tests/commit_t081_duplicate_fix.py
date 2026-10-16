"""主控运行：单案红绿及差异复审完成后，以原身份提交本次测试修正。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tarfile

from command_evidence import CommandLog
from commit_t081_closeout import commit_identity, whitespace_paths, path_parts

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'evidence/2026-10-14-batch14/T-081'
TARGET = '3ee28bc3ad77595e23b77dbef34af20c5370dea9'
CODE = ['test_bad_worker_e2e.py', 'prepare_t081_mutants.py', 'run_t081_bad_worker_suite.py',
        'collect_t081_closeout.py', 'run_t081_duplicate_case.py', 'test_t081_duplicate_input.py',
        'commit_t081_duplicate_fix.py']
DOCUMENTS = ['DUPLICATE-FIX.md', 'CLOSEOUT.md', 'independent-review-02.md',
             'independent-review-02.request.json', 'independent-review-02.completed.json']
DIRS = ['duplicate-fix-01', 'duplicate-conflict-01', 'closeout-duplicate-pending-01', 'closeout-duplicate-final-01']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log-dir', type=Path, default=Path('/private/tmp/t081-duplicate-commit-01'))
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    out = args.log_dir.resolve()
    if not args.check_only and (out == ROOT or ROOT in out.parents):
        raise RuntimeError('Commit logs must remain outside the worktree.')
    out.mkdir(exist_ok=False)
    log = CommandLog(out)
    report = {'status': 'INCOMPLETE', 'scope': '只提交矛盾 Session 输入修正及证据；未 submit/集成/push'}
    def run(argv):
        result = log.run(argv, cwd=ROOT, env=os.environ, timeout=120)
        if result.returncode:
            raise RuntimeError('命令失败，保留 index，不 reset 或绕过 hook：' + str(result.evidence['id']))
        return result.stdout.strip()
    def names(*values):
        result = subprocess.run(['git', *values], cwd=ROOT, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}, capture_output=True, check=True)
        return [value.decode('utf-8') for value in result.stdout.split(b'\0') if value]
    try:
        identity = commit_identity(os.environ)
        if run(['git', 'rev-parse', 'HEAD']) != TARGET or run(['git', 'branch', '--show-current']) != 'exec/t081':
            raise RuntimeError('差异修正的基线/分支变化，停止重新核对。')
        if run(['git', 'diff', '391d70b0', '--', 'workbench/src', 'workbench/hooks']):
            raise RuntimeError('出现产品修改，停止，不提交。')
        observed = json.loads((BASE / 'duplicate-conflict-01/run.json').read_text(encoding='utf-8'))
        if (observed.get('status') != 'PASS' or observed.get('variant') != 'conflicting_sessions'
                or not observed.get('actual_refusal_code') or not observed.get('counted_as_bad_behavior_pass')
                or [row['label'] for row in observed['steps']] != ['red', 'green']
                or not all(row['valid_evidence'] for row in observed['steps'])):
            raise RuntimeError('缺少新单案的目标业务红态与候选拒收，不提交。')
        review = json.loads((BASE / 'independent-review-02.completed.json').read_text(encoding='utf-8'))
        if (review.get('phase') != 'completed' or review.get('delta_status') != 'PASS'
                or 'P2-01' not in review.get('resolved_findings', []) or review.get('reviewed_base') != TARGET
                or review.get('source_snapshot') != 'evidence/2026-10-14-batch14/T-081/duplicate-conflict-01/candidate-source.tar.gz'):
            raise RuntimeError('差异复审尚未明确解决 P2-01，不提交。')
        with tarfile.open(BASE / 'duplicate-conflict-01/candidate-source.tar.gz', 'r:gz') as archive:
            for name in CODE:
                if name == 'commit_t081_duplicate_fix.py':
                    continue
                relative = 'workbench/tests/' + name
                if archive.extractfile(relative).read() != (ROOT / relative).read_bytes():
                    raise RuntimeError('Reviewed executable test bytes changed: ' + relative)
        exact = ['workbench/tests/' + name for name in CODE] + [str((BASE / name).relative_to(ROOT)) for name in DOCUMENTS]
        directories = [str((BASE / name).relative_to(ROOT)) for name in DIRS]
        def owned(name):
            return name in exact or any(name.startswith(directory + '/') for directory in directories)
        if names('ls-files', '--unmerged', '-z') or any(not owned(name) for name in names('diff', '--cached', '--name-only', '-z') + names('diff', '--name-only', '-z')):
            raise RuntimeError('index/工作树含其他任务内容或冲突，不 add 或重置。')
        for name in exact + directories:
            path = ROOT / name
            if path.is_symlink() or not path.exists():
                raise RuntimeError('交付缺失或含链接：' + name)
            for file in (path.rglob('*') if path.is_dir() else [path]):
                if file.is_symlink() or file.name in ('.git', 'auth.json') or file.is_file() and file.stat().st_size > 5_000_000:
                    raise RuntimeError('交付路径/大小越界，停止：' + str(file))
        if args.check_only:
            report.update(status='PASS', scope='Read-only commit preconditions; no add or commit',
                          identity=identity, delta_status=review['delta_status'],
                          actual_refusal_code=observed['actual_refusal_code'], frozen_case_sources_match=True)
            (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(json.dumps(report, ensure_ascii=False))
            return 0
        run(['git', 'add', '--', *exact, *directories])
        staged = names('diff', '--cached', '--name-only', '-z')
        if any(not owned(name) for name in staged):
            raise RuntimeError('暂存范围越界，不提交。')
        checked, excluded = whitespace_paths(staged)
        scope = {'identity': identity, 'checked_paths': checked,
                 'raw_whitespace_exclusions': path_parts(out / 'whitespace-excluded', excluded),
                 'actual_refusal_code': observed['actual_refusal_code'], 'resolved_findings': review['resolved_findings'],
                 'unresolved': ['6a', '6e', '最终组合入口未完整重跑']}
        (out / 'scope.json').write_text(json.dumps(scope, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if not checked:
            raise RuntimeError('空白检查范围为空，不提交。')
        run(['git', 'diff', '--cached', '--check', '--', *checked])
        run(['git', 'diff', '--cached', '--stat', '--stat-count=25'])
        message = out / 'message.txt'
        message.write_text('T-081: test conflicting Session trailer identities\n\n'
                           '以一真一假的 Session 输入取代同值重复；旧案仅观察，不计坏行为通过。\n'
                           '单案唯一变异先红、候选拒收与差异复审见原始证据；不改产品。\n'
                           '6a/6e 仍待裁定，未称最终组合入口完整重跑。\n', encoding='utf-8')
        run(['git', 'commit', '--quiet', '--file', message])
        report.update(status='PASS', commit=run(['git', 'rev-parse', 'HEAD']), identity=identity,
                      actual_refusal_code=observed['actual_refusal_code'])
    except Exception as error:
        import traceback
        report.update(error=repr(error), traceback=traceback.format_exc(), index_preserved=True)
    (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
