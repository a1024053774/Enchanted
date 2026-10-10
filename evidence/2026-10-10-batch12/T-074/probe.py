#!/usr/bin/env python3
"""Set up and control one isolated native TUI probe; never retry inputs."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def launch(label):
    if not Path('/Volumes/WD-Elements').is_mount():
        raise SystemExit('外置盘未挂载；停止，不回退')
    out = BASE / label
    out.mkdir()  # Existing evidence labels are rejected.
    temp = Path(tempfile.mkdtemp(prefix='a2a-t074-', dir='/tmp'))
    fixture = temp / 'fixture'
    fixture.mkdir()
    home = temp / 'codex-home'
    home.mkdir(mode=0o700)
    shell_home = temp / 'shell-home'
    shell_home.mkdir()
    subprocess.run(['git', 'init', '-q', str(fixture)], check=True)
    subprocess.run(['git', '-C', str(fixture), '-c', 'user.name=T074 Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--allow-empty', '-qm', 'T074 fixture'], check=True)
    shutil.copyfile(Path.home() / '.codex/auth.json', home / 'auth.json')
    (home / 'auth.json').chmod(0o600)
    (home / 'config.toml').write_text(f'[projects.{json.dumps(str(fixture))}]\ntrust_level = "trusted"\n', encoding='utf-8')
    (home / 'rules').mkdir()
    (home / 'rules/default.rules').write_text('prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n', encoding='utf-8')
    codex = Path(shutil.which('codex')).resolve()
    node_pty = ROOT.parent / 'synara/apps/server/node_modules/node-pty'
    if subprocess.check_output([str(codex), '--version'], text=True).strip() != 'codex-cli 0.162.1':
        raise SystemExit('Fixed Codex version differs; stop before real launch')
    argv = [str(codex), '--no-daemon', '--no-alt-screen', '-C', str(fixture),
            '-m', 'gpt-6.1-sol', '-c', 'model_reasoning_effort="xhigh"',
            '-c', 'service_tier="fast"', '-c', 'check_for_update_on_startup=false',
            '-s', 'workspace-write', '-a', 'on-request',
            '-c', 'notify=' + json.dumps(['python3', str(BASE / 'notify.py'), str(out / 'notify.jsonl')]),
            '-c', 'tui.notifications=["approval-requested"]',
            '-c', 'tui.notification_method="osc9"', '-c', 'tui.notification_condition="always"',
            '只回复「T074就绪」，不要调用工具。']
    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TMPDIR'] if key in os.environ}
    env.update(HOME=str(shell_home), ZDOTDIR=str(shell_home), CODEX_HOME=str(home),
               SHELL='/bin/zsh', TERM='xterm-256color', COLORTERM='truecolor',
               LANG='en_US.UTF-8', PYTHONDONTWRITEBYTECODE='1')
    manifest = dict(created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                    task_card='T-074-1', ready_rev=1,
                    starting_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                    codex_version=subprocess.check_output([str(codex), '--version'], text=True).strip(),
                    node_version=subprocess.check_output(['node', '--version'], text=True).strip(),
                    node_pty_version=json.loads((node_pty / 'package.json').read_text(encoding='utf-8'))['version'],
                    node_pty_path=str(node_pty), temp_root=str(temp), fixture=str(fixture),
                    output=str(out), codex_home=str(home), socket=str(temp / 'control.sock'), codex_argv=argv, env=env)
    write_json(out / 'launch.json', manifest)
    log = open(out / 'host.log', 'ab')
    shutil.copyfile(BASE / 'pty-host.cjs', out / 'pty-host.cjs')
    process = subprocess.Popen(['node', str(out / 'pty-host.cjs'), str(out / 'launch.json')],
                               cwd=fixture, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                               start_new_session=True)
    write_json(out / 'host-process.json', dict(pid=process.pid, start_new_session=True))
    print(json.dumps(dict(label=label, host_pid=process.pid, temp_root=str(temp))))

def control(label, request):
    manifest = json.loads((BASE / label / 'launch.json').read_text(encoding='utf-8'))
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(manifest['socket'])
        client.sendall((json.dumps(request, ensure_ascii=False) + '\n').encode('utf-8'))
        data = b''
        while b'\n' not in data:
            chunk = client.recv(65536)
            if not chunk:
                break
            data += chunk
    return json.loads(data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['launch', 'status', 'request'])
    parser.add_argument('label')
    parser.add_argument('--json')
    args = parser.parse_args()
    if args.operation == 'launch':
        launch(args.label)
    else:
        request = {'op': 'status'} if args.operation == 'status' else json.loads(args.json)
        print(json.dumps(control(args.label, request), ensure_ascii=False, indent=2))
