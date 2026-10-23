"""T-146 自然退出的最小真实入口探针（不替代 Electron e2e）。
失败方式：CLI /exit 后 zsh 仍活着，sidebar/Reflect 仍报告 idle/running；
用关终端或门禁回收冒充 CLI 退出；嵌套 Bash 沙箱失败污染退出观察。
模型仅返回一句话，CLI 不调用 Bash；/exit 由真实终端输入入口发送。
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from scripted_claude import Fixture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--revision')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据'
    report = dict(status='INCOMPLETE', argv=sys.argv)
    fixture = None
    try:
        fixture = Fixture('t146-exit-', lambda body: ('no-tools', [], '等待下一条指令。'), revision=args.revision)
        report['fixture'] = str(fixture.dir)
        fixture.start(shutil.which('claude') or str(Path.home() / '.local/bin/claude'), {'README.md': 'fixture\n', 'check.py': 'pass\n'})
        fixture.card('T-exit', 'result.txt', 'check.py')
        started = fixture.request('dispatch', fixture.terminal, task='T-exit', runtimeMode='workspace-write')
        assert started.get('ok'), started
        launch = started['attempt']['runtime_identity']['launch']
        thread = started['attempt']['thread_id']
        report['before'] = fixture.wait('CLI 完成真实回合', lambda: fixture.api.main >= 1 and next((a for a in fixture.request('sidebar_snapshot')['agents']
            if a['id'] == launch and a['state'] == 'idle'), None), 60)
        pane = fixture.request('pane_status', thread=thread)
        window = fixture.request('window_open', fixture.operator, launch=launch, task='demo+T-exit')
        assert window.get('ok'), window
        result = fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()), data='/exit\r')
        assert result.get('ok'), result

        def exited():
            pid = str(pane['shell_pid'])
            shell = subprocess.run(['/bin/ps', '-p', pid, '-o', 'comm='], capture_output=True, text=True, timeout=10)
            children = subprocess.run(['/usr/bin/pgrep', '-P', pid], capture_output=True, text=True, timeout=10)
            assert 'Operation not permitted' not in shell.stderr + children.stderr, 'OS process probe denied by sandbox'
            return dict(shell_pid=int(pid), shell=shell.stdout.strip(), child_pids=children.stdout.strip()) if (
                shell.returncode == 0 and shell.stdout.strip().endswith('zsh') and children.returncode == 1) else None

        report['os_observation'] = fixture.wait('只有 zsh，CLI 已退出', exited, 40)
        report['sidebar'] = fixture.request('sidebar_snapshot')
        report['reflect'] = fixture.request('reflect_tree', project='demo')
        report['pane'] = fixture.request('pane_status', thread=thread)
        sidebar = next((a['state'] for a in report['sidebar']['agents'] if a['id'] == launch), 'MISSING')
        reflect = next((n['state'] for n in report['reflect']['nodes'] if n['launch'] == launch), 'MISSING')
        assert sidebar in ('MISSING', 'ended') and reflect == 'ended', f'CLI exited with live zsh: sidebar={sidebar}, reflect={reflect}'
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        if fixture:
            report['api_snapshot'] = fixture.api.snapshot()
        raise
    finally:
        try:
            if fixture:
                fixture.stop()
        finally:
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            with args.summary.open('x', encoding='utf-8') as output:
                output.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
