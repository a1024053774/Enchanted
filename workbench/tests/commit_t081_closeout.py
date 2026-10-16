"""主控运行：待 CAS 和实际 home 清理收据齐备后，只暂存并 Git 提交 T-081。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from command_evidence import CommandLog

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'evidence/2026-10-14-batch14/T-081'
HEAD = '391d70b07ceda29462c06b47116b36829d767001'
LAUNCH = 'launch-517c75701a0443ec9633fb6388e8ad2f'
NATIVE = '01a13bc2-d779-7370-88a0-6b71bb434456'
LEDGER = Path('/Users/luckye/Documents/Code/a2a/records/launches.jsonl')
CODE_PREFIXES = ('workbench/', 'acceptance/', 'scripts/', '.project-map/')
REQUIRED_ENV = ('A2A_PROJECT', 'A2A_TASK', 'A2A_ATTEMPT', 'A2A_SESSION', 'A2A_ROLE',
                'A2A_LAUNCH', 'A2A_LAUNCHES', 'CODEX_THREAD_ID',
                'GIT_CONFIG_COUNT', 'GIT_CONFIG_KEY_0', 'GIT_CONFIG_VALUE_0')
FILES = [
    'archive_t081_capability_run02.py', 'capability_command_paths.py', 'capability_poll_evidence.py',
    'check_t081_capability_paths.py', 'check_t081_capability_run03.py', 'collect_t081_closeout.py',
    'commit_t081_closeout.py', 'diagnose_t081_capability_run02.py', 'prepare_t081_capability.py',
    'prepare_t081_capability_run02.ts', 'prepare_t081_capability_run03.ts', 'prepare_t081_capability_run04.ts',
    'prepare_t081_mutants.py', 'run_t081_bad_worker_suite.py', 'run_t081_capability_turn.py',
    'run_t081_cas_suite.py', 't081_capability_audit.ts', 't081_capability_home.py', 't081_capability_materials.ts',
    'test_bad_worker_e2e.py', 'test_t081_archive_ownership.py', 'test_t081_capability_audit.ts', 'test_t081_cleanup.py',
    'test_t081_commit.py',
]


def description(path):
    prefix = str(BASE.relative_to(ROOT)) + '/'
    if not path.startswith(prefix):
        return False
    relative = Path(path[len(prefix):])
    return relative.suffix == '.md' and (len(relative.parts) == 1 or
        (relative.name == 'RESULTS.md' and relative.parts[0].startswith(('full-', 'closeout-'))))


def whitespace_paths(names):
    checked = [name for name in names if name.startswith(CODE_PREFIXES) or description(name)]
    checked_set = set(checked)
    return checked, [name for name in names if name not in checked_set]


def commit_identity(env):
    missing = [name for name in REQUIRED_ENV if not env.get(name)]
    if missing:
        raise RuntimeError('缺少提交身份环境变量；先由主控按 s14-t081 记录设置：' + ', '.join(missing))
    if env['A2A_LAUNCH'] != LAUNCH or env['CODEX_THREAD_ID'] != NATIVE:
        raise RuntimeError('A2A_LAUNCH / CODEX_THREAD_ID 必须匹配主控 #179 指定的 s14-t081 启动和原生会话。')
    ledger = Path(env['A2A_LAUNCHES'])
    if not ledger.is_absolute() or ledger.resolve() != LEDGER:
        raise RuntimeError('A2A_LAUNCHES 不是已核对的主仓绝对记录路径。')
    sys.path.insert(0, str(ROOT / 'scripts'))
    from launch_records import find_launch
    from record_io import read_records
    row = find_launch(read_records(ledger), LAUNCH)
    if (row.get('agent'), row.get('task'), row.get('role'), row.get('model'), row.get('effort')) != ('s14-t081', 'T-081', 'worker', 'gpt-6.1-sol', 'xhigh') or Path(row['cwd']).resolve() != ROOT:
        raise RuntimeError('启动记录的 agent/task/role/model/effort/cwd 不符。')
    for field in ('project', 'task', 'attempt', 'session', 'role'):
        if env['A2A_' + field.upper()] != row[field]:
            raise RuntimeError('环境变量与启动记录不符：A2A_' + field.upper())
    if row['native_session'] not in ('unknown', NATIVE):
        raise RuntimeError('启动记录已经绑定其他原生会话，不提交。')
    hooks = LEDGER.parent.parent / 'scripts/git-hooks'
    if (env['GIT_CONFIG_COUNT'], env['GIT_CONFIG_KEY_0']) != ('1', 'core.hooksPath') or Path(env['GIT_CONFIG_VALUE_0']).resolve() != hooks:
        raise RuntimeError('会话 Git hook 环境不符：GIT_CONFIG_COUNT / GIT_CONFIG_KEY_0 / GIT_CONFIG_VALUE_0')
    return {'agent': row['agent'], 'launch': LAUNCH, 'native_session': NATIVE, 'native_source': '主控 #179 / Herdr 记录',
            'ledger': str(ledger), 'native_binding_in_ledger': row['native_session'],
            'task': row['task'], 'attempt': row['attempt'], 'session': row['session'], 'role': row['role'], 'hooks': str(hooks)}


def path_parts(directory, names):
    directory.mkdir()
    parts = []
    for index in range(0, len(names), 1000):
        path = directory / ('%04d.json' % (index // 1000 + 1))
        path.write_text(json.dumps(names[index:index + 1000], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if path.stat().st_size > 5_000_000:
            raise RuntimeError('清单分卷超过 5 MB，停止报告。')
        parts.append(str(path))
    return parts


def execute(args, out, log):
    identity = commit_identity(os.environ)
    readonly_env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}
    def run(argv):
        result = log.run(argv, cwd=ROOT, env=os.environ, timeout=240)
        if result.returncode:
            raise RuntimeError('命令失败；保留 index 和日志，不 reset 或绕过 hook：' + str(result.evidence['id']))
        return result.stdout.strip()
    def names(*argv):
        result = subprocess.run(['git', *argv], cwd=ROOT, env=readonly_env, capture_output=True, check=True)
        return [name.decode('utf-8') for name in result.stdout.split(b'\0') if name]
    def index_entries():
        rows = names('ls-files', '--stage', '-z')
        entries = {}
        for row in rows:
            header, _, name = row.partition('\t')
            mode, oid, stage = header.split()
            if stage != '0':
                raise RuntimeError('index 含未合并冲突；不 add 或重置。')
            entries[name] = (mode, oid)
        return entries
    prefixes = ['workbench/tests/' + name for name in FILES]
    evidence_prefix = str(BASE.relative_to(ROOT)) + '/'
    def scoped(staged):
        unknown = [name for name in staged if name not in prefixes and not name.startswith(evidence_prefix)]
        if unknown:
            raise RuntimeError('index 含其他任务内容，不提交或重置：' + repr(unknown[:20]))
    if run(['git', 'branch', '--show-current']) != 'exec/t081' or run(['git', 'rev-parse', 'HEAD']) != HEAD:
        raise RuntimeError('分支/起点改变，停止重新核对。')
    before = index_entries()
    initial = names('diff', '--cached', '--name-only', '-z')
    scoped(initial)
    _, initial_raw = whitespace_paths(initial)
    changed = names('diff', '--name-only', '-z')
    if any(name not in prefixes and not description(name) for name in changed):
        raise RuntimeError('原始证据或其他任务有未暂存修改；不覆盖既有 index：' + repr(changed[:20]))
    cas = json.loads((BASE / 'cas-01/run.json').read_text(encoding='utf-8'))
    if cas.get('status') != 'PASS' or [step['label'] for step in cas.get('steps', [])] != ['red', 'green'] or not all(step['valid_evidence'] for step in cas['steps']):
        raise RuntimeError('CAS 补证尚未通过，不提交。')
    cleanup = json.loads((BASE / 'home-cleanup-01.json').read_text(encoding='utf-8'))
    if cleanup.get('status') != 'PASS' or cleanup.get('removed') is not True or cleanup.get('check_only') is not False or len(cleanup.get('checked_runs', [])) != 4 or Path('/private/tmp/t081-capability-01/codex-home').exists():
        raise RuntimeError('缺少四轮核对后的实际 home 删除收据，不提交。')
    final = json.loads((BASE / 'closeout-final-01/run.json').read_text(encoding='utf-8'))
    if final['cas']['status'] != 'PASS' or final['home_cleanup']['status'] != 'PASS' or final['consumed_real_turns'] != 3:
        raise RuntimeError('既有 closeout-final-01 未确认 CAS/清理/3 回合，不重复生成或覆盖。')
    run([sys.executable, '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', ROOT])
    count, total = 0, 0
    for path in BASE.rglob('*'):
        if path.is_symlink() or path.name in ('.git', 'auth.json'):
            raise RuntimeError('证据中出现链接、内嵌 Git 或凭据文件；不暂存：' + str(path))
        if path.is_file():
            if path.stat().st_size > 5_000_000:
                raise RuntimeError('单文件超过 5 MB，停止报告：' + str(path))
            count += 1; total += path.stat().st_size
    fresh = names('ls-files', '--others', '--exclude-standard', '-z', '--', *prefixes, str(BASE.relative_to(ROOT)))
    delta = sorted(set(changed + fresh))
    if any(not (ROOT / name).is_file() for name in delta):
        raise RuntimeError('待暂存路径含删除/非文件，不自动处理。')
    inventory = {'evidence_files': count, 'evidence_bytes': total, 'test_files': prefixes, 'identity': identity,
                 'initial_staged_files': len(initial), 'delta_add_files': len(delta),
                 'delta_manifest': path_parts(out / 'delta-add', delta), 'check_only': args.check_only,
                 'unresolved': ['6a 完全缺尾注裁定', '6e 追溯字段一致性裁定'],
                 'preserves_raw_failures': True, 'no_submit_or_push': True}
    if not args.check_only:
        for number in range(0, len(delta), 1000):
            batch = delta[number:number + 1000]
            pathspec = out / ('add-%04d.paths' % (number // 1000 + 1))
            pathspec.write_bytes(b''.join(name.encode('utf-8') + b'\0' for name in batch))
            run(['git', 'add', '--pathspec-from-file=' + str(pathspec), '--pathspec-file-nul'])
    after = index_entries()
    # Compare existing Git object identities instead of rereading 350 MB of raw
    # bytes. A change stops the commit; no new content fingerprint is computed.
    if any(after.get(name) != before[name] for name in initial_raw):
        raise RuntimeError('既有原始证据的 index mode/object 发生变化，停止，不 reset。')
    staged = names('diff', '--cached', '--name-only', '-z')
    scoped(staged)
    checked, excluded = whitespace_paths(staged)
    inventory.update(checked_paths=checked, excluded_raw_count=len(excluded),
                     excluded_raw_manifest=path_parts(out / 'whitespace-excluded', excluded),
                     exclusion_scope='仅免除原始证据空白检查；仍保留并提交 staged 原件',
                     preexisting_raw_index_entries_preserved=len(initial_raw),
                     reused_closeout=str(BASE / 'closeout-final-01/run.json'))
    (out / 'scope.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: inventory[key] for key in ('initial_staged_files', 'delta_add_files', 'excluded_raw_count', 'check_only')}, ensure_ascii=False), flush=True)
    if not checked:
        raise RuntimeError('空白检查范围为空，不能当作通过。')
    run(['git', 'diff', '--cached', '--check', '--', *checked])
    if args.check_only:
        return {'status': 'PASS', 'scope': '只读核对当前 index、身份、原件排除和增量暂存计划；未 add/commit',
                'identity': identity, 'receipt': str(out / 'scope.json'), 'check_only': True}
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
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log-dir', type=Path, default=Path('/private/tmp/t081-closeout-commit-02'))
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    out = args.log_dir.resolve()
    if not args.check_only and (ROOT == out or ROOT in out.parents):
        raise RuntimeError('真实提交日志须放工作树之外，避免边写边暂存。')
    out.mkdir(exist_ok=False)
    log = CommandLog(out)
    try:
        result = execute(args, out, log)
    except Exception as error:
        import traceback
        result = {'status': 'INCOMPLETE', 'error': repr(error), 'traceback': traceback.format_exc(),
                  'preserved_index_no_reset': True}
    (out / 'run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
