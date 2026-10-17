#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
base = Path('evidence/2026-10-11-batch13/T-078')
before = '09b58c69202c922fff3f760e9bbd5acaef528f72'

def git(*args):
    return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()

assert git('rev-parse', 'HEAD') == before and git('branch', '--show-current') == 'exec/t078'
assert os.environ.get('CODEX_THREAD_ID') == '01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK') == 'T-078-1' and os.environ.get('A2A_ROLE') == 'worker'
assert not git('diff', '--cached', '--name-only')
allow = json.loads((base / '09b-run-04-allowlist.json').read_bytes())
for row in subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode().split('\0'):
    if row:
        name = row[3:]
        assert any(name == p or name.startswith(p + '/') for p in allow), ('Unowned work; no mutation', name)
assert all(Path(p).exists() for p in allow)
for name in ['09b-run-04-source-freeze.json', '09b-run-04-commit', '09b-executable-materials-04']:
    assert not (base / name).exists(), ('Existing output; preserve it, no retry', name)
old = json.loads((base / '09b-stage-a-03/result.json').read_bytes())
assert old['status'] == 'INCOMPLETE' and old['spawned'] is True
assert 'invalid_task_card' in old.get('error', '')
preflight = json.loads((base / '09b-card-preflight-runner-06/results.json').read_bytes())
assert preflight['status'] == 'PASS' and preflight['spawned'] is False and preflight['root_created'] is False
archive_helper = json.loads((base / 'cleanup-archive-helper-test-06.json').read_bytes())
assert archive_helper['status'] == 'PASS'
ownership = json.loads((base / '09b-run-04-ownership-preflight-09.json').read_bytes())
assert ownership['status'] == 'PASS' and ownership['unowned'] == []
dry_cleanup = json.loads((base / '09b-stage-a-03-cleanup-dry-run/result.json').read_bytes())
assert dry_cleanup['status'] == 'PASS' and dry_cleanup['dry_run'] is True and dry_cleanup['signals_sent'] == [] and dry_cleanup['root_removed'] is False
real_cleanup = json.loads((base / '09b-stage-a-03-cleanup/result.json').read_bytes())
assert real_cleanup['status'] == 'BLOCKED' and real_cleanup['dry_run'] is False and real_cleanup['root_removed'] is False
assert real_cleanup['signals_sent'] == [{'pid': 62217, 'signal': 'SIGTERM'}] and 'API exit unconfirmed' in real_cleanup.get('error', '')
red_stop = json.loads((base / '09b-fake-api-stop-red-07/result.json').read_bytes())
green_stop = json.loads((base / '09b-fake-api-stop-green-08/result.json').read_bytes())
assert red_stop['status'] == 'PASS' and red_stop['verdict'] == 'RED_TIMEOUT'
assert green_stop['status'] == 'PASS' and green_stop['verdict'] == 'GREEN_EXIT_WITHIN_2S'
recovery_dry = json.loads((base / '09b-stage-a-03-recovery-dry-run/result.json').read_bytes())
assert recovery_dry['status'] == 'PASS' and recovery_dry['dry_run'] is True and recovery_dry['signals_sent'] == [] and recovery_dry['root_removed'] is False
recovery = json.loads((base / '09b-stage-a-03-recovery/result.json').read_bytes())
assert recovery['status'] == 'PASS' and recovery['dry_run'] is False and recovery['byte_readback'] == 'PASS' and recovery['root_removed'] is True
assert recovery['signals_sent'] == [{'pid': 62217, 'signal': 'SIGKILL'}, {'pid': 62218, 'signal': 'SIGKILL'}]
subprocess.run(['git', 'diff', '--check'], check=True)
subprocess.run(['git', 'add', '--', *allow], check=True)
subprocess.run(['git', 'diff', '--cached', '--stat'], check=True)
subprocess.run(['git', 'commit', '-m', 'fix(T-078): preflight stage A task card before runtime spawn'], check=True)
revision = git('rev-parse', 'HEAD')
with (base / '09b-run-04-source-freeze.json').open('x', encoding='utf-8') as f:
    json.dump({'revision': revision, 'parent_revision': before, 'old_red_preserved': True,
               'card_preflight': 'taskCards.validateTaskCard before fake API/daemon/target spawn',
               'fake_api_stop': 'SystemExit from signal handler; red timeout and green <=2s evidence',
               'recovery': 'SIGKILL owner-bound recovery after preserved SIGTERM deadlock',
               'paths_deny': [], 'oracle_paths': 'gate-protected exact paths', 'launch': 'NO_GO'}, f, ensure_ascii=False, indent=2)
    f.write('\n')
run = base / '09b-run-04-commit'; run.mkdir()
prepare = [sys.executable, '-B', str((base / 'prepare-09b-executable.py').resolve()), '--label', '09b-executable-materials-04']
with (run / 'prepare.stdout.bin').open('xb') as stdout, (run / 'prepare.stderr.bin').open('xb') as stderr:
    result = subprocess.run(prepare, stdout=stdout, stderr=stderr)
(run / 'prepare.command.json').write_text(json.dumps({'argv': prepare, 'revision': revision, 'exit_code': result.returncode}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert result.returncode == 0, 'Preserve failed package/commit; no retry'
facts = json.loads((base / '09b-executable-materials-04/static-check.json').read_bytes())
assert facts['status'] == 'PASS' and facts['launch_status'] == 'NO_GO' and facts['revision'] == revision
with (base / 'RESULTS.md').open('a', encoding='utf-8') as f:
    f.write('\n## 阶段 A 卡片预检、假 API 停止修复与 materials-04 冻结\n\n#195 的 `09b-stage-a-03` 与 #197/#198 cleanup BLOCKED 现场均保留：坏卡红态未 dispatch/claim/target；首个假 API 的 SIGTERM 死锁由 sample 证据确认，恢复脚本先 dry-run 再对 62217/62218 各一次经身份核对的 SIGKILL，归档逐成员读回 PASS 后删除 root。假 API 停止测试先取当前实现 SIGTERM 两秒超时红态，再以 signal handler 抛 `SystemExit` 取得两秒内退出绿态。runner 仍先经真实 `taskCards.validateTaskCard` 预检，空 `paths.deny` 由 `oracle_paths` 承担 oracle 保护；materials-04 静态冻结继续 `launch_status=NO_GO`，本轮不启动阶段 A、CLI、目标或供应商模型。\n')
second = [str(base / '09b-executable-materials-04'), str(run), str(base / '09b-run-04-source-freeze.json'), str(base / 'RESULTS.md')]
subprocess.run(['git', 'add', '--', *second], check=True)
subprocess.run(['git', 'diff', '--cached', '--stat'], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): freeze stage A card preflight and materials 04'], check=True)
assert not git('status', '--porcelain')
print(json.dumps({'status': 'PASS', 'source_revision': revision,
                  'materials_revision': git('rev-parse', 'HEAD'),
                  'packet': str(base / '09b-executable-materials-04'),
                  'launch': 'NO_GO'}, ensure_ascii=False))
PY
