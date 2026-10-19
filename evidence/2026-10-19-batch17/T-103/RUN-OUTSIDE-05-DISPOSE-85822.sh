#!/bin/bash
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t103
python3 - <<'PY'
import datetime, json, os, shlex, signal, subprocess, time
from pathlib import Path

disk = Path('/Volumes/WD-Elements')
assert disk.is_mount(), '外置盘未挂载，停止；不回退内置盘'
root = disk / 'a2a-evidence/2026-10-19-batch17/T-103'
out = root / ('dispose-85822-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
out.mkdir()
run = root / 'run-20261019T051645Z'
baseline = root / 'baseline-20261019T051645Z'
state = '/private/tmp/a2at103-_o2_ksvs/red-state'
ui = '/private/tmp/a2at103-_o2_ksvs/red-fixed-task-ui'
task = 'task-0-0-e6ddc9'
entry = str(run / 'red-fixed-task/start-entry/observe.mjs')
expected_child = [str(baseline / 'workbench/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron'),
                  entry, '--state', state, '--task', task, '--user-data', ui]
expected_parent = [str(baseline / 'workbench/app/start.mjs'), '--build',
                   str(run / 'red-fixed-task/start-entry'), '--state', state, '--user-data', ui, '--task', task]
record = {'status': 'INCOMPLETE', 'scope': '仅核对并结束主控 #10 指定的 Electron PID 85822；不发进程组信号、不结束后台、不删夹具',
          'pid': 85822, 'expected_ppid': 85798, 'expected_child_argv': expected_child,
          'expected_parent_argv_after_node': expected_parent, 'signal': None}
env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}

def save(name, value):
    (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def observe(pid):
    result = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,ppid=,uid=,stat=,lstart=,command='],
                            text=True, capture_output=True, timeout=5, env=env)
    if result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
        return None
    assert result.returncode == 0 and not result.stderr.strip(), 'ps 核对失败，拒绝发信号'
    fields = result.stdout.strip().split(maxsplit=9)
    assert len(fields) == 10 and int(fields[0]) == pid, 'ps 身份字段不完整'
    return {'pid': int(fields[0]), 'ppid': int(fields[1]), 'uid': int(fields[2]), 'stat': fields[3],
            'started': ' '.join(fields[4:9]), 'command': fields[9]}

def identity(value):
    return None if value is None else {key: value[key] for key in ['pid', 'ppid', 'uid', 'started', 'command']}

def children():
    result = subprocess.run(['/bin/ps', '-ax', '-o', 'pid=,ppid='], text=True, capture_output=True, timeout=5, env=env)
    assert result.returncode == 0 and not result.stderr.strip(), '无法核对子进程，拒绝发信号'
    return [int(fields[0]) for line in result.stdout.splitlines()
            if len(fields := line.split()) == 2 and int(fields[1]) == 85822]

try:
    child = observe(85822)
    if child is None:
        record.update(status='PASS', action='指定 PID 已不存在，未发信号')
    else:
        parent = observe(85798)
        record.update(before=child, parent=parent)
        assert child['ppid'] == 85798 and child['uid'] == os.getuid(), '子进程所属父进程或用户不符'
        assert shlex.split(child['command']) == expected_child, 'Electron 完整命令不符'
        assert parent and parent['uid'] == os.getuid(), '启动器身份无法确认'
        parent_argv = shlex.split(parent['command'])
        assert Path(parent_argv[0]).name == 'node' and parent_argv[1:] == expected_parent, '启动器完整命令不符'
        assert not children(), '该 Electron 已有子进程，现场与挂起描述不同，停止处置'
        save('verified-owner.json', record)
        assert identity(observe(85822)) == identity(child) and identity(observe(85798)) == identity(parent), 'PID、启动时间或完整命令已变化'
        assert not children(), '发信号前出现子进程，停止处置'
        os.kill(85822, signal.SIGTERM)
        record['signal'] = 'SIGTERM'
        deadline = time.monotonic() + 5
        while True:
            current = observe(85822)
            if current is None or identity(current) != identity(child):
                record.update(status='PASS', action='已核对原 Electron 退出；未向其他进程发信号', after=current)
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('SIGTERM 后 5 秒仍在运行；保留现场，不自动 SIGKILL')
            time.sleep(.1)
except Exception as error:
    record['error'] = repr(error)
finally:
    save('result.json', record)
    Path('evidence/2026-10-19-batch17/T-103').joinpath(out.name + '-summary.json').write_text(
        json.dumps({**record, 'archive': str(out)}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    Path('evidence/2026-10-19-batch17/T-103').joinpath(out.name + '.archive.json').write_text(
        json.dumps({'original': '本次只读进程快照；无原目录删除', 'archive': str(out),
                    'bytes': sum(path.stat().st_size for path in out.iterdir() if path.is_file()),
                    'replay': 'bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-05-DISPOSE-85822.sh'},
                   ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False, indent=2))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
PY
