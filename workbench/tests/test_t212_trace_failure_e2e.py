"""T-212：经真实后台入口注入 paint 的 trace 写入失败。

失败方式（先列再写断言）：
1. resize 的 paint 回调抛错，attach 已离开 pending 却没有 resolve/reject，请求悬挂。
2. 同一 hc 连接被破坏，另一个项目终端也变成 hc_connection_lost、输入失败。
3. 捕获 IO 错误却仍返回成功/旧重绘偏移，或未把目标窗格记为 trace_write_failed。
4. 初次 attach 的 paint 出错仍返回成功或悬挂，影响其他终端。
5. 失败请求卡住写入队列，后续请求继续挂起；清理遗漏权限恢复或测试后台/core。
T-227 追加（规则：初次打开失败算“没建成”，当场销毁；窗格失败后不再写 trace，同一失败只记一次）：
6. 初次 attach 失败后，hc 终端和其中的 zsh 仍留在私有 core 里。
7. 销毁了终端却没记 shell_closed，侧栏仍把它当活着的终端。
8. 窗格失败后程序继续输出，每帧再记一条 trace_write_failed。
9. 去重或销毁时误伤另一个终端，或断开共享 hc 连接。
10. 只给失败事件去重，每帧仍去写 trace：trace 恢复可写后，失败窗格的后续输出又写了进去（T-227 第一轮审查）。

只改自己夹具的文件权限，不写满磁盘、不连接 default core、不调用模型。
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from hc_evidence import assert_public_evidence, private_tokens, user_core_snapshot
from scripted_claude import stop_private_core
from test_t212_shell_hc_e2e import wait_for

ROOT = Path(__file__).resolve().parents[2]


def scenario(case, output):
    output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='t212-trace-', dir='/private/tmp'))
    state, home, cwd = [fixture / name for name in ('state', 'home', 'project')]
    for directory in (state, home, cwd): directory.mkdir()
    (home / '.zshrc').write_text("PS1='TRACE% '\n", encoding='utf-8')
    env = {k: os.environ[k] for k in ('PATH', 'LANG') if k in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TMPDIR='/private/tmp', TERM='xterm-256color',
        A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'))
    before = user_core_snapshot()
    report = dict(status='INCOMPLETE', case=case, fixture=str(fixture), command=[sys.executable, *sys.argv], checks={})
    running = False; daemon_pid = None; protected = []; watcher = None; quit_watcher = threading.Event()
    operator = None; owned_pids = set(); tokens = set(); launches = []

    def cli(*args):
        run = subprocess.run(['node', str(ROOT / 'workbench/src/gates/cli.ts'), '--state', str(state), *args],
            env=env, capture_output=True, text=True, timeout=30, start_new_session=True)
        assert run.returncode == 0, run.stdout or run.stderr
        return json.loads(run.stdout)

    def request(command, identity=None, timeout=3, **fields):
        started = time.monotonic()
        try:
            with socket.socket(socket.AF_UNIX) as connection:
                connection.settimeout(timeout); connection.connect(str(state / 'control.sock'))
                connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), identity=identity,
                    input=dict(command=command, **fields))) + '\n').encode())
                raw = b''
                while b'\n' not in raw:
                    part = connection.recv(65536); assert part, '后台在回执前断开'; raw += part
            return json.loads(raw.split(b'\n')[0])
        except socket.timeout:
            return dict(timed_out=True, elapsed_seconds=time.monotonic()-started)

    def start_shell():
        result = request('shell_start', operator, project='t212-trace', cwd=str(cwd))
        assert result.get('ok'), result
        launch = result['launch']; launches.append(launch)
        owned_pids.add(request('pane_status', thread=launch['thread'])['shell_pid'])
        return launch

    def open_window(launch):
        result = request('window_open', operator, launch=launch['id'], project=launch['project'])
        assert result.get('ok'), result
        return result['identity']

    def protect(file):
        size = file.stat().st_size
        mode = file.stat().st_mode & 0o777
        file.chmod(0o400); protected.append((file, mode, size))

    try:
        started = cli('daemon_start'); running = True; daemon_pid = started['pid']
        pid, pgid = map(int, subprocess.check_output(['/bin/ps', '-p', str(daemon_pid), '-o', 'pid=,pgid='], text=True).split())
        assert pid == pgid and pgid != os.getpgrp()
        operator = json.loads(Path(env['A2A_OPERATOR_CREDENTIAL']).read_text())
        wait_for(lambda: request('pane_layout').get('recovering') is False, '后台恢复未完成')
        first, other = start_shell(), start_shell()
        first_window, other_window = open_window(first), open_window(other)
        trace_root = state / 'traces'
        for launch, window in ((first, first_window), (other, other_window)):
            ready = request('window_input', window, sequence=1, request_id=str(uuid.uuid4()), data='print -r -- T212_READY\r')
            assert ready.get('ok'), ready
            wait_for(lambda: b'T212_READY' in (trace_root / launch['id'] / 'pty.raw').read_bytes(), '真实终端尚未接收输入')
        manifest = json.loads((state / 'hc-runtime.json').read_text())
        private = dict(env, HC_SESSION=manifest['session'], HC_SOCKET=manifest['socket'],
            XDG_STATE_HOME=str(state / 'hc/state'), XDG_CONFIG_HOME=str(state / 'hc/config'))
        hc = subprocess.run([str(state / 'hc/bin/herdr-core'), '--json', 'server', 'status'], env=private,
            capture_output=True, text=True, timeout=15, start_new_session=True)
        core_pid = json.loads(hc.stdout)['pid']; owned_pids.add(core_pid)
        for shell_pid in list(owned_pids - {core_pid}):
            owned_pids.add(int(subprocess.check_output(['/bin/ps','-p',str(shell_pid),'-o','ppid='],text=True)))
        report['private_core_pid'] = core_pid
        if case == 'resize':
            target = first
            # Output keeps coming after the failure: each frame used to record trace_write_failed again.
            ticking = request('window_input', first_window, sequence=2, request_id=str(uuid.uuid4()),
                data=f"for i in {{1..40}}; do print -r -- T227_TICK_$i; print $i > '{cwd / 'tick'}'; sleep 0.05; done\r")
            assert ticking.get('ok'), ticking
            wait_for(lambda: b'T227_TICK_1' in (trace_root / target['id'] / 'pty.raw').read_bytes(), '输出循环未开始')
            protect(trace_root / target['id'] / 'pty.raw')
            response = request('window_resize', first_window, sequence=3, request_id=str(uuid.uuid4()), cols=111, rows=37)
        else:
            previous = set(trace_root.glob('*/pty.raw'))
            def watch():
                while not quit_watcher.is_set():
                    fresh = set(trace_root.glob('*/pty.raw')) - previous
                    if fresh:
                        protect(next(iter(fresh))); return
                    time.sleep(.001)
            watcher = threading.Thread(target=watch); watcher.start()
            response = request('shell_start', operator, project='t212-trace', cwd=str(cwd))
            quit_watcher.set(); watcher.join(timeout=2)
            assert protected and protected[0][2] == 0, '初次 paint 权限注入未发生在空 trace 上'
            assert protected[0][0].stat().st_size == 0, '初次 paint 已在权限注入前写入：不是有效场景'
            target_id = protected[0][0].parent.name
            events = request('orchestration_events')['events']
            created = next(e for e in events if e['type']=='shell_created' and e['launch']==target_id)
            # The append-only event carries the launch id, not its thread id.
            with sqlite3.connect(f'file:{state / "state.sqlite3"}?mode=ro', uri=True) as db:
                target = json.loads(db.execute('SELECT data FROM launch_records WHERE id=?', (target_id,)).fetchone()[0])
            owned_pids.add(created['data']['shell_pid'])
        report['failing_request'] = response
        status = request('pane_status', thread=target['thread'])
        other_status = request('pane_status', thread=other['thread'])
        report['pane_statuses'] = dict(target=status, other=other_status)
        refused = not response.get('timed_out') and response.get('ok') is False and response.get('error') == 'pane_unavailable'
        report['checks']['explicit_refusal_no_hang'] = refused
        report['checks']['target_trace_failure'] = str(status.get('failed','')).startswith('trace_write_failed:')
        if case == 'resize':
            # The trace becomes writable again while the loop still prints: a stopped pane leaves it untouched.
            file, mode, _ = protected[0]; file.chmod(mode)
            frozen = dict(bytes=file.stat().st_size, tick=int((cwd / 'tick').read_text()))
        report['checks']['other_not_failed'] = other_status.get('failed') is None and other_status.get('lifecycle') == 'running'
        marker = cwd / 'other-alive'
        typed = request('window_input', other_window, sequence=2, request_id=str(uuid.uuid4()), data=f"print -r -- intact > '{marker}'\r")
        report['other_input_response'] = typed
        if typed.get('ok'): wait_for(lambda: marker.exists(), '另一个终端未执行命令')
        report['checks']['other_still_usable'] = typed.get('ok') is True and marker.read_text().strip() == 'intact'
        if case == 'resize':
            after = request('window_input', first_window, sequence=4, request_id=str(uuid.uuid4()), data='x')
            report['later_input_response'] = after
            report['checks']['later_request_refused_no_hang'] = not after.get('timed_out') and after.get('error') == 'pane_unavailable'
        report['checks']['socket_survives'] = Path(manifest['socket']).exists()
        time.sleep(3)  # Longer than the 40 x 50 ms output loop.
        failures = [e for e in request('orchestration_events')['events']
                    if e['type'] == 'trace_write_failed' and e['launch'] == target['id']]
        report['trace_write_failed_events'] = len(failures)
        report['checks']['trace_failure_recorded_once'] = len(failures) == 1
        if case == 'resize':
            later = dict(bytes=file.stat().st_size, tick=int((cwd / 'tick').read_text()))
            report['trace_after_restore'] = dict(at_restore=frozen, after=later)
            report['checks']['output_continued_after_restore'] = later['tick'] > frozen['tick']
            report['checks']['trace_not_written_after_failure'] = later['bytes'] == frozen['bytes']
        if case == 'initial':
            listed = subprocess.run([str(state / 'hc/bin/herdr-core'), '--json', 'ls', '--all'], env=private,
                capture_output=True, text=True, timeout=15, start_new_session=True)
            live = [t for t in json.loads(listed.stdout).get('terminals', [])
                    if t['address'] == created['data']['hc_terminal'] and t['state'] == 'live']  # hc ls has no labels
            shell_pid = created['data']['shell_pid']
            gone = subprocess.run(['/bin/ps', '-p', str(shell_pid), '-o', 'stat='], capture_output=True, text=True).stdout.strip()
            report['initial_after'] = dict(live_terminals=live, shell_ps=gone)
            report['checks']['failed_terminal_not_in_core'] = not live
            report['checks']['failed_shell_exited'] = not gone or gone.startswith('Z')
            report['checks']['failed_terminal_recorded_closed'] = any(e['type'] == 'shell_closed' and e['launch'] == target['id']
                for e in request('orchestration_events')['events'])
        assert all(report['checks'].values()), str([name for name,value in report['checks'].items() if not value])
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        quit_watcher.set()
        if watcher: watcher.join(timeout=2)
        restored=[]
        for file,mode,size in protected:
            file.chmod(mode);restored.append(dict(path=str(file),mode=oct(file.stat().st_mode & 0o777),bytes_before_injection=size))
        report['permissions_restored'] = restored
        try:
            tokens = private_tokens(state)
            if running:
                stopping = request('daemon_stop', operator)
                deadline = time.monotonic()+3
                while (state/'control.sock').exists() and time.monotonic()<deadline: time.sleep(.05)
                if (state/'control.sock').exists():
                    # A known-bad stuck write queue cannot finish shutdown. Kill only our detached daemon.
                    os.kill(daemon_pid, signal.SIGKILL)
                    report['daemon_cleanup'] = 'SIGKILL after shutdown deadline (known-bad outstanding attach)'
                else: report['daemon_cleanup'] = 'normal daemon_stop'
            report['core_cleanup'] = stop_private_core(fixture / 'state', env)
            assert report['core_cleanup'] is None or report['core_cleanup']['exit']==0
            def exited(pid):
                try:os.kill(pid,0);return False
                except ProcessLookupError:return True
            wait_for(lambda: all(exited(pid) for pid in owned_pids), '本测试 core/holder/shell 未退出', seconds=15)
            report['cleanup'] = 'PASS'
        except Exception as error:
            report.update(cleanup=str(error),status='INCOMPLETE')
        after = user_core_snapshot();report['user_core'] = dict(before=before,after=after,unchanged=before==after)
        assert before==after
        (output/'run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        report['evidence_boundary'] = assert_public_evidence(output,tokens)
        if report['status']=='PASS' and report['cleanup']=='PASS':
            shutil.rmtree(fixture);report['successful_fixture_removed']=not fixture.exists()
        (output/'run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report['status']=='PASS'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--case',choices=['resize','initial'],required=True)
    args=p.parse_args()
    return 0 if scenario(args.case,args.output) else 1


if __name__=='__main__':raise SystemExit(main())
