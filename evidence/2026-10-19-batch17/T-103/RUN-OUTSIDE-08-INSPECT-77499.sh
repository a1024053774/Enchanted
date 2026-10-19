#!/bin/bash
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t103
# 只读核对第六轮未确认退出的后台；不发信号，不改原现场。
/usr/bin/python3 -B - <<'PY'
import datetime, json, subprocess
from pathlib import Path
pid = 77499
argv = ['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,ppid=,uid=,lstart=,command=']
result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', timeout=5)
absent = result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip()
report = {'status': 'PASS' if absent else 'INCOMPLETE',
          'scope': '仅核对 PID 77499 当前是否存在；不代表原 E2E 或所有后台清理通过',
          'time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'argv': argv, 'exit': result.returncode,
          'stdout': result.stdout, 'stderr': result.stderr, 'signal_sent': False,
          'original_run': 'run-20261019T060557Z',
          'expected_command_fragments': [
              '/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-103/baseline-20261019T060557Z/workbench/src/daemon.ts',
              '/private/tmp/a2at103-stani09q/red-state']}
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
path = Path('evidence/2026-10-19-batch17/T-103') / ('inspect-77499-' + stamp + '.json')
with path.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if absent else 1)
PY
