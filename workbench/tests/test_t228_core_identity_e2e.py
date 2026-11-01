"""T-228：编排后台启动时认私有 core 的身份。

失败方式（写断言之前列出）：
1. holder 重拉的 core（父进程是 holder、受控环境、私有状态目录）被当成外来的拒掉，后台起不来。
2. 外来 core（同一 session 与 socket，但状态写进默认 XDG 目录）被接受，后台在它上面开终端。
3. 拒绝时没有事件、没有原因，只剩一个退出码。
4. 核对 core 用哪个状态目录的手段失败或超时，被当成通过。
5. server start 报的 pid 与实际持有锁的进程不是同一个，仍被接受。
6. 路径写法不同（/tmp 与 /private/tmp），或路径含非 ASCII 字符、lsof 在 C locale 下转义输出，导致自己的 core 被误拒。
7. core 在后台自己的进程组里，后台退出时把它一起带走（T-212 的 detach 要求不能丢）。
8. 接受 holder 的 core 后，原终端没接回、shell 换了进程，或屏幕记成 exact。
9. 碰到用户自己的 core 或状态目录；遗留本测试的 core、holder、shell。

oracle 来自独立 ps、hc 自己的 server status 与 ls、后台数据库，不导入产品实现。
--case holder：停后台，杀 core，等 holder 重拉，再启动后台，期望接受并接回原终端。
--case foreign：停后台，杀 core 与 holder，用默认 XDG 目录起一个同 session 的 core，再启动后台，期望拒绝并记原因。
--non-ascii：数据目录含中文与空格，后台与 hc 都在 LC_ALL=C 下运行（第 6 项）。
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
import time
import traceback
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from hc_evidence import assert_public_evidence, private_tokens, user_core_snapshot  # noqa: E402
from test_t212_shell_hc_e2e import stop_private_core, wait_for  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=['holder', 'foreign'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--non-ascii', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='t228-' + args.case + ('-测试 目录-' if args.non_ascii else '-'), dir='/private/tmp'))
    state, home = fixture / 'state', fixture / 'home'
    state.mkdir(); home.mkdir()
    (home / '.zshrc').write_text("PS1='T228% '\n", encoding='utf-8')
    binary = state / 'hc/bin/herdr-core'
    env = {key: os.environ[key] for key in ('PATH', 'LANG', 'ENCHANTED_HC_CACHE_DIR') if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TMPDIR='/private/tmp')
    if args.non_ascii:
        env['LC_ALL'] = 'C'
    report = dict(status='INCOMPLETE', case=args.case, command=[sys.executable, *sys.argv], fixture=str(fixture),
                  checks={}, commands=[], real_model_calls=0)
    before = user_core_snapshot()
    running, manifest, launches, owned = False, None, [], set()

    def cli(*arguments, check=True):
        argv = ['node', str(ROOT / 'workbench/src/gates/cli.ts'), '--state', str(state), *arguments]
        run = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=60, start_new_session=True)
        report['commands'].append(dict(argv=argv, exit=run.returncode, stdout=run.stdout[-2000:], stderr=run.stderr[-2000:]))
        if check:
            assert run.returncode == 0, run.stdout or run.stderr
            return json.loads(run.stdout)
        return run

    def request(command, **fields):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(20); connection.connect(str(state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), identity=None,
                                                input=dict(command=command, **fields))) + '\n').encode())
            raw = b''
            while b'\n' not in raw:
                part = connection.recv(65536); assert part, '后台在回执前断开'; raw += part
        return json.loads(raw.split(b'\n')[0])

    def daemon_start(check=True):
        nonlocal running, manifest
        env['A2A_OPERATOR_CREDENTIAL'] = str(fixture / ('operator-' + uuid.uuid4().hex + '.json'))
        run = cli('daemon_start', check=False)
        if run.returncode == 0:
            running = True
            wait_for(lambda: request('pane_layout').get('recovering') is False, '后台恢复未完成', 30)
        elif check:
            raise AssertionError(run.stdout or run.stderr)
        manifest = json.loads((state / 'hc-runtime.json').read_text(encoding='utf-8'))
        return run

    def daemon_stop():
        nonlocal running
        if running:
            cli('daemon_stop'); wait_for(lambda: not (state / 'control.sock').exists(), '后台未退出', 20); running = False

    def hc(*arguments, private_state=True, timeout=20):
        extra = dict(XDG_STATE_HOME=str(state / 'hc/state'), XDG_CONFIG_HOME=str(state / 'hc/config')) if private_state else {}
        scoped = dict(env, HC_SESSION=manifest['session'], HC_SOCKET=manifest['socket'], **extra)
        argv = [str(binary), '--json', *arguments]
        run = subprocess.run(argv, env=scoped, capture_output=True, text=True, timeout=timeout, start_new_session=True)
        report['commands'].append(dict(argv=argv, private_state=private_state, exit=run.returncode,
                                       stdout=run.stdout[-2000:], stderr=run.stderr[-2000:]))
        assert run.returncode == 0, run.stderr
        return json.loads(run.stdout)

    def core_alive():
        with socket.socket(socket.AF_UNIX) as probe:
            probe.settimeout(.5)
            try:
                probe.connect(manifest['socket']); return True
            except OSError:
                return False

    def status():
        value = hc('server', 'status')
        owned.add(value['pid']); owned.update(h['pid'] for h in value['holders'])
        return value

    def parent(pid):
        return int(subprocess.check_output(['/bin/ps', '-p', str(pid), '-o', 'ppid='], text=True).strip())

    def alive(pid):
        run = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True, timeout=5)
        return bool(run.stdout.strip()) and not run.stdout.strip().startswith('Z')

    def events():
        with sqlite3.connect(f'file:{state / "state.sqlite3"}?mode=ro', uri=True) as db:
            return [dict(type=t, launch=l, data=json.loads(d)) for t, l, d in
                    db.execute('SELECT type, launch, data FROM orchestration_events ORDER BY seq')]

    try:
        daemon_start()
        launch = cli('shell_start', '--project', 't228', '--cwd', str(home))['launch']; launches.append(launch)
        shell_pid = request('pane_status', thread=launch['thread'])['shell_pid']; owned.add(shell_pid)
        first = status()
        daemon_stop()
        if args.case == 'holder':
            os.kill(first['pid'], signal.SIGKILL)
            wait_for(lambda: not alive(first['pid']), '旧 core 未退出', 5)
            wait_for(core_alive, 'holder 未重拉 core', 15)
            respawned = status()
            report['respawned_core'] = dict(pid=respawned['pid'], parent=parent(respawned['pid']),
                                            holders=[h['pid'] for h in first['holders']])
            report['checks']['holder_respawned_new_core'] = respawned['pid'] != first['pid']
            report['checks']['respawned_parent_is_holder'] = report['respawned_core']['parent'] in report['respawned_core']['holders']
            run = daemon_start(check=False)
            report['checks']['daemon_accepted_holder_core'] = run.returncode == 0
            assert run.returncode == 0, '后台拒绝了 holder 重拉的 core：' + (run.stdout or run.stderr)[-500:]
            after = status()
            pane = request('pane_status', thread=launch['thread'])
            reattached = [e for e in events() if e['type'] == 'shell_reattached' and e['launch'] == launch['id']]
            report['after_restart'] = dict(pane=pane, reattached=reattached, core_pid=after['pid'])
            report['checks'].update(
                same_core_kept=after['pid'] == respawned['pid'],
                same_shell_pid=pane.get('shell_pid') == shell_pid and alive(shell_pid),
                reattached_inexact=bool(reattached) and reattached[-1]['data'].get('screen') == 'inexact',
                status_inexact=pane.get('screen') == 'inexact')
        else:
            for pid in [h['pid'] for h in first['holders']] + [first['pid']]:
                os.kill(pid, signal.SIGKILL)
            wait_for(lambda: not core_alive() and not alive(first['pid']), 'core 或 holder 仍存活', 10)
            time.sleep(4)  # Longer than the holder's ~3 s respawn: nothing may bring the core back on its own.
            report['checks']['no_respawn_without_holder'] = not core_alive()
            foreign = hc('server', 'start', private_state=False)
            owned.add(foreign['pid'])
            default_lock = home / '.local/state/herdr-core' / manifest['session'] / 'core.lock'
            report['foreign_core'] = dict(pid=foreign['pid'], parent=parent(foreign['pid']),
                                          default_state_lock=default_lock.exists())
            report['checks']['foreign_core_uses_default_state'] = default_lock.exists()
            terminals_before = hc('ls', '--all', private_state=False).get('terminals', [])
            run = daemon_start(check=False)
            refused = [e for e in events() if e['type'] == 'hc_start_failed']
            terminals_after = hc('ls', '--all', private_state=False).get('terminals', []) if core_alive() else []
            report['after_start'] = dict(exit=run.returncode, stdout=run.stdout[-1000:], refused=refused,
                                         terminals_before=len(terminals_before), terminals_after=len(terminals_after))
            report['checks'].update(
                daemon_refused_foreign_core=run.returncode != 0,
                refusal_event_with_reason=bool(refused) and 'core.lock' in refused[-1]['data'].get('reason', ''),
                no_terminal_on_foreign_core=len(terminals_after) == len(terminals_before))
            if run.returncode == 0:
                daemon_stop()
            hc('server', 'stop', private_state=False)
        failed = [k for k, v in report['checks'].items() if not v]
        assert not failed, '断言失败：' + str(failed)
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        tokens = private_tokens(state)
        errors = []
        if running:
            for item in launches:
                try: cli('shell_close', '--launch', item['id'])
                except Exception as error: errors.append(str(error))
        try: daemon_stop()
        except Exception as error: errors.append(str(error))
        try:
            stop_private_core(fixture, env)
            for pid in owned:
                if alive(pid):
                    os.kill(pid, signal.SIGKILL)
            wait_for(lambda: not any(alive(pid) for pid in owned), '测试 core/holder/shell 仍存活', 20)
        except Exception as error: errors.append(str(error))
        report['cleanup'] = dict(status='INCOMPLETE' if errors else 'PASS', errors=errors, owned_pids=sorted(owned))
        if errors: report['status'] = 'INCOMPLETE'
        after = user_core_snapshot(); report['user_core'] = dict(unchanged=before == after, before=before, after=after)
        if before != after: report['status'] = 'NO_GO'
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        report['evidence_boundary'] = assert_public_evidence(args.output, tokens)
        if report['status'] == 'PASS' and not errors:
            shutil.rmtree(fixture)
    print(json.dumps(dict(status=report['status'], error=report.get('error'), checks=report['checks']), ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
