"""只核对已批准项目主控的真实角色来源；不运行 Electron 或真实模型。

失败方式：角色批准未生效；侧栏与窗格快照未使用同一个 launch；
把侧栏的 controller 投影误当成窗格快照的 launch.role。
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from scripted_claude import Fixture

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--summary', required=True, type=Path)
args = parser.parse_args()
assert not args.summary.exists(), '保留已有证据，使用新路径'
report = dict(status='INCOMPLETE', purpose='区分侧栏角色与真实窗格快照角色；不替代 Electron 分屏验收',
              argv=sys.argv, code_version=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              model_calls=0)
fixture = None
try:
    fixture = Fixture('t159-role-probe-', lambda _: (_ for _ in ()).throw(AssertionError('禁止模型请求')))
    report['fixture'] = str(fixture.dir)
    # The daemon receives a valid executable but starts no worker or provider CLI.
    fixture.start('/usr/bin/true', {'README.md': 'T159 controller scope probe\n'})
    who = fixture.request('terminal_whoami', fixture.terminal)
    snapshot = fixture.request('workbench_snapshot', project='demo', launch=fixture.terminal_launch)
    sidebar = fixture.request('sidebar_snapshot')
    entry = next(a for a in sidebar['agents'] if a['id'] == fixture.terminal_launch)
    report['observed'] = dict(launch=fixture.terminal_launch, approved_role=who.get('role'),
        sidebar={k: entry.get(k) for k in ['role', 'preset', 'terminal', 'project', 'task']},
        pane_snapshot=dict(task=snapshot.get('task'), role=snapshot.get('launch', {}).get('role'),
                           project=snapshot.get('launch', {}).get('project')))
    assert who.get('ok') and who.get('role') == 'executor', who
    assert snapshot.get('ok') and snapshot['task'] is None, snapshot
    assert entry['role'] == 'controller' and snapshot['launch']['role'] == 'shell', report['observed']
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = type(error).__name__ + ': ' + str(error)
finally:
    if fixture:
        try:
            fixture.stop()
        except Exception as error:
            report['cleanup_error'] = str(error)
            report['status'] = 'INCOMPLETE'
    with args.summary.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
