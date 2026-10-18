#!/bin/sh
# 主控运行：10 次独立首屏启动，不向 pane 写探测命令；只关闭本次自建 pane。
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t094
python3 -B evidence/2026-10-16-batch16/T-094/probe-start.py \
  --label busy-02 --count 10 --cwd "$PWD" --launcher scripts/launch-worker \
  --expect-diagnostics --expect-busy-foreground
python3 -B - <<'PY'
import json
from pathlib import Path
import shutil
disk = Path('/Volumes/WD-Elements')
if not disk.is_mount():
    raise SystemExit('外置盘未挂载')
base = disk / 'a2a-evidence/2026-10-16-batch16/T-094'
root = base / 'busy-02'
run = json.loads((root / 'run.json').read_text(encoding='utf-8'))
violations = []
for attempt in run['attempts']:
    row = attempt['launch_record']
    calls = [json.loads(s) for s in (root / ('attempt-%02d' % attempt['number']) / 'herdr.jsonl').read_text(encoding='utf-8').splitlines()]
    if row['shell_ready_policy'] != dict(stable_ms=1500, sample_interval_ms=100, timeout_ms=30000):
        violations.append('就绪判据未固定')
    if attempt['launch']['returncode'] == 0:
        start = next(c for c in calls if c['argv'][:2] == ['agent', 'start'])
        idle_since = None
        for call in calls[:calls.index(start)]:
            if call['argv'][:2] != ['pane', 'process-info']:
                continue
            info = json.loads(call['stdout'])['result']['process_info']
            processes = info.get('foreground_processes', [])
            if (info.get('shell_pid') and info.get('foreground_process_group_id') == info['shell_pid']
                and len(processes) == 1 and processes[0]['pid'] == info['shell_pid']
                and processes[0]['name'].lstrip('-') == 'zsh'):
                if idle_since is None:
                    idle_since = call['finished_unix_ns']
            else:
                idle_since = None
        if idle_since is None or start['started_unix_ns'] - idle_since < 1500000000:
            violations.append('start 前未取得 1500ms shell 独占采样：' + str(attempt['number']))
    print(json.dumps(dict(number=attempt['number'], pane=row['pane'], exit_code=attempt['launch']['returncode'],
                         error_code=row.get('error_code'), busy_foreground=row.get('busy_foreground'),
                         shell_foreground=row.get('shell_foreground')), ensure_ascii=False))
def size(path):
    files = [p for p in path.rglob('*') if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)
archives = [('（probe-start.py 直接写入外置盘）', root, 'busy-02')]
for source, label in ((Path('/tmp/t094-stable-details-01'), 'stable-details-01'),
                      (Path('/tmp/t094-init-gap-details-01'), 'init-gap-details-01')):
    target = base / label
    shutil.copytree(source, target)
    if size(source) != size(target):
        raise SystemExit('归档计数或字节数不一致，保留两边原件')
    archives.append((str(source), target, label))
for original, archive, label in archives:
    count, byte_count = size(archive)
    manifest = dict(original=original, archive=str(archive), files=count, bytes=byte_count,
                    replay='sh evidence/2026-10-16-batch16/T-094/outside-busy-02.sh（重放换用新标签与归档目录）')
    with (Path('evidence/2026-10-16-batch16/T-094') / (label + '.archive.json')).open('x', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')
if violations:
    raise SystemExit('\n'.join(violations))
print(json.dumps(dict(successful_starts=sum(a['launch']['returncode'] == 0 for a in run['attempts']),
                      failed_starts=sum(a['launch']['returncode'] != 0 for a in run['attempts']),
                      readiness_check='PASS', model_turns=run['model_turns']), ensure_ascii=False))
PY
