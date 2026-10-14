"""主控运行：待 CAS 和实际 home 清理收据齐备后，只暂存并 Git 提交 T-081。"""
import json
import os
from pathlib import Path
import subprocess
import sys

from command_evidence import CommandLog

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'evidence/2026-10-14-batch14/T-081'
HEAD = '391d70b07ceda29462c06b47116b36829d767001'
FILES = [
    'archive_t081_capability_run02.py', 'capability_command_paths.py', 'capability_poll_evidence.py',
    'check_t081_capability_paths.py', 'check_t081_capability_run03.py', 'collect_t081_closeout.py',
    'commit_t081_closeout.py', 'diagnose_t081_capability_run02.py', 'prepare_t081_capability.py',
    'prepare_t081_capability_run02.ts', 'prepare_t081_capability_run03.ts', 'prepare_t081_capability_run04.ts',
    'prepare_t081_mutants.py', 'run_t081_bad_worker_suite.py', 'run_t081_capability_turn.py',
    'run_t081_cas_suite.py', 't081_capability_audit.ts', 't081_capability_home.py', 't081_capability_materials.ts',
    'test_bad_worker_e2e.py', 'test_t081_archive_ownership.py', 'test_t081_capability_audit.ts', 'test_t081_cleanup.py',
]


def main():
    # Keep commit output outside the tree being staged; no self-changing logs
    # can become half-staged evidence. Existing attempts are never overwritten.
    out = Path('/private/tmp/t081-closeout-commit-01')
    out.mkdir(exist_ok=False)
    log = CommandLog(out)
    def run(argv):
        result = log.run(argv, cwd=ROOT, env=os.environ, timeout=240)
        if result.returncode:
            raise RuntimeError('命令失败；保留 index 和日志，不 reset 或绕过 hook：' + str(result.evidence['id']))
        return result.stdout.strip()
    prefixes = [str((ROOT / 'workbench/tests' / name).relative_to(ROOT)) for name in FILES]
    evidence_prefix = str(BASE.relative_to(ROOT)) + '/'
    def scoped_names():
        argv = ['git', 'diff', '--cached', '--name-only', '-z']
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, check=True)
        names = [name.decode('utf-8') for name in result.stdout.split(b'\0') if name]
        unknown = [name for name in names if name not in prefixes and not name.startswith(evidence_prefix)]
        if unknown:
            raise RuntimeError('index 含其他任务内容，不提交或重置：' + repr(unknown[:20]))
        return names
    if run(['git', 'branch', '--show-current']) != 'exec/t081' or run(['git', 'rev-parse', 'HEAD']) != HEAD:
        raise RuntimeError('分支/起点改变，停止重新核对。')
    if run(['git', 'diff', '--name-only']):
        raise RuntimeError('出现受控文件 diff；不把其他修改纳入本票。')
    scoped_names()
    cas = json.loads((BASE / 'cas-01/run.json').read_text(encoding='utf-8'))
    if cas.get('status') != 'PASS' or [step['label'] for step in cas.get('steps', [])] != ['red', 'green'] or not all(step['valid_evidence'] for step in cas['steps']):
        raise RuntimeError('CAS 补证尚未通过，不提交。')
    cleanup = json.loads((BASE / 'home-cleanup-01.json').read_text(encoding='utf-8'))
    if cleanup.get('status') != 'PASS' or cleanup.get('removed') is not True or cleanup.get('check_only') is not False or len(cleanup.get('checked_runs', [])) != 4 or Path('/private/tmp/t081-capability-01/codex-home').exists():
        raise RuntimeError('缺少四轮核对后的实际 home 删除收据，不提交。')
    run([sys.executable, '-B', ROOT / 'workbench/tests/collect_t081_closeout.py', '--output', BASE / 'closeout-final-01'])
    run([sys.executable, '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', ROOT])
    count, total = 0, 0
    for path in BASE.rglob('*'):
        if path.is_symlink() or path.name in ('.git', 'auth.json'):
            raise RuntimeError('证据中出现链接、内嵌 Git 或凭据文件；不暂存：' + str(path))
        if path.is_file():
            if path.stat().st_size > 5_000_000:
                raise RuntimeError('单文件超过 5 MB，停止报告：' + str(path))
            count += 1; total += path.stat().st_size
    inventory = {'evidence_files': count, 'evidence_bytes': total, 'test_files': prefixes,
                 'unresolved': ['6a 完全缺尾注裁定', '6e 追溯字段一致性裁定'],
                 'preserves_raw_failures': True, 'no_submit_or_push': True}
    (out / 'scope.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(inventory, ensure_ascii=False), flush=True)
    run(['git', 'add', '--', *prefixes, str(BASE.relative_to(ROOT))])
    staged = scoped_names()
    run(['git', 'diff', '--cached', '--check'])
    run(['git', 'diff', '--cached', '--stat', '--stat-count=30'])
    message = out / 'message.txt'
    message.write_text('T-081: add bad-worker matrix and capability evidence\n\n'
                       '受控坏行为、正例与回归证据；真实能力观察累计 3/3；CAS 先红后绿与隔离 home 清理。\n'
                       '6a 完全缺尾注与 6e 追溯字段一致性仍待用户裁定，不称全票通过。\n', encoding='utf-8')
    # Project hooks own all trailers. Never handwrite A2A metadata or bypass.
    run(['git', 'commit', '--quiet', '--file', message])
    result = {'status': 'PASS', 'scope': '仅本票 Git 提交；未 submit、集成或 push',
              'commit': run(['git', 'rev-parse', 'HEAD']), 'staged_files': len(staged),
              'pending_decisions': inventory['unresolved'], 'logs': str(out)}
    (out / 'run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
