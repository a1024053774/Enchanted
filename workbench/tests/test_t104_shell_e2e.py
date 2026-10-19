"""真实 CLI/daemon/socket/zsh 合同；无 Electron、供应商 CLI 或模型。

仅操作自建的隔离 HOME、数据库和进程。--revision 在隔离源码上运行同一
场景，--leaky-mutant 故意恢复请求载荷日志，验证隐私断言能拒绝已知坏行为。
原始现场归档到调用者指定的外置盘目录；摘要文件不覆盖。
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
import uuid


ROOT = Path(__file__).resolve().parents[2]


def wait_for(read, description, seconds=10):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = read()
        if value:
            return value
        time.sleep(.05)
    raise AssertionError(description)


def inventory(path):
    files = [p for p in path.rglob('*') if p.is_file() or p.is_symlink()]
    return len(files), sum(p.lstat().st_size for p in files)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--leaky-mutant', action='store_true')
    args = parser.parse_args()
    assert os.path.ismount('/Volumes/WD-Elements'), '外置盘未挂载，不运行或归档'
    assert str(args.archive.resolve()).startswith('/Volumes/WD-Elements/'), '归档必须在外置盘'
    assert not args.archive.exists() and not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t104-', dir='/private/tmp')).resolve()
    state = fixture / 'state'
    state.mkdir()
    home = fixture / 'home'
    home.mkdir()
    (home / '.zprofile').write_text('export T104_LOGIN_RC=loaded\n', encoding='utf-8')
    (home / '.zshrc').write_text("PS1='T104% '\n", encoding='utf-8')
    cwd = fixture / '项目 alpha space'
    cwd.mkdir()
    other_cwd = fixture / 'beta'
    other_cwd.mkdir()
    source = ROOT
    if args.revision or args.leaky_mutant:
        source = fixture / 'source'
        if args.revision:
            files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', args.revision,
                                             'workbench/src'], cwd=ROOT, text=True).splitlines()
            for name in files:
                target = source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(subprocess.check_output(['git', 'show', f'{args.revision}:{name}'], cwd=ROOT))
        else:
            shutil.copytree(ROOT / 'workbench/src', source / 'workbench/src')
            daemon = source / 'workbench/src/daemon.ts'
            text = daemon.read_text(encoding='utf-8')
            assert 'input: eventInput(envelope.input)' in text
            daemon.write_text(text.replace('input: eventInput(envelope.input)', 'input: envelope.input'), encoding='utf-8')
        # This is an isolated source fixture, never a build-output directory.
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
    cli = source / 'workbench/src/gates/cli.ts'
    credential = None
    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'LC_ALL', 'TMPDIR'] if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color')
    report = dict(status='INCOMPLETE', argv=sys.argv, source=str(source), revision=args.revision,
                  mutant=args.leaky_mutant, fixture=str(fixture), checks=[], commands=[], cleanup=[])
    nonce = 'private-' + uuid.uuid4().hex
    shells = []
    windows = []
    processes = set()
    running = False
    checkpoint = 'setup'

    def run_cli(command, *arguments, ok=True):
        argv = ['node', str(cli), '--state', str(state), command, *arguments]
        run = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=30)
        report['commands'].append(dict(argv=argv, exit=run.returncode, stdout=run.stdout, stderr=run.stderr))
        assert run.returncode == 0 if ok else run.returncode != 0, f'{command}: {run.stderr or run.stdout}'
        return json.loads(run.stdout)

    def request(command, identity=None, **data):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(15)
            connection.connect(str(state / 'control.sock'))
            payload = dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)
            connection.sendall((json.dumps(payload) + '\n').encode())
            response = b''
            while b'\n' not in response:
                part = connection.recv(65536)
                assert part, 'daemon 在回执前断开'
                response += part
        reply = json.loads(response.split(b'\n', 1)[0])
        # Request content is supplied by the test, not extracted from the product.
        # Raw input is intentionally kept only in this private fixture transcript.
        with (fixture / 'transport.jsonl').open('a', encoding='utf-8') as log:
            safe = dict(payload, identity={'kind': identity.get('kind')} if identity else None)
            logged_reply = {k: v for k, v in reply.items() if k != 'identity'}
            log.write(json.dumps(dict(request=safe, reply=logged_reply), ensure_ascii=False) + '\n')
        return reply

    def operator():
        return json.loads(credential.read_text(encoding='utf-8'))

    def start(number):
        nonlocal credential, running
        credential = fixture / f'operator-{number}.json'
        env['A2A_OPERATOR_CREDENTIAL'] = str(credential)
        result = run_cli('daemon_start')
        running = True
        report.setdefault('daemons', []).append(result['pid'])
        info = subprocess.check_output(['/bin/ps', '-p', str(result['pid']), '-o', 'pid=,pgid='], text=True)
        pid, pgid = map(int, info.split())
        assert pid == pgid and pgid != os.getpgrp(), '后台必须脱离调用者进程组'
        wait_for(lambda: request('pane_layout').get('recovering') is False, '后台恢复未结束')

    def process_state(pid):
        run = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,stat=,command='],
                             capture_output=True, text=True, timeout=5)
        assert run.returncode in (0, 1) and not run.stderr, '独立进程查询失败'
        report['cleanup'].append(dict(pid=pid, exit=run.returncode, output=run.stdout))
        # A zombie has exited, although the parent has not reaped it yet.
        return not run.stdout.strip() or run.stdout.split()[1].startswith('Z')

    def stop():
        nonlocal running
        if not running:
            return
        result = run_cli('daemon_stop')
        wait_for(lambda: not (state / 'control.sock').exists() and process_state(result['pid']), '后台退出未确认')
        running = False

    def open_shell(project, directory):
        record = run_cli('shell_start', '--project', project, '--cwd', str(directory))['launch']
        shells.append(record)
        assert record['role'] == 'shell' and record['project'] == project
        assert record['task'] is None and record['attempt'] is None and record['session'] is None and record['fence'] is None
        assert record['shell'] == '/bin/zsh' and record['shell_argv'] == ['-l', '-i']
        assert record['env'] == {'A2A_PROJECT': project}
        opened = request('window_open', operator(), launch=record['id'], project=project)
        assert opened['ok'], opened
        window = dict(identity=opened['identity'], seq=0, record=record)
        windows.append(window)
        return window

    def send(window, text, **extra):
        window['seq'] += 1
        return request('window_input', window['identity'], sequence=window['seq'], request_id=str(uuid.uuid4()), data=text, **extra)

    def output_lines(window):
        result = request('pane_output', launch=window['record']['id'], offset=0)
        assert result['ok'], result
        import base64
        text = base64.b64decode(result['data_base64']).decode('utf-8')
        return re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))', '', text).splitlines()

    try:
        # Upgrade an existing append-only launch table through the real daemon.
        with sqlite3.connect(state / 'state.sqlite3') as db:
            db.execute('CREATE TABLE launch_records (id TEXT PRIMARY KEY, task TEXT NOT NULL, attempt TEXT, data TEXT NOT NULL)')
            old = dict(id='legacy', task='legacy-task', attempt=None, thread='legacy-thread', role='controller', execution_state='prepared')
            db.execute('INSERT INTO launch_records VALUES (?,?,?,?)', ('legacy', 'legacy-task', None, json.dumps(old)))
        checkpoint = 'daemon_start'
        start(1)
        checkpoint = 'shell_start'
        first = open_shell('t104-alpha', cwd)
        checkpoint = 'shell_io'
        second = open_shell('t104-beta', other_cwd)
        marker = 'stdout-' + uuid.uuid4().hex
        assert send(first, f"printf '\\n%s\\n' '{marker}'; pwd; print -r -- LOGIN=$options[login],INTERACTIVE=$options[interactive],RC=$T104_LOGIN_RC; /usr/bin/env | /usr/bin/grep '^A2A_'\r")['ok']
        lines = wait_for(lambda: (lambda rows: rows if str(cwd) in rows and 'LOGIN=on,INTERACTIVE=on,RC=loaded' in rows else None)(output_lines(first)), 'zsh 未执行 pwd 或登录配置')
        assert marker in lines
        assert [line for line in lines if line.startswith('A2A_')] == ['A2A_PROJECT=t104-alpha']
        assert request('pane_layout', project='t104-alpha')['panes'][0]['launch'] == first['record']['id']
        assert len(request('pane_layout', project='t104-alpha')['panes']) == 1
        report['checks'].append('真实 zsh 登录、交互、echo/pwd、项目环境和项目隔离')
        assert request('shell_start', project='t104-alpha', cwd=str(cwd))['error'] == 'caller_identity_required'
        assert request('shell_start', first['identity'], project='t104-alpha', cwd=str(cwd))['error'] == 'window_command_forbidden'
        assert request('window_open', operator(), launch=first['record']['id'], project='t104-beta')['error'] == 'launch_project_mismatch'
        assert request('workbench_snapshot', launch=first['record']['id'], project='t104-beta')['error'] == 'launch_project_mismatch'
        assert request('pane_dispatch', operator(), thread=first['record']['thread'], body='不要进入 agent 队列')['error'] == 'agent_pane_required'
        assert request('signal', {'launch': first['record']['id'], 'token': ''}, launch=first['record']['id'], raw_stdin='{}')['error'] == 'agent_pane_required'
        assert request('shell_close', operator(), launch='legacy')['error'] == 'shell_required'
        report['checks'].append('匿名、窗口越权、跨项目、agent 派发与身份均拒绝')
        assert send(first, f"printf '\\n%s\\n' '{nonce}'\r")['ok']
        wait_for(lambda: nonce in output_lines(first), '输入没有送到真实 PTY')
        assert send(first, nonce, encoding='invalid')['error'] == 'invalid_terminal_input'
        assert request('window_input', dict(first['identity'], token='invalid'), data=nonce)['error'] == 'invalid_window_identity'
        first['seq'] += 1
        observation = request('window_observation', first['identity'], sequence=first['seq'], request_id=str(uuid.uuid4()),
                              type='focus-mode-intercept', raw_sequence='\x1b[?1004h'+nonce)
        assert observation['ok'] and observation['written'] is False, '终端控制观察不得使普通 shell 输入失败'
        checkpoint = 'close_children'
        assert send(first, "/bin/sleep 300 &\r")['ok']
        time.sleep(.1)
        assert send(first, "/bin/sleep 300\r")['ok']
        tree = wait_for(lambda: (lambda r: r if r.get('ok') and len(r['processes']) >= 3 else None)(request('pane_process_info', thread=first['record']['thread'])), '前台和后台子进程没有启动')
        pids = [p['pid'] for p in tree['processes']]
        processes.update(pids)
        assert len([p for p in tree['processes'] if p['command'] == '/bin/sleep']) == 2
        report['process_tree'] = tree
        run_cli('shell_close', '--launch', first['record']['id'])
        wait_for(lambda: all(process_state(pid) for pid in pids), '关闭后仍有活动子进程')
        assert request('pane_status', thread=first['record']['thread'])['lifecycle'] == 'ended'
        assert send(first, nonce)['error'] == 'pane_unavailable'
        assert request('pane_layout', project='t104-alpha')['panes'] == []
        assert request('pane_layout', project='t104-alpha')['saved'] is True
        assert request('pane_status', thread=second['record']['thread'])['lifecycle'] == 'running'
        report['checks'].append('显式关闭结束 shell、前台子进程和后台子进程，其他项目保持运行')
        checkpoint = 'restart'
        second_pid = request('pane_status', thread=second['record']['thread'])['shell_pid']
        processes.add(second_pid)
        stop()
        wait_for(lambda: process_state(second_pid), 'daemon 停止后 shell 没退出')
        start(2)
        snapshot = request('workbench_snapshot', launch=second['record']['id'], project='t104-beta')
        assert snapshot['ok'] and snapshot['task'] is None and snapshot['pane']['lifecycle'] == 'ended'
        assert snapshot['pane']['shell_pid'] is None and snapshot['pane']['historical'] is True
        assert request('pane_layout', project='t104-beta')['panes'][0]['launch'] == second['record']['id']
        assert send(second, nonce)['error'] == 'invalid_window_identity'
        report['checks'].append('后台重启保留打开集，shell 结束且不续接，旧窗口身份失效')
        checkpoint = 'privacy'
        events = request('orchestration_events')['events']
        assert nonce not in json.dumps(events, ensure_ascii=False), 'shell 输入内容泄漏进事件流'
        assert marker not in json.dumps(events, ensure_ascii=False), 'shell 输入命令泄漏进事件流'
        for shell in shells:
            owned = [e for e in events if e.get('launch') == shell['id']]
            assert len([e for e in owned if e['type'] == 'shell_created' and e['data']['role'] == 'shell']) == 1
            assert len([e for e in owned if e['type'] == 'shell_closed' and e['data']['role'] == 'shell']) == 1
            assert not any(e['type'] in ['pane_restore_pending', 'dispatch_queued', 'terminal_input_write_intent'] for e in owned)
        with sqlite3.connect(state / 'state.sqlite3') as db:
            assert db.execute('SELECT count(*) FROM user_inputs').fetchone()[0] == 0
            assert db.execute('SELECT count(*) FROM user_input_ingress').fetchone()[0] == 0
            assert db.execute('SELECT data FROM launch_records WHERE id=?', ('legacy',)).fetchone()[0] == json.dumps(old)
            assert db.execute("SELECT count(*) FROM dispatch_records").fetchone()[0] == 0
            try:
                db.execute("UPDATE launch_records SET task='changed' WHERE id='legacy'")
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError('迁移丢失追加式约束')
        report['checks'].append('创建/关闭事件存在；成功、拒绝、过期身份输入均无正文记录；无 agent 输入或人工介入')
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc(), checkpoint=checkpoint)
    finally:
        try:
            stop()
            for pid in processes:
                wait_for(lambda: process_state(pid), f'测试进程 {pid} 退出未确认')
            report['cleanup_complete'] = True
        except Exception as error:
            report.update(status='INCOMPLETE', cleanup_error=str(error), cleanup_complete=False)
        if report.get('cleanup_complete'):
            for file in fixture.glob('operator-*.json'):
                file.unlink()  # Only this test's credentials; never archived.
        (fixture / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # Preserve all failure evidence. A live/unknown fixture is kept in place.
        if report.get('cleanup_complete'):
            args.archive.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(fixture, args.archive, symlinks=True)
            assert inventory(fixture) == inventory(args.archive), '归档文件数或字节数不一致，保留原目录'
            count, size = inventory(fixture)
            report['archive'] = dict(original=str(fixture), archive=str(args.archive), files=count, bytes=size,
                                     replay=' '.join(sys.argv))
            shutil.rmtree(fixture)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open('x', encoding='utf-8') as summary:
            json.dump(report, summary, ensure_ascii=False, indent=2)
            summary.write('\n')
    print(json.dumps(dict(status=report['status'], checkpoint=report.get('checkpoint'), error=report.get('error'), cleanup_complete=report.get('cleanup_complete')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
