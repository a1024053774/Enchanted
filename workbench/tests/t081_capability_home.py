"""主控批准后单独运行：生成或删除固定夹具的隔离 CODEX_HOME；不启动 CLI。"""
import argparse
import json
import os
from pathlib import Path
import shutil


FIXTURE = Path('/private/tmp/t081-capability-01')
HOME_PATH = FIXTURE / 'codex-home'
EVIDENCE = Path(__file__).resolve().parents[2] / 'evidence/2026-10-14-batch14/T-081'


def inspect_cleanup(fixture, evidence):
    """核对四次运行的端点、所有权及实际 PID 退出；从不停止进程。"""
    checked, runs = set(), []
    for number in range(1, 5):
        run_root = fixture if number == 1 else fixture / ('run-%02d' % number)
        state = run_root / 'state'
        for path in (state / 'daemon.pid', state / 'control.sock'):
            if path.exists() or path.is_symlink():
                raise RuntimeError('后台端点仍存在；保留 home：' + str(path))
        ownership = json.loads((run_root / 'owned-pids.json').read_text(encoding='utf-8'))
        result = json.loads((evidence / ('capability-run-%02d' % number) / 'run.json').read_text(encoding='utf-8'))
        if (ownership.get('root') != str(fixture) or not ownership.get('pids')
                or ownership.get('all_confirmed_exited') is not True
                or result.get('processes_stopped') is not True
                or result.get('pid_exit', {}).get('all_confirmed_exited') is not True
                or sorted(ownership['pids']) != sorted(result['pid_exit']['pids'])):
            raise RuntimeError('PID 所有权或退出证据不符；保留 home：' + str(run_root))
        if number > 1 and ownership.get('run_root') != str(run_root):
            raise RuntimeError('PID 记录 run_root 不符；保留 home。')
        for pid in ownership['pids']:
            if type(pid) is not int or pid <= 1:
                raise RuntimeError('PID 记录无效；保留 home。')
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                checked.add(pid)
            else:
                raise RuntimeError('记录 PID 仍存在（也可能已复用）；不停止它，保留 home：' + str(pid))
        runs.append({'run': number, 'root': str(run_root), 'pids': ownership['pids'],
                     'registry': str(run_root / 'owned-pids.json'), 'exit_report': str(evidence / ('capability-run-%02d' % number) / 'run.json')})
    return {'checked_runs': runs, 'checked_exited_pids': sorted(checked)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'cleanup'])
    parser.add_argument('--approval-ref', required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true', help='只读核对 cleanup 前提，不删除 home')
    args = parser.parse_args()
    if not args.approval_ref.strip():
        raise RuntimeError('需要主控本次批准的位置引用。')
    if FIXTURE.is_symlink() or FIXTURE.resolve(strict=True) != FIXTURE:
        raise RuntimeError('夹具根不符合固定路径。')
    marker = json.loads((FIXTURE / 'PREPARED.json').read_text(encoding='utf-8'))
    if marker['task'] != 'T-081' or marker['root'] != str(FIXTURE):
        raise RuntimeError('夹具身份不符。')
    receipt = args.receipt.resolve()
    if receipt.exists() or FIXTURE == receipt or FIXTURE in receipt.parents:
        raise RuntimeError('收据必须是夹具之外的新文件，不可把凭据目录当证据。')
    record = {'task': 'T-081', 'action': args.action, 'approval_ref': args.approval_ref,
              'home': str(HOME_PATH), 'credential_contents_recorded': False,
              'hooks_installed': False, 'real_codex_turns_started_by_this_script': 0}
    if args.action == 'prepare':
        if args.check_only:
            raise RuntimeError('--check-only 只用于 cleanup。')
        HOME_PATH.mkdir(mode=0o700, exist_ok=False)
        source = Path.home() / '.codex/auth.json'
        shutil.copyfile(source, HOME_PATH / 'auth.json')
        (HOME_PATH / 'auth.json').chmod(0o600)
        config = '[projects.' + json.dumps(str(FIXTURE)) + ']\ntrust_level = "trusted"\n'
        with (HOME_PATH / 'config.toml').open('x', encoding='utf-8') as stream:
            stream.write(config)
        (HOME_PATH / 'rules').mkdir(mode=0o700)
        rules = ('prefix_rule(pattern=["git", "add"], decision="allow")\n'
                 'prefix_rule(pattern=["git", "commit"], decision="allow")\n')
        with (HOME_PATH / 'rules/default.rules').open('x', encoding='utf-8') as stream:
            stream.write(rules)
        record.update(status='PASS', scope='仅隔离 home 准备', config=config, rules=rules,
                      copied_names=['auth.json'], generated_names=['config.toml', 'rules/default.rules'])
    else:
        if HOME_PATH.is_symlink() or HOME_PATH.resolve(strict=True) != HOME_PATH:
            raise RuntimeError('隔离 home 路径不符，拒绝删除。')
        record.update(inspect_cleanup(FIXTURE, EVIDENCE))
        protected = {path.name: path.lstat().st_ino for path in FIXTURE.iterdir() if path != HOME_PATH}
        if not args.check_only:
            shutil.rmtree(HOME_PATH)
        if protected != {path.name: path.lstat().st_ino for path in FIXTURE.iterdir() if path != HOME_PATH}:
            raise RuntimeError('非 home 的夹具目录发生变化，停止报告。')
        record.update(status='PASS', scope='仅四次运行已停止的隔离 home 清理' if not args.check_only else '只读 cleanup 前提检查；没有删除 home',
                      removed=not HOME_PATH.exists(), check_only=args.check_only,
                      protected_fixture_entries=list(protected), repositories_preserved=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': record['status'], 'scope': record['scope'], 'receipt': str(receipt)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
