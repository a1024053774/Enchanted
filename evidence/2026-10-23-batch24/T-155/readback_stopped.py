"""停止后复制 DB，仅在副本里检查完整性并读取事实；不驱动产品流程。"""
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2]
ROOTS = [Path('/private/tmp') / name for name in (
    't155-dogfood-lv2rm2nt', 't155-dogfood-ohzs_78v')]
OUT = Path('/private/tmp/t155-final-readback')


def main():
    for root in ROOTS:
        if (root / 'state/daemon.pid').exists() or (root / 'state/control.sock').exists():
            raise RuntimeError('后台尚未确认停止：' + str(root))
    processes = subprocess.run(['/bin/ps', '-axo', 'pid=,command='],
                               capture_output=True, text=True, check=True).stdout
    for line in processes.splitlines():
        if any(str(root) in line for root in ROOTS):
            raise RuntimeError('仍有实例进程：' + line)
    sys.path.insert(0, str(SOURCE / 'workbench/tests'))
    from fixture_artifacts import archive_stopped_database
    OUT.mkdir(mode=0o700, exist_ok=False)
    summaries = []
    for root in ROOTS:
        target = OUT / root.name / 'state.sqlite3'
        copied = archive_stopped_database(root / 'state', target)
        with closing(sqlite3.connect('file:' + str(target) + '?mode=ro', uri=True)) as db:
            def rows(table):
                return [json.loads(r[0]) for r in db.execute('SELECT data FROM ' + table)]
            inputs = rows('user_inputs')
            events = list(db.execute('SELECT seq,time,type,data FROM orchestration_events'))
            task_events = list(db.execute('SELECT seq,time,type,details FROM events'))
            roles = [{'seq': r[0], 'time': r[1], 'type': r[2]} for r in events
                     if r[2].startswith('role_request_')]
            blocked = [{'source': table, 'seq': r[0], 'time': r[1], 'type': r[2],
                        'details': json.loads(r[3])}
                       for table, stream in [('orchestration_events', events), ('events', task_events)]
                       for r in stream if 'worker_not_active' in r[3]]
            tasks = [{k: v.get(k) for k in ('task_id', 'state', 'fence', 'spec_rev',
                      'card_version', 'candidate_commit', 'current_attempt', 'integration_intent', 'quality')}
                     for v in rows('tasks')]
            reviews = rows('verifications')
            summaries.append({'root': str(root), 'database_copy': copied,
                'user_inputs': {'count': len(inputs), 'forms': dict(Counter(v['form'] for v in inputs)),
                    'entries': [{'id': v['id'], 'form': v['form'], 'channel': v['channel'],
                                 'created_at': v['created_at']} for v in inputs]},
                'role_events': roles, 'worker_not_active_events': blocked, 'tasks': tasks,
                'launch_roles': dict(Counter(v['role'] for v in rows('launch_records'))),
                'verification_rows': len(reviews),
                'main': subprocess.run(['git', '-C', str(root / 'demo-repo'), 'rev-parse', 'main'],
                                       capture_output=True, text=True, check=True).stdout.strip()})
    result = {'phase': 'after-parent-STOP-all', 'method': '原 DB/WAL 只复制；副本转 DELETE 并 integrity_check，再 mode=ro 查询；不改产品状态',
              'command': 'python3 evidence/2026-10-23-batch24/T-155/readback_stopped.py',
              'instances': summaries}
    with (HERE / 'stopped-readback.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'instances': len(summaries), 'output': str(OUT)}))


if __name__ == '__main__':
    main()
