#!/usr/bin/env python3
"""主控运行：验证通过后提交 T-080；尾注由原会话钩子生成，不 push。"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('t080_final_runner', HERE / 'run_final01_outside.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
# 来源是本 worker 启动环境；不从主控 shell 借用另一个会话身份。
WORKER_ENV = {
    'A2A_PROJECT': 'a2a', 'A2A_TASK': 'T-080', 'A2A_ATTEMPT': 'a1',
    'A2A_SESSION': 'a1334b21-5fb5-4bae-8a38-929401aab3c3', 'A2A_ROLE': 'worker',
    'A2A_LAUNCH': 'launch-8156a548a8d7400f93c66c576fbec29b',
    'A2A_LAUNCHES': '/Users/luckye/Documents/Code/a2a/records/launches.jsonl',
    'CODEX_THREAD_ID': '01a13a92-4deb-78b3-ad28-2473704a890e',
    'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.hooksPath',
    'GIT_CONFIG_VALUE_0': '/Users/luckye/Documents/Code/a2a/scripts/git-hooks',
}
RECEIPTS = Path(WORKER_ENV['A2A_LAUNCHES']).resolve().parents[1] / HERE.relative_to(ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    validation, out = args.validation.resolve(), args.output.resolve()
    if validation.parent != HERE or out.parent != RECEIPTS:
        raise RuntimeError('验证目录须在 worker 的 T-080 证据根；提交收据须在主仓同一 T-080 证据根的新子目录。')
    out.mkdir(parents=True, exist_ok=False)
    report = {'status': 'INCOMPLETE', 'task': 'T-080', 'argv': sys.argv, 'commands': [],
              'push': False, 'trailers': '由原 worker 会话钩子生成', 'independent_review': '由主控另外完成'}
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    env.update(WORKER_ENV)

    def command(argv):
        p = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
        report['commands'].append({'argv': argv, 'cwd': str(ROOT), 'exit': p.returncode,
                                   'stdout': p.stdout, 'stderr': p.stderr})
        if p.returncode:
            raise RuntimeError('提交步骤失败，保留暂存区与现场：' + repr(argv))
        return p.stdout.strip()

    try:
        result = json.loads((validation / 'run.json').read_text(encoding='utf-8'))
        manifest = json.loads((validation / 'source-manifest.json').read_text(encoding='utf-8'))
        if result['status'] != 'PASS' or result['task'] != 'T-080' or result.get('real_model_calls') != 0:
            raise RuntimeError('全量阶段未通过；不提交。')
        if command(['git', 'branch', '--show-current']) != 'exec/t080' or command(['git', 'rev-parse', 'HEAD']) != manifest['head']:
            raise RuntimeError('分支或冻结起点改变；不提交。')
        runner.ensure_frozen(validation / 'candidate-source.tar.gz')
        runner.sizes(HERE)
        if command(['git', 'diff', '--cached', '--name-only']):
            raise RuntimeError('已有暂存工作；不混入本提交，也不清除。')
        sys.path.insert(0, str(ROOT / 'scripts'))
        from launch_records import find_launch
        from record_io import locked, read_records
        launches = Path(WORKER_ENV['A2A_LAUNCHES'])
        with locked(launches.parent / '.launches.lock'):
            launch = find_launch(read_records(launches), WORKER_ENV['A2A_LAUNCH'])
        for key in ('project', 'task', 'attempt', 'session', 'role'):
            if launch[key] != WORKER_ENV['A2A_' + key.upper()]:
                raise RuntimeError('启动记录身份不符：' + key)
        if Path(launch['cwd']).resolve() != ROOT or launch['native_session'] not in ('unknown', WORKER_ENV['CODEX_THREAD_ID']):
            raise RuntimeError('启动工作区或原生会话不符。')
        hooks = Path(WORKER_ENV['GIT_CONFIG_VALUE_0'])
        if not (hooks / 'prepare-commit-msg').is_file() or not os.access(hooks / 'prepare-commit-msg', os.X_OK):
            raise RuntimeError('原会话尾注钩子不可用；不安装替代钩子。')
        paths = [*runner.OWNED, 'evidence/2026-10-14-batch14/T-080']
        command(['git', 'add', '--', *paths])
        command(['git', 'commit', '-m', '保护任务卡验收文件并保留 T-080 门禁证据'])
        commit = command(['git', 'rev-parse', 'HEAD'])
        message = command(['git', 'log', '-1', '--format=%B'])
        report.update(commit=commit, message=message)
        expected = {'Task': launch['task'], 'Attempt': launch['attempt'], 'Session': launch['session'],
                    'Role': 'worker', 'Tool': launch['cli_version'], 'Model': launch['model'],
                    'Effort': launch['effort'], 'Native-Session': WORKER_ENV['CODEX_THREAD_ID'], 'Launch': launch['launch_id']}
        actual = [line.partition(': ') for line in message.splitlines() if line.startswith('A2A-')]
        if len(actual) != len(expected) or {k[4:]: v for k, _, v in actual} != expected:
            raise RuntimeError('提交已落地，但钩子尾注读回不符；保留提交并交主控核对。')
        runner.ensure_frozen(validation / 'candidate-source.tar.gz')
        status = command(['git', 'status', '--porcelain=v1', '--untracked-files=all'])
        if status:
            raise RuntimeError('提交后工作树仍有改动；原样保留并交主控核对，不清理。')
        report['status'] = 'PASS'
        report['scope'] = '本地提交及尾注读回；不代表独立验收或集成'
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        runner.save(out / 'run.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
