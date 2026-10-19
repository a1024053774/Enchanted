#!/bin/bash
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t103
python3 - <<'PY'
import datetime, json, os, shlex, signal, subprocess, time
from pathlib import Path

disk = Path('/Volumes/WD-Elements')
assert disk.is_mount(), '外置盘未挂载，停止；不回退内置盘'
root = disk / 'a2a-evidence/2026-10-19-batch17/T-103'
run = root / 'run-20261019T052842Z'
launch = json.loads((run / 'red-no-task/launch.json').read_text(encoding='utf-8'))
assert launch['pid'] == 75497 and '--task' not in launch['argv']
out = root / ('dispose-75497-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
out.mkdir()
record = {'status': 'INCOMPLETE', 'scope': '仅核对并结束主控 #11 点名的孤儿 Electron 75497；不发进程组信号、不结束后台、不删除夹具',
          'pid': 75497, 'expected_ppid': 1, 'expected_argv': launch['argv'], 'signal': None}
env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}

def observe():
    result = subprocess.run(['/bin/ps', '-ww', '-p', '75497', '-o', 'pid=,ppid=,uid=,lstart=,command='],
                            env=env, text=True, capture_output=True, timeout=5)
    if result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
        return None
    assert result.returncode == 0 and not result.stderr.strip(), 'ps 核对失败，拒绝发信号'
    fields = result.stdout.strip().split(maxsplit=8)
    assert len(fields) == 9 and int(fields[0]) == 75497
    return {'pid': 75497, 'ppid': int(fields[1]), 'uid': int(fields[2]),
            'started': ' '.join(fields[3:8]), 'command': fields[8]}

try:
    owner = observe()
    if owner is None:
        record.update(status='PASS', action='指定 PID 已不存在，未发信号')
    else:
        record['before'] = owner
        assert owner['ppid'] == 1 and owner['uid'] == os.getuid(), '父进程或用户不符，停止'
        assert shlex.split(owner['command']) == launch['argv'], '完整命令与失败启动记录不符，停止'
        (out / 'verified-owner.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        assert observe() == owner, 'PID、启动时间、父进程或命令改变，停止'
        os.kill(75497, signal.SIGTERM)
        record['signal'] = 'SIGTERM'
        deadline = time.monotonic() + 5
        while True:
            current = observe()
            if current is None or current != owner:
                record.update(status='PASS', action='已核对原 Electron 退出；未向其他进程发信号', after=current)
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('SIGTERM 后仍未退出，保留现场，不自动 SIGKILL')
            time.sleep(.1)
except Exception as error:
    record['error'] = repr(error)
finally:
    (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    dest = Path('evidence/2026-10-19-batch17/T-103')
    (dest / (out.name + '-summary.json')).write_text(json.dumps({**record, 'archive': str(out)}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (dest / (out.name + '.archive.json')).write_text(json.dumps({'original': '本次只读进程快照，无原目录删除',
        'archive': str(out), 'bytes': sum(path.stat().st_size for path in out.iterdir() if path.is_file()),
        'replay': 'bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-07-DISPOSE-75497.sh'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False, indent=2))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
PY
