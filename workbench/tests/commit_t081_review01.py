"""主控运行：以 s14-t081 身份只提交一次独立审查报告与请求/完成记录。"""
import json
import os
from pathlib import Path
import subprocess

from command_evidence import CommandLog
from commit_t081_closeout import commit_identity

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'evidence/2026-10-14-batch14/T-081'
TARGET = 'b71cff6b458dc20acff7036614239592e998c22c'
ORIGIN = '391d70b07ceda29462c06b47116b36829d767001'
PATHS = ['workbench/tests/commit_t081_review01.py',
         'evidence/2026-10-14-batch14/T-081/independent-review-01.md',
         'evidence/2026-10-14-batch14/T-081/independent-review-01.request.json',
         'evidence/2026-10-14-batch14/T-081/independent-review-01.completed.json']


def main():
    out = Path('/private/tmp/t081-review01-commit-01')
    out.mkdir(exist_ok=False)
    log = CommandLog(out)
    report = {'status': 'INCOMPLETE', 'scope': '仅独立审查记录 Git 提交；不 submit、集成或 push'}
    def run(argv):
        result = log.run(argv, cwd=ROOT, env=os.environ, timeout=60)
        if result.returncode:
            raise RuntimeError('命令失败，保留 index 与日志，不 reset 或绕过 hook：' + str(result.evidence['id']))
        return result.stdout.strip()
    def names(*args):
        value = subprocess.run(['git', *args], cwd=ROOT, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'},
                               capture_output=True, check=True)
        return [name.decode('utf-8') for name in value.stdout.split(b'\0') if name]
    try:
        identity = commit_identity(os.environ)
        if run(['git', 'branch', '--show-current']) != 'exec/t081' or run(['git', 'rev-parse', 'HEAD']) != TARGET:
            raise RuntimeError('审查后的分支/候选发生变化，停止重新核对。')
        if names('ls-files', '--unmerged', '-z'):
            raise RuntimeError('index 有未合并冲突，不处理。')
        staged = names('diff', '--cached', '--name-only', '-z')
        changed = names('diff', '--name-only', '-z')
        if any(name not in PATHS for name in staged + changed):
            raise RuntimeError('存在独立审查交付之外的 staged/未暂存修改，不提交或重置。')
        for name in PATHS:
            path = ROOT / name
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 5_000_000:
                raise RuntimeError('审查交付缺失、含链接或超过 5 MB：' + name)
        request = json.loads((BASE / 'independent-review-01.request.json').read_text(encoding='utf-8'))
        completed = json.loads((BASE / 'independent-review-01.completed.json').read_text(encoding='utf-8'))
        review = (BASE / 'independent-review-01.md').read_text(encoding='utf-8')
        status = review.splitlines()[0].removeprefix('STATUS:').strip()
        if request['candidate'] != TARGET or request['base'] != ORIGIN or completed['candidate'] != TARGET:
            raise RuntimeError('审查绑定版本不符。')
        if (request['agent_type'], request['model_requested'], request['reasoning_effort_requested'], request['fork_turns']) != ('explorer', 'gpt-6.1-sol', 'xhigh', 'none'):
            raise RuntimeError('独立审查启动配置不符。')
        if completed['review_status'] != status or status not in ('PASS', 'NO_GO', 'INCOMPLETE') or completed['phase'] != 'completed':
            raise RuntimeError('报告状态与完成收据不符；不改写审查结论。')
        if completed['service_tier_observed'] is not None or request['service_tier_observed'] is not None:
            raise RuntimeError('本次 tier 未观察，记录不能声称已观察。')
        run(['git', 'add', '--', *PATHS])
        if set(names('diff', '--cached', '--name-only', '-z')) != set(PATHS):
            raise RuntimeError('暂存范围不是这四个审查交付文件。')
        run(['git', 'diff', '--cached', '--check', '--', *PATHS])
        run(['git', 'diff', '--cached', '--stat', '--', *PATHS])
        message = out / 'message.txt'
        message.write_text('T-081: record independent review of b71cff6b\n\n'
                           '独立 explorer，gpt-6.1-sol / xhigh 请求，fork_turns=none；tier 未观察。\n'
                           + '审查状态：' + status + '；保留原报告结论，不代表自动验收。\n'
                           '仅审查记录与提交脚本，不修改产品或既有原始证据。\n', encoding='utf-8')
        run(['git', 'commit', '--quiet', '--file', message])
        report['commit'] = run(['git', 'rev-parse', 'HEAD'])
        body = run(['git', 'log', '-1', '--format=%B'])
        expected = {'A2A-Task': identity['task'], 'A2A-Attempt': identity['attempt'],
                    'A2A-Session': identity['session'], 'A2A-Role': identity['role'],
                    'A2A-Tool': 'codex-cli 0.162.1', 'A2A-Model': 'gpt-6.1-sol', 'A2A-Effort': 'xhigh',
                    'A2A-Native-Session': identity['native_session'], 'A2A-Launch': identity['launch']}
        observed = {}
        for line in body.splitlines():
            key, delimiter, value = line.partition(':')
            if delimiter and key.startswith('A2A-'):
                observed.setdefault(key, []).append(value.strip())
        if observed != {key: [value] for key, value in expected.items()}:
            raise RuntimeError('提交已产生，但九项自动尾注读回不符；保留提交，不 reset。')
        report.update(status='PASS', review_status=status, identity=identity, trailers=observed, committed_paths=PATHS)
    except Exception as error:
        import traceback
        report.update(error=repr(error), traceback=traceback.format_exc(), index_and_commit_preserved=True)
    (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
