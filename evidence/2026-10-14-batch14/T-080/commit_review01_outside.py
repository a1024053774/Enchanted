#!/usr/bin/env python3
"""主控运行：只提交 T-080 独立审查报告、请求/完成记录和冻结 diff。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

from commit_outside import WORKER_ENV, RECEIPTS, runner

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'cdf8fe9b0eebfacf9f8d2ffeff3aecebf1e6eb37'
CANDIDATE = '1645eae0593f8d0bf4d51ef859bb231698a49752'
FILES = [str(HERE.relative_to(ROOT) / name) for name in (
    'independent-review-01.diff', 'independent-review-01.request.json',
    'independent-review-01.completed.json', 'independent-review-01.preparation.json',
    'independent-review-01.md',
    'commit_review01_outside.py')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.parent != RECEIPTS:
        raise RuntimeError('提交收据必须是主仓 T-080 证据根的新子目录。')
    out.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'INCOMPLETE', 'task': 'T-080', 'argv': sys.argv,
               'reviewed_candidate': CANDIDATE, 'files': FILES, 'commands': [], 'push': False}
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    env.update(WORKER_ENV)
    env['PYTHONDONTWRITEBYTECODE'] = '1'

    def command(argv, *, include_stdout=True):
        process = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=120)
        row = {'argv': argv, 'cwd': str(ROOT), 'exit': process.returncode,
               'stderr': process.stderr.decode('utf-8')}
        if include_stdout:
            row['stdout'] = process.stdout.decode('utf-8')
        else:
            row['stdout_bytes'] = len(process.stdout)
        receipt['commands'].append(row)
        if process.returncode:
            raise RuntimeError('审查产物提交步骤失败，保留现场：' + repr(argv))
        return process.stdout

    try:
        if command(['git', 'branch', '--show-current']).decode().strip() != 'exec/t080':
            raise RuntimeError('不是分配的 exec/t080 分支。')
        if command(['git', 'rev-parse', 'HEAD']).decode().strip() != CANDIDATE:
            raise RuntimeError('HEAD 已离开审查候选；不提交、不重做审查。')
        if command(['git', 'diff', '--cached', '--name-only']).strip():
            raise RuntimeError('已有暂存工作；不混入、不清除。')
        status = command(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode('utf-8')
        entries = [entry for entry in status.split('\0') if entry]
        if set(entry[3:] for entry in entries) != set(FILES) or any(not entry.startswith('?? ') for entry in entries):
            raise RuntimeError('工作树含审查产物之外的改动或缺少产物；保留现场。')
        request_path = HERE / 'independent-review-01.request.json'
        completed = json.loads((HERE / 'independent-review-01.completed.json').read_text(encoding='utf-8'))
        request_text = request_path.read_text(encoding='utf-8')
        request = json.loads(request_text)
        report = (HERE / 'independent-review-01.md').read_text(encoding='utf-8')
        if (request['base'] != BASE or request['candidate'] != CANDIDATE
                or completed['status'] != 'COMPLETED' or completed['review_status'] != 'PASS'
                or request_text != completed['request_text'] or report != completed['report_text']
                or not report.startswith('STATUS: PASS\n')):
            raise RuntimeError('审查版本、记录或报告已改变；不提交。')
        if (request['requested_model'] != 'gpt-6.1-sol' or request['requested_reasoning_effort'] != 'xhigh'
                or request['agent_type'] != 'explorer' or request['fork_turns'] != 'none'
                or completed['actual_service_tier'] != 'NOT_OBSERVED'):
            raise RuntimeError('审查请求配置或 tier 记录不符；不提交。')
        diff = command(['git', 'diff', '--binary', '--full-index', '--unified=1000000',
                        BASE, CANDIDATE, '--', *request['diff_paths']], include_stdout=False)
        if diff != (HERE / 'independent-review-01.diff').read_bytes():
            raise RuntimeError('冻结 diff 与被审查候选不一致；不提交。')
        runner.sizes(HERE)
        command(['git', 'diff', '--check'])
        command([sys.executable, '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py',
                 'status', '--root', '.'])
        sys.path.insert(0, str(ROOT / 'scripts'))
        from launch_records import find_launch
        from record_io import locked, read_records
        launches = Path(WORKER_ENV['A2A_LAUNCHES'])
        with locked(launches.parent / '.launches.lock'):
            launch = find_launch(read_records(launches), WORKER_ENV['A2A_LAUNCH'])
        for key in ('project', 'task', 'attempt', 'session', 'role'):
            if launch[key] != WORKER_ENV['A2A_' + key.upper()]:
                raise RuntimeError('原 worker 启动身份不符：' + key)
        if Path(launch['cwd']).resolve() != ROOT or launch['native_session'] not in ('unknown', WORKER_ENV['CODEX_THREAD_ID']):
            raise RuntimeError('原 worker 工作区或原生会话不符。')
        hooks = Path(WORKER_ENV['GIT_CONFIG_VALUE_0'])
        if not (hooks / 'prepare-commit-msg').is_file() or not os.access(hooks / 'prepare-commit-msg', os.X_OK):
            raise RuntimeError('原 worker 尾注钩子不可用；不装替代钩子。')
        command(['git', 'add', '--', *FILES])
        command(['git', 'commit', '-m', '记录 T-080 独立只读审查'])
        commit = command(['git', 'rev-parse', 'HEAD']).decode().strip()
        receipt['commit'] = commit
        if command(['git', 'rev-parse', 'HEAD^']).decode().strip() != CANDIDATE:
            raise RuntimeError('提交已落地，但父提交与审查候选不同；保留并上报。')
        changed = command(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines()
        if set(changed) != set(FILES):
            raise RuntimeError('提交已落地，但包含审查产物之外的文件；保留并上报。')
        message = command(['git', 'log', '-1', '--format=%B']).decode('utf-8')
        expected = {'Task': launch['task'], 'Attempt': launch['attempt'], 'Session': launch['session'],
                    'Role': 'worker', 'Tool': launch['cli_version'], 'Model': launch['model'],
                    'Effort': launch['effort'], 'Native-Session': WORKER_ENV['CODEX_THREAD_ID'], 'Launch': launch['launch_id']}
        actual = [line.partition(': ') for line in message.splitlines() if line.startswith('A2A-')]
        if len(actual) != len(expected) or {key[4:]: value for key, _, value in actual} != expected:
            raise RuntimeError('提交已落地，但九项钩子尾注不符；保留并上报。')
        if command(['git', 'status', '--porcelain=v1', '--untracked-files=all']).strip():
            raise RuntimeError('提交已落地，但工作树仍有改动；不清理，交主控核对。')
        receipt.update(status='PASS', scope='仅审查产物的本地提交；不是 submit、验收或集成')
    except Exception as error:
        receipt.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        runner.save(out / 'run.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
