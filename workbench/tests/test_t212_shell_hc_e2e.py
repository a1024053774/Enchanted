"""T-212：真实后台、项目终端、窗口输入和后台重启。

失败方式（写断言之前列出）：
1. 后台停止时杀掉项目终端，或恢复时另起程序冒充原程序。
2. 重启遗漏已有的数百行中文历史，或错过后台离线期间的输出。
3. attach 不回 CREDIT，超过 256 KiB 后输出停住。
4. DATA 改写中文、粘贴、Esc、Ctrl-C；RESIZE 没到真实终端。
5. hc 与 viewer 重复应答终端查询；OSC 7501 不再透传或恢复时遗漏。
6. core 继承 agent 标记、用户 hc 配置或错误的 XDG 目录；碰到用户 core。
7. 终端令牌/socket 在重启后失效，a2a 包装命令不能用。
8. closeShell 没结束终端及其子进程；测试后台留在调用者进程组。
9. core 运行中崩溃后，侧栏忽略 failed，普通终端仍为空闲、已批准主控仍在运行。
10. 后台接回崩溃后被收养的终端，却漏记 shell_screen_inexact 或返回 exact。
11. 崩溃场景错误撤销仍活着的终端身份，或遗留本测试的 core、holder、shell。
12. hc 接回时的大尺寸重绘回放给小尺寸 xterm，光标被夹到最后一行，覆盖历史。
13. 连续改变布局时每次都取完整重绘，trace 追加成批重复历史。
14. 合并尺寸变化时丢掉最终尺寸，或还在等待时提前显示旧重绘。
15. 改尺寸后继续输出时，旧块与新重绘交错导致缺行、多行或顺序变化。
16. 项目终端的隐藏/重放处理误用于受管窗格，改变尺寸就闪“恢复中”。
17. 重绘边界沿用半个 UTF-8 字符或未结束的 OSC carry，吞掉新 viewer 的报告。

编号及存活 oracle 来自夹具程序自己写的文件和独立 ps，不导入产品实现。
"""
import argparse
import base64
import json
import os
import pwd
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import signal
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from types import SimpleNamespace
from hc_evidence import assert_public_evidence, private_tokens, user_core_snapshot

ROOT = Path(__file__).resolve().parents[2]
RAW_PROGRAM = r'''
import json,os,pathlib,re,select,termios,time,tty
old=termios.tcgetattr(0)
try:
 tty.setraw(0)
 os.write(1,b'\x1b[c')
 answer=b''
 until=time.monotonic()+.5
 while time.monotonic()<until:
  if select.select([0],[],[],.05)[0]: answer+=os.read(0,4096)
 pathlib.Path('query.json').write_text(json.dumps({'hex':answer.hex(),'answers':len(re.findall(rb'\x1b\[\?[0-9;]+c',answer))}))
 pathlib.Path('raw-ready').write_text('ready')
 received=b''
 while not received.endswith(b'\x03'):
  if not select.select([0],[],[],15)[0]: raise RuntimeError('input deadline')
  received+=os.read(0,4096)
 size=os.get_terminal_size(0)
 pathlib.Path('input.json').write_text(json.dumps({'hex':received.hex(),'size':[size.columns,size.lines]}))
finally:
 termios.tcsetattr(0,termios.TCSANOW,old)
'''


def stop_private_core(fixture, env):
    state = fixture / 'state'
    manifest = state / 'hc-runtime.json'
    if not manifest.exists():
        return None
    identity = json.loads(manifest.read_text(encoding='utf-8'))
    assert identity['session'].startswith('enchanted-') and identity['session'] != 'default'
    binary = state / 'hc/bin/herdr-core'
    if not binary.exists():
        return None
    private = dict(env, HC_SESSION=identity['session'], HC_SOCKET=identity['socket'],
                   XDG_STATE_HOME=str(state / 'hc/state'), XDG_CONFIG_HOME=str(state / 'hc/config'))
    run = subprocess.run([str(binary), 'server', 'stop'], env=private, capture_output=True, text=True, timeout=20,
                         start_new_session=True)
    return dict(exit=run.returncode, stdout=run.stdout, stderr=run.stderr, session=identity['session'])


def wait_for(probe, message, seconds=15):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = probe()
        if value:
            return value
        time.sleep(.05)
    raise AssertionError(message)


def core_crash_scenario(args):
    args.output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='t212-crash-', dir='/private/tmp'))
    state, home = fixture / 'state', fixture / 'home'
    state.mkdir(); home.mkdir()
    (home / '.zshrc').write_text("PS1='CRASH% '\n", encoding='utf-8')
    env = {key: os.environ[key] for key in ('PATH', 'LANG') if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TMPDIR='/private/tmp', T212_CORE_STARTER_MARKER='initial-daemon')
    report = dict(status='INCOMPLETE', command=[sys.executable, *sys.argv], fixture=str(fixture),
        checks={}, commands=[], real_model_calls=0,
        controller_fixture='终端身份经真实 role_request/decide/confirm 入口；不启动供应商 CLI。实际 Claude/UI 旅程另引用主控 t133。')
    before = user_core_snapshot()
    running, launches, owned_pids, tokens = False, [], set(), set()
    holder_pids = set()
    manifest = None

    def cli(*arguments):
        argv = ['node', str(ROOT / 'workbench/src/gates/cli.ts'), '--state', str(state), *arguments]
        run = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=40, start_new_session=True)
        report['commands'].append(dict(argv=argv, exit=run.returncode, stdout=run.stdout, stderr=run.stderr))
        assert run.returncode == 0, run.stdout or run.stderr
        return json.loads(run.stdout)

    def request(command, identity=None, **fields):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(20); connection.connect(str(state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), identity=identity,
                input=dict(command=command, **fields))) + '\n').encode())
            raw = b''
            while b'\n' not in raw:
                part = connection.recv(65536); assert part, '后台在回执前断开'; raw += part
        return json.loads(raw.split(b'\n')[0])

    def start():
        nonlocal running, manifest
        env['A2A_OPERATOR_CREDENTIAL'] = str(fixture / ('operator-' + uuid.uuid4().hex + '.json'))
        started = cli('daemon_start'); running = True
        pid, pgid = map(int, subprocess.check_output(['/bin/ps', '-p', str(started['pid']), '-o', 'pid=,pgid='], text=True).split())
        assert pid == pgid and pgid != os.getpgrp()
        wait_for(lambda: request('pane_layout').get('recovering') is False, '后台恢复未完成')
        manifest = json.loads((state / 'hc-runtime.json').read_text(encoding='utf-8'))
        assert manifest['session'].startswith('enchanted-') and manifest['session'] != 'default'

    def stop():
        nonlocal running
        if running:
            cli('daemon_stop'); wait_for(lambda: not (state / 'control.sock').exists(), '后台未退出'); running = False

    def hc(*arguments):
        private = dict(env, HC_SESSION=manifest['session'], HC_SOCKET=manifest['socket'],
            XDG_STATE_HOME=str(state / 'hc/state'), XDG_CONFIG_HOME=str(state / 'hc/config'))
        argv = [str(state / 'hc/bin/herdr-core'), '--json', *arguments]
        run = subprocess.run(argv, env=private, capture_output=True, text=True, timeout=20, start_new_session=True)
        report['commands'].append(dict(argv=argv, exit=run.returncode, stdout=run.stdout, stderr=run.stderr))
        assert run.returncode == 0, run.stderr
        return json.loads(run.stdout)

    def core_status():
        status = hc('server', 'status')
        owned_pids.add(status['pid'])
        for holder in status['holders']:
            owned_pids.add(holder['pid']); holder_pids.add(holder['pid'])
        return status

    def exited(pid):
        run = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True, timeout=5)
        assert run.returncode in (0, 1) and not run.stderr
        return not run.stdout.strip() or run.stdout.strip().startswith('Z')

    try:
        start()
        plain = cli('shell_start', '--project', 'crash', '--cwd', str(home))['launch']; launches.append(plain)
        controller = cli('shell_start', '--project', 'crash', '--cwd', str(home))['launch']; launches.append(controller)
        for launch in launches:
            owned_pids.add(request('pane_status', thread=launch['thread'])['shell_pid'])
        # Read this disposable terminal's bearer only from its private registry; never print or copy it.
        registry = state / 'hc/state/herdr-core' / manifest['session'] / 'terminals.json'
        terminals = json.loads(registry.read_text(encoding='utf-8'))['terminals'].values()
        token = next(t['restart_env']['A2A_TERMINAL_TOKEN'] for t in terminals
            if t['labels'].get('enchanted_launch') == controller['id'])
        terminal_identity = dict(kind='terminal', launch=controller['id'], token=token)
        operator = json.loads(Path(env['A2A_OPERATOR_CREDENTIAL']).read_text(encoding='utf-8'))
        with socket.socket(socket.AF_UNIX) as asker:
            asker.settimeout(20); asker.connect(str(state / 'control.sock'))
            asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), identity=terminal_identity, input=dict(
                command='role_request', role='executor', cli='claude', native_session=str(uuid.uuid4()),
                native_home=str(home / '.claude'), wait_seconds=60))) + '\n').encode())
            pending = wait_for(lambda: [r for r in request('sidebar_snapshot')['role_requests']
                if r['launch'] == controller['id']], '角色申请未出现')[0]
            assert request('role_request_decide', operator, role_request=pending['id'], approved=True)['ok']
            reply = b''
            while b'\n' not in reply:
                part = asker.recv(65536); assert part; reply += part
            granted = json.loads(reply.split(b'\n')[0]); assert granted['ok'], granted
            confirmed = request('role_request_confirm', terminal_identity, role_request=pending['id'])
            assert confirmed['ok'], confirmed
        initial = request('sidebar_snapshot')
        assert next(t for t in initial['terminals'] if t['id'] == plain['id'])['state'] == 'idle'
        assert next(a for a in initial['agents'] if a['id'] == controller['id'])['state'] == 'running'
        old_core = core_status()
        command = subprocess.check_output(['/bin/ps', '-p', str(old_core['pid']), '-o', 'comm='], text=True).strip()
        assert Path(command).resolve() == (state / 'hc/bin/herdr-core').resolve()
        os.kill(old_core['pid'], signal.SIGKILL)
        wait_for(lambda: all((request('pane_status', thread=l['thread']).get('failed') or '').startswith('hc_connection_lost')
            for l in launches), '未记录 core 连接丢失')
        lost_status = {l['id']: request('pane_status', thread=l['thread']) for l in launches}
        lost_sidebar = request('sidebar_snapshot')
        plain_lost = next(t for t in lost_sidebar['terminals'] if t['id'] == plain['id'])
        controller_lost = next(a for a in lost_sidebar['agents'] if a['id'] == controller['id'])
        report['after_crash'] = dict(statuses=lost_status, ordinary=plain_lost, controller=controller_lost)
        report['checks'].update(failed_recorded=all((s['failed'] or '').startswith('hc_connection_lost') for s in lost_status.values()),
            ordinary_unknown=plain_lost['state'] == 'unknown', controller_unknown=controller_lost['state'] == 'unknown',
            approved_role_retained=request('terminal_whoami', terminal_identity).get('role') == 'executor')
        # Continue even on the expected sidebar red, so the same run also observes inexact recovery.
        stop(); env['T212_CORE_STARTER_MARKER'] = 'restarted-daemon'; start()
        new_core = core_status(); assert new_core['pid'] != old_core['pid']
        events = request('orchestration_events')['events']
        recovered = {l['id']: request('pane_status', thread=l['thread']) for l in launches}
        for launch in launches:
            identity = launch['id']
            report['checks']['inexact_event_' + identity] = any(e['type'] == 'shell_screen_inexact'
                and e.get('launch') == identity and e['data']['screen'] == 'inexact' for e in events)
            report['checks']['inexact_status_' + identity] = recovered[identity].get('screen') == 'inexact'
            report['checks']['inexact_reattached_' + identity] = any(e['type'] == 'shell_reattached'
                and e.get('launch') == identity and e['data']['screen'] == 'inexact' for e in events)
        whoami = request('terminal_whoami', terminal_identity)
        report['checks']['role_retained_after_restart'] = whoami.get('role') == 'executor'
        report['checks']['same_shell_pids'] = all(recovered[l['id']]['shell_pid'] == lost_status[l['id']]['shell_pid'] for l in launches)
        report['after_restart'] = dict(statuses=recovered, events=[e for e in events if e['type'] in ('shell_screen_inexact', 'shell_reattached')])
        env_file = fixture / 'new-core-environment.json'
        program = "import os,json,pathlib;pathlib.Path(" + repr(str(env_file)) + ").write_text(json.dumps({'starter':os.environ.get('T212_CORE_STARTER_MARKER'),'xdg_state':os.environ.get('XDG_STATE_HOME')}))"
        probe = hc('run', '--bg', '--no-parent', '--no-notify', '/usr/bin/python3', '-c', program)
        wait_for(lambda: env_file.exists(), '新 core 环境探针未完成')
        observed = json.loads(env_file.read_text(encoding='utf-8'))
        # T-228: whichever comes first brings the core back, the restarted daemon or the holder (about 3 s, with
        # the first daemon's controlled environment); both are ours. A core with a terminal's marker is not.
        assert observed['starter'] in ('restarted-daemon', 'initial-daemon') and observed['xdg_state'] == str(state / 'hc/state')
        report['core_restart'] = dict(old_pid=old_core['pid'], new_pid=new_core['pid'],
            initiated_by='重启的编排后台' if observed['starter'] == 'restarted-daemon' else 'holder（沿用首个后台的受控环境）',
            observed_environment=observed, probe_terminal=probe['address'], agent_first_restart='未知；T-220 范围，本场景未测试抢先启动')
        core_status()  # Include every holder created by the environment probe in cleanup.
        assert all(report['checks'].values()), 'core 崩溃投影/恢复断言失败：' + str([k for k,v in report['checks'].items() if not v])
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        tokens = private_tokens(state)
        cleanup_errors = []
        if running:
            for launch in launches:
                try: cli('shell_close', '--launch', launch['id'])
                except Exception as error: cleanup_errors.append(str(error))
        try: stop()
        except Exception as error: cleanup_errors.append(str(error))
        try:
            result = stop_private_core(fixture, env)
            report['core_cleanup'] = result
            assert result is None or result['exit'] == 0, result
            wait_for(lambda: all(exited(pid) for pid in owned_pids), '测试 core/holder/shell 仍存活', seconds=20)
            sockets = [] if not manifest else list(Path(manifest['socket']).parent.glob('*.sock'))
            assert not sockets, '私有 holder socket 残留'
        except Exception as error: cleanup_errors.append(str(error))
        report['cleanup'] = dict(status='INCOMPLETE' if cleanup_errors else 'PASS', errors=cleanup_errors,
            owned_pids=sorted(owned_pids), holder_pids=sorted(holder_pids))
        if cleanup_errors: report['status'] = 'INCOMPLETE'
        after = user_core_snapshot(); report['user_core'] = dict(before=before, after=after, unchanged=before == after)
        if before != after: report['status'] = 'NO_GO'
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        report['evidence_boundary'] = assert_public_evidence(args.output, tokens)
        if report['status'] == 'PASS' and report['cleanup']['status'] == 'PASS':
            shutil.rmtree(fixture)
            report['successful_fixture_removed'] = not fixture.exists()
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'PASS' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mutant', choices=['forget-token', 'forget-socket', 'no-reset'])
    parser.add_argument('--electron-screen', action='store_true')
    parser.add_argument('--mismatched-screen', action='store_true', help='重启前把 hc 设为 193×120，真实窗格仍自行拟合')
    parser.add_argument('--resize-burst', action='store_true', help='真实 Electron 连续改变布局 24 次，再核对重绘次数和完整输出')
    parser.add_argument('--core-crash', action='store_true')
    args = parser.parse_args()
    assert not args.mismatched_screen or args.electron_screen
    assert not args.resize_burst or args.electron_screen
    if args.core_crash:
        assert not args.mutant and not args.electron_screen, '崩溃场景单独运行'
        return core_crash_scenario(args)
    args.output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='t212-', dir='/private/tmp'))
    state, home, cwd = (fixture / x for x in ('state', 'home', '项目 alpha'))
    for path in (state, home, cwd):
        path.mkdir()
    (home / '.zshrc').write_text("PS1='T212% '\n", encoding='utf-8')
    env = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR') if k in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color',
               A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'))
    source = ROOT
    if args.mutant:
        source = fixture / 'source'
        shutil.copytree(ROOT / 'workbench/src', source / 'workbench/src')
        for part in ('terminal', 'hooks', 'roles'):
            shutil.copytree(ROOT / 'workbench' / part, source / 'workbench' / part, symlinks=True)
        (source / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
        # Local distribution input only; version and digest still come from the release pin.
        env['ENCHANTED_HC_CACHE_DIR'] = str(ROOT.parent / 'hc-cache')
        if args.mutant == 'forget-token':
            path = source / 'workbench/src/panes.ts'
            text = path.read_text(encoding='utf-8')
            old = 'await this.attachShell(record as any, tokenHash, terminal);'
            assert text.count(old) == 1
            path.write_text(text.replace(old, 'await this.attachShell(record as any, "0".repeat(64), terminal);'), encoding='utf-8')
        if args.mutant == 'no-reset':
            path = source / 'workbench/src/panes.ts'
            text = path.read_text(encoding='utf-8')
            old = 'appendFileSync(trace, "\\x1bc");'
            assert text.count(old) == 1
            path.write_text(text.replace(old, ''), encoding='utf-8')
    report = dict(status='INCOMPLETE', command=[sys.executable, *sys.argv], fixture=str(fixture), checks=[], commands=[])
    running = False
    launch = None
    window = None
    sequence = 0
    electron = None
    tokens = set()
    project = 't212'

    def user_inventory():
        # Directory names only: never connect to the user's core.
        path = Path(pwd.getpwuid(os.getuid()).pw_dir) / '.local/state/herdr-core'
        return sorted(str(p.relative_to(path)) for p in path.rglob('*')) if path.exists() else []

    before_user = user_core_snapshot()

    def cli(*argv):
        command = ['node', str(source / 'workbench/src/gates/cli.ts'), '--state', str(state), *argv]
        run = subprocess.run(command, env=env, capture_output=True, text=True, timeout=40, start_new_session=True)
        report['commands'].append(dict(argv=command, exit=run.returncode, stdout=run.stdout, stderr=run.stderr))
        assert run.returncode == 0, f'{argv}: {run.stdout} {run.stderr}'
        return json.loads(run.stdout)

    def request(command, identity=None, **data):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(20)
            connection.connect(str(state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), identity=identity,
                input=dict(command=command, **data))) + '\n').encode())
            result = b''
            while b'\n' not in result:
                part = connection.recv(65536)
                assert part, '后台在回执前断开'
                result += part
        return json.loads(result.split(b'\n')[0])

    def start():
        nonlocal running
        env['A2A_OPERATOR_CREDENTIAL'] = str(fixture / ('operator-' + uuid.uuid4().hex + '.json'))
        result = cli('daemon_start')
        running = True
        pid, pgid = map(int, subprocess.check_output(['/bin/ps', '-p', str(result['pid']), '-o', 'pid=,pgid='], text=True).split())
        assert pid == pgid and pgid != os.getpgrp(), '后台未脱离调用者进程组'
        wait_for(lambda: request('pane_layout').get('recovering') is False, '恢复未结束')

    def stop():
        nonlocal running
        if running:
            cli('daemon_stop')
            wait_for(lambda: not (state / 'control.sock').exists(), '后台未退出')
            running = False

    def open_window():
        nonlocal window, sequence
        identity = json.loads(Path(env['A2A_OPERATOR_CREDENTIAL']).read_text(encoding='utf-8'))
        result = request('window_open', identity, launch=launch['id'], project=launch['project'])
        assert result['ok'], result
        window, sequence = result['identity'], 0

    def send(data):
        nonlocal sequence
        sequence += 1
        result = request('window_input', window, sequence=sequence, request_id=str(uuid.uuid4()), data=data)
        assert result['ok'], result

    def output():
        offset, data = 0, bytearray()
        while True:
            result = request('pane_output', launch=launch['id'], offset=offset)
            assert result['ok'], result
            data.extend(base64.b64decode(result['data_base64']))
            offset = result['next_offset']
            if offset == result['total_bytes']:
                break
        return bytes(data).decode('utf-8')

    def count():
        try:
            return int((cwd / 'count').read_text())
        except (FileNotFoundError, ValueError):
            return 0

    try:
        start()
        if args.electron_screen:
            operator = json.loads(Path(env['A2A_OPERATOR_CREDENTIAL']).read_text())
            opened = request('project_open', operator, repo=str(cwd))
            assert opened['ok'], opened
            project = opened['project']
        launch = cli('shell_start', '--project', project, '--cwd', str(cwd))['launch']
        open_window()
        program = cwd / 'numbered.py'
        program.write_text('import os,time,pathlib\n'
            'pathlib.Path("pid").write_text(str(os.getpid()))\n'
            'print("\\x1b]7501;state=working:app=agy\\x07",end="",flush=True)\n'
            'for i in range(1,100000):\n'
            ' if pathlib.Path("pause").exists():\n'
            '  pathlib.Path("paused").write_text("ready")\n'
            '  while pathlib.Path("pause").exists(): time.sleep(.01)\n'
            ' print(f"编号-{i:06d}-中文",flush=True)\n'
            ' pathlib.Path("count").write_text(str(i))\n'
            ' if i>=400: time.sleep(.02)\n', encoding='utf-8')
        send(f"/usr/bin/python3 '{program}'\r")
        wait_for(lambda: count() >= 410 and '编号-000400-中文' in output(), '编号程序未开始')
        before = output()
        (args.output / 'before.raw').write_text(before, encoding='utf-8')
        pid = int((cwd / 'pid').read_text())
        shell_pid = request('pane_status', thread=launch['thread'])['shell_pid']
        if args.mismatched_screen:
            sequence += 1
            sized = request('window_resize', window, sequence=sequence, request_id=str(uuid.uuid4()), cols=193, rows=120)
            assert sized['ok'], sized
            report['forced_hc_size'] = [193, 120]
        stopped_at = count()
        stop()
        if args.mutant == 'forget-socket':
            (state / 'terminal-endpoint.json').unlink()
        time.sleep(.4)
        observation = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'pid=,stat=,command='], capture_output=True, text=True)
        report['survival'] = dict(pid=pid, shell_pid=shell_pid, before=stopped_at, after=count(), ps=observation.stdout)
        assert count() > stopped_at + 5 and observation.stdout.strip() and not observation.stdout.split()[1].startswith('Z'), \
            '程序随后台重启结束：编号停止增长，原进程已退出'
        start()
        open_window()
        wait_for(lambda: f'编号-{count()-5:06d}-中文' in output(), '离线输出未接回')
        after = output()
        (args.output / 'after.raw').write_text(after, encoding='utf-8')
        status = request('pane_status', thread=launch['thread'])
        assert status['shell_pid'] == shell_pid and status['lifecycle'] == 'running', status
        assert after.startswith(before), '已记录历史被改写'
        numbers = {int(x) for x in re.findall(r'编号-(\d+)-中文', after)}
        assert set(range(1, count()-5)).issubset(numbers), '恢复后编号历史有缺口'
        report['checks'].append('原 pid、数百行中文历史及离线输出在后台重启后保留')
        assert status.get('cli_turn', {}).get('state') == 'working', status
        report['checks'].append('OSC 7501 实时透传且新 viewer 第一屏补发最新报告')
        if args.electron_screen:
            # Pause only the fixture's numbered output; Python remains the live foreground program.
            (cwd / 'pause').write_text('pause')
            wait_for(lambda: (cwd / 'paused').exists(), '编号程序未确认暂停输出')
            report['hc_size_before_electron'] = request('pane_status', thread=launch['thread']).get('size')
            try:
                from scripted_claude import Electron
                out = fixture / 'ui-output'; out.mkdir()
                ui = SimpleNamespace(source=ROOT, env=env, state=state, dir=fixture, out=out)
                electron = Electron(ui, 't212-screen-' + uuid.uuid4().hex[:8])
                selector = f'.pane[data-launch-id="{launch["id"]}"]'
                electron.until('接回的项目终端窗格',
                    f'''(()=>{{const r=document.querySelector('[data-terminal-launch="{launch['id']}"]');r?.click();
                    const p=document.querySelector({json.dumps(selector)});return p&&p.offsetParent!==null&&p.querySelector('[data-restoring]')?.dataset.restoring==='false'}})()''', 45)
                # Read the actual Terminal instance held in React state; no test branch or renderer export.
                buffer_expression = f'''(()=>{{
                  const p=document.querySelector({json.dumps(selector)});
                  const key=Object.keys(p).find(k=>k.startsWith('__reactFiber$'));let f=p[key];
                  for(;f;f=f.return)for(let h=f.memoizedState;h&&h.memoizedState!==undefined;h=h.next){{
                    const t=h.memoizedState;if(t?.buffer?.active?.getLine){{const b=t.buffer.active;
                      return Array.from({{length:b.length}},(_,i)=>b.getLine(i)?.translateToString(true)??'').join('\\n')}}
                  }}return null}})()'''
                rendered = electron.until('xterm 实际 buffer', buffer_expression, 30)
                manifest = json.loads((state / 'hc-runtime.json').read_text())
                core_env = dict(env, HC_SESSION=manifest['session'], HC_SOCKET=manifest['socket'],
                    XDG_STATE_HOME=str(state / 'hc/state'), XDG_CONFIG_HOME=str(state / 'hc/config'))
                size_expression = buffer_expression.replace("return Array.from({length:b.length},(_,i)=>b.getLine(i)?.translateToString(true)??'').join('\\n')", "return {cols:t.cols,rows:t.rows,cursorY:b.cursorY}")
                report['xterm_size'] = electron.evaluate(size_expression)
                if args.mismatched_screen:
                    assert report['xterm_size']['rows'] < 120, report['xterm_size']
                # Read by the address recorded on shell_created, never a guessed/current terminal.
                created = next(e for e in request('orchestration_events')['events'] if e['type']=='shell_created' and e.get('launch')==launch['id'])
                listed = subprocess.run([str(state / 'hc/bin/herdr-core'), '--json', 'get', created['data']['hc_terminal']], env=core_env,
                    capture_output=True, text=True, timeout=15)
                assert listed.returncode == 0, listed.stderr
                terminal_record = json.loads(listed.stdout)
                report['hc_size_after_electron'] = {key: terminal_record[key] for key in ('cols', 'rows')}
                assert report['hc_size_after_electron'] == {key: report['xterm_size'][key] for key in ('cols', 'rows')}
                argv = [str(state / 'hc/bin/herdr-core'), '--json', 'read', created['data']['hc_terminal'], '--lines', '10000']
                read = subprocess.run(argv, env=core_env, capture_output=True, text=True, timeout=15)
                assert read.returncode == 0, read.stderr
                text = json.loads(read.stdout)['text']
                pattern = r'编号-\d+-中文'
                expected = re.findall(pattern, text); actual = re.findall(pattern, rendered)
                # Renderer writes are asynchronous even after the backend read has reached its end.
                end = time.monotonic() + 10
                while actual != expected and time.monotonic() < end:
                    time.sleep(.1)
                    rendered = electron.evaluate(buffer_expression)
                    actual = re.findall(pattern, rendered)
                (args.output / 'xterm-buffer.txt').write_text(rendered, encoding='utf-8')
                (args.output / 'hc-terminal-read.txt').write_text(text, encoding='utf-8')
                electron.screenshot(args.output / 'reattached-terminal.png')
                report['screen_comparison'] = dict(command=argv, xterm_lines=len(actual), hc_lines=len(expected),
                    first=actual[:1], last=actual[-1:], missing=sorted(set(expected)-set(actual)), extra=sorted(set(actual)-set(expected)), program_pid=pid)
                assert len(expected) >= 410 and actual == expected, 'xterm 与 hc terminal.read 的历史/屏幕不同'
                assert actual[0] == '编号-000001-中文'
                report['checks'].append('真实 Electron 接回窗格：xterm buffer 与 hc terminal.read 的全部编号中文历史逐行一致，原程序仍在')
                if args.resize_burst:
                    trace = state / 'traces' / launch['id'] / 'pty.raw'
                    before_resets = trace.read_bytes().count(b'\x1bc')
                    sizes = electron.evaluate(f'''(async()=>{{
                      const p=document.querySelector({json.dumps(selector)}), sizes=[];
                      for(let i=0;i<24;i++){{
                        p.style.width=(900+i*8)+'px';p.style.height=(350+(i%2)*14)+'px';
                        await new Promise(r=>setTimeout(r,25));sizes.push({size_expression});
                      }}return sizes}})()''')
                    assert len({(s['cols'], s['rows']) for s in sizes}) >= 20, sizes
                    # Continue output while the last resize/paint may still be in flight.
                    (cwd / 'paused').unlink()
                    (cwd / 'pause').unlink()
                    resumed_at = count()
                    wait_for(lambda: count() >= resumed_at + 20, '连续改尺寸后程序输出停住')
                    (cwd / 'pause').write_text('pause')
                    wait_for(lambda: (cwd / 'paused').exists(), '连续改尺寸后未确认暂停')
                    final_size = {key: sizes[-1][key] for key in ('cols', 'rows')}
                    def hc_at_final_size():
                        got = subprocess.run([str(state / 'hc/bin/herdr-core'), '--json', 'get', created['data']['hc_terminal']],
                            env=core_env, capture_output=True, text=True, timeout=15)
                        assert got.returncode == 0, got.stderr
                        return {key: json.loads(got.stdout)[key] for key in ('cols', 'rows')} == final_size
                    wait_for(hc_at_final_size, 'hc 未采用最终尺寸')
                    electron.until('最终重绘显示完成', f"document.querySelector({json.dumps(selector)})?.querySelector('[data-restoring]')?.dataset.restoring==='false'", 20)
                    resized_read = subprocess.run(argv, env=core_env, capture_output=True, text=True, timeout=15)
                    assert resized_read.returncode == 0, resized_read.stderr
                    resized_text = json.loads(resized_read.stdout)['text']
                    resized_expected = re.findall(pattern, resized_text)
                    deadline = time.monotonic() + 10
                    while True:
                        resized_rendered = electron.evaluate(buffer_expression)
                        resized_actual = re.findall(pattern, resized_rendered)
                        if resized_actual == resized_expected or time.monotonic() >= deadline: break
                        time.sleep(.1)
                    added_resets = trace.read_bytes().count(b'\x1bc') - before_resets
                    (args.output / 'xterm-after-burst.txt').write_text(resized_rendered, encoding='utf-8')
                    (args.output / 'hc-after-burst.txt').write_text(resized_text, encoding='utf-8')
                    electron.screenshot(args.output / 'after-resize-burst.png')
                    report['resize_burst'] = dict(layout_changes=24, observed_sizes=sizes,
                        distinct_sizes=len({(s['cols'], s['rows']) for s in sizes}), added_resets=added_resets,
                        repaint_budget=3, final_hc_size=final_size, final_xterm_size=electron.evaluate(size_expression),
                        xterm_lines=len(resized_actual), hc_lines=len(resized_expected),
                        missing=sorted(set(resized_expected)-set(resized_actual)), extra=sorted(set(resized_actual)-set(resized_expected)))
                    assert resized_actual == resized_expected and resized_actual[0] == '编号-000001-中文', '连续改尺寸后历史/屏幕不完整'
                    assert added_resets <= 3, f'连续 24 次尺寸变化产生 {added_resets} 次全历史重绘，要求至多 3 次'
                    report['checks'].append('真实 Electron 连续 24 次布局变化只取少量重绘，最终尺寸和继续输出的全部历史一致')
            finally:
                (cwd / 'pause').unlink()
                if electron: electron.stop(); electron = None
        send('\x03')
        wait_for(lambda: 'KeyboardInterrupt' in output(), 'Ctrl-C 未到达程序')
        send(f"a2a whoami > '{cwd / 'whoami.json'}'; print -r -- command_done\r")
        wait_for(lambda: (cwd / 'whoami.json').exists() and (cwd / 'whoami.json').stat().st_size, '重启后 a2a 命令没有返回')
        identity = json.loads((cwd / 'whoami.json').read_text(encoding='utf-8'))
        assert identity.get('ok') is True and identity.get('terminal') == launch['id'] and identity.get('project') == project, \
            f'重启后 a2a 命令失效：{identity}'
        report['checks'].append('接回原终端后 a2a whoami 成功，socket 与身份仍有效')
        (cwd / 'raw.py').write_text(RAW_PROGRAM, encoding='utf-8')
        send(f"/usr/bin/python3 '{cwd / 'raw.py'}'\r")
        wait_for(lambda: (cwd / 'raw-ready').exists(), 'raw 程序未就绪')
        query = json.loads((cwd / 'query.json').read_text())
        assert query['answers'] == 1, f'终端查询未被恰好应答一次：{query}'
        # Typed keys, bracketed paste with Chinese/CR, Esc, and raw Ctrl-C all cross window_input.
        typed, pasted = 'ab', '\x1b[200~粘贴中文\r多行\x1b[201~'
        send(typed[0]); send(typed[1]); send(pasted); send('\x1b')
        sequence += 1
        resized = request('window_resize', window, sequence=sequence, request_id=str(uuid.uuid4()), cols=93, rows=31)
        assert resized['ok'], resized
        send('\x03')
        wait_for(lambda: (cwd / 'input.json').exists(), '真实终端未收到输入')
        received = json.loads((cwd / 'input.json').read_text())
        assert bytes.fromhex(received['hex']) == (typed + pasted + '\x1b\x03').encode('utf-8'), received
        assert received['size'] == [93, 31], received
        report['raw_io'] = dict(query=query, received=received)
        report['checks'].append('逐字打字、粘贴、中文、CR、Esc、Ctrl-C 原样到达；改尺寸到达真实终端；查询只应答一次')
        flood = cwd / 'flood.py'
        flood.write_text('import sys\nfor i in range(6000): print(f"FLOW-{i:05d}-"+"x"*80)\nprint("FLOW-COMPLETE",flush=True)\n', encoding='utf-8')
        send(f"/usr/bin/python3 '{flood}'\r")
        wait_for(lambda: '\r\nFLOW-COMPLETE\r\n' in output(), '超过 256 KiB 后输出停止', seconds=30)
        all_output = output()
        assert set(int(x) for x in re.findall(r'FLOW-(\d+)-', all_output)) == set(range(6000)), '流控输出缺行'
        (args.output / 'flow.raw').write_text(all_output, encoding='utf-8')
        report['checks'].append('6000 行、超过 512 KiB 的 attach 输出完整到达，CREDIT 持续归还')
        with sqlite3.connect(f'file:{state / "state.sqlite3"}?mode=ro', uri=True) as db:
            assert db.execute('SELECT count(*) FROM user_inputs').fetchone()[0] == 0
            assert db.execute('SELECT count(*) FROM user_input_ingress').fetchone()[0] == 0
        report['checks'].append('普通项目终端的输入没有被记为 agent 用户输入或人工介入')
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        try:
            if electron: electron.stop()
            tokens = private_tokens(state)
            if launch and running:
                cli('shell_close', '--launch', launch['id'])
            stop()
            report['core_cleanup'] = stop_private_core(fixture, env)
            assert report['core_cleanup'] is None or report['core_cleanup']['exit'] == 0, report['core_cleanup']
            report['cleanup'] = 'PASS'
        except Exception as error:
            report['cleanup'] = str(error)
            report['status'] = 'INCOMPLETE'
        after_user = user_core_snapshot()
        report['user_core_observations'] = dict(before=before_user, after=after_user)
        report['user_core_directory_unchanged'] = before_user['listing'] == after_user['listing']
        report['user_core_processes_unchanged'] = before_user['processes'] == after_user['processes']
        manifest = state / 'hc-runtime.json'
        if manifest.exists():
            private_socket = json.loads(manifest.read_text())['socket']
            report['private_socket_outside_user_home'] = not Path(private_socket).is_relative_to(Path(pwd.getpwuid(os.getuid()).pw_dir)) if sys.version_info >= (3,9) else private_socket.startswith('/private/tmp/')
        if not report['user_core_directory_unchanged']:
            report['status'] = 'NO_GO'
        # Keep the original fixture and its exact command for failure investigation.
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        report['evidence_boundary'] = assert_public_evidence(args.output, tokens)
        if report['status'] == 'PASS' and report.get('cleanup') == 'PASS':
            shutil.rmtree(fixture)
            report['successful_fixture_removed'] = not fixture.exists()
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
