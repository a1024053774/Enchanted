"""T-230：Enchanted 终端里不带私有 core 的地址；core 被杀后终端里的 hc 调用碰不到私有 core；inexact 窗格显示“历史不完整”。

真实入口：门禁命令行起编排后台、开项目终端；hc 只用后台按固定版本装好的二进制；夹具有自己的 HOME，
终端里不带 HC_SOCKET 的 hc 调用落在夹具 HOME 的默认会话下（hc 按 $HOME 解析默认状态与 socket 目录，T-211/T-220）。
“终端里的 agent 调 hc”沿用 T-220 探针二：夹具 .zshrc 在每个终端挂一个后台子进程，触发文件出现后以该终端的环境调 `hc ls`。

失败方式：
1. 四个变量 HC_SOCKET、HC_SESSION、HC_TERMINAL_ID、HC_TERMINAL_SOCKET 中任何一个漏进终端。
2. 去变量时连带去掉 a2a 自己的终端身份（A2A_TERMINAL、A2A_TERMINAL_SOCKET），a2a 命令失效。
3. core 被杀后，终端里的 hc 调用连到私有 socket，抢先拉起外来 core（父进程是 1、状态写进夹具 HOME 的私有会话目录）。
4. 私有 core 没被 holder 按受控环境接回，或原终端的 shell 被结束。
5. 后台重启后没接回窗格，shell 进程号变了，或没标 inexact。
6. 界面上 inexact 窗格不显示“历史不完整”。
7. 界面上没受影响（exact）的窗格也显示“历史不完整”。
8. 测试连到或改动用户自己的 core 与状态目录。
9. 终端里的 hc 调用在连到任何 core 之前就失败了，竞争场景其实没发生，检查却照样通过。

用法：python3 test_t230_terminal_hc_isolation_e2e.py --output DIR [--electron]
--electron 需要能起 Electron 的 python（T-212 用 Xcode 自带的 python3）。
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from types import SimpleNamespace
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from hc_evidence import assert_public_evidence, private_tokens, user_core_snapshot  # noqa: E402

HC_KEYS = ('HC_SOCKET', 'HC_SESSION', 'HC_TERMINAL_ID', 'HC_TERMINAL_SOCKET')
ZSHRC = r'''PS1='T230% '
/usr/bin/python3 -c 'import json,os,sys;json.dump({k:os.environ.get(k) for k in sys.argv[2:]},open(sys.argv[1],"w"))' \
  "$T230_DIR/env-$A2A_TERMINAL.json" HC_SOCKET HC_SESSION HC_TERMINAL_ID HC_TERMINAL_SOCKET A2A_TERMINAL A2A_TERMINAL_SOCKET
( while [[ ! -e $T230_DIR/trigger-$A2A_TERMINAL ]]; do sleep 0.02; done
  T230_STARTER=terminal-agent "$T230_HC" --json ls > "$T230_DIR/agent-$A2A_TERMINAL.out" 2> "$T230_DIR/agent-$A2A_TERMINAL.err"
  echo $? > "$T230_DIR/agent-$A2A_TERMINAL.exit" ) &!
'''


def wait_for(probe, message, seconds=15.0, step=.1):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = probe()
        if value:
            return value
        time.sleep(step)
    raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--electron', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='t230-', dir='/private/tmp'))
    state, home, marks, cwd = fixture / 'state', fixture / 'home', fixture / 'marks', fixture / 'project'
    for d in (state, home, marks, cwd):
        d.mkdir()
    subprocess.run(['git', 'init', '-q', str(cwd)], check=True)
    (home / '.zshrc').write_text(ZSHRC, encoding='utf-8')
    binary = state / 'hc/bin/herdr-core'
    env = {key: os.environ[key] for key in ('PATH', 'LANG', 'ENCHANTED_HC_CACHE_DIR') if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TMPDIR='/private/tmp', T230_DIR=str(marks), T230_HC=str(binary))
    report = dict(status='INCOMPLETE', command=[sys.executable, *sys.argv], fixture=str(fixture), commands=[],
                  real_model_calls=0, checks={})
    checks = report['checks']
    before = user_core_snapshot()
    running, manifest, electron = False, None, None

    def cli(*arguments, check=True):
        argv = ['node', str(ROOT / 'workbench/src/gates/cli.ts'), '--state', str(state), *arguments]
        run = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=60, start_new_session=True)
        report['commands'].append(dict(argv=argv, exit=run.returncode, stdout=run.stdout[-1500:], stderr=run.stderr[-1500:]))
        if check:
            assert run.returncode == 0, run.stdout or run.stderr
            return json.loads(run.stdout)
        return run

    def request(command, identity=None, **fields):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(20)
            connection.connect(str(state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), identity=identity,
                                                input=dict(command=command, **fields))) + '\n').encode())
            raw = b''
            while b'\n' not in raw:
                part = connection.recv(65536)
                assert part, '后台在回执前断开'
                raw += part
        return json.loads(raw.split(b'\n')[0])

    def start_daemon(check=True):
        nonlocal running, manifest
        env['A2A_OPERATOR_CREDENTIAL'] = str(fixture / ('operator-' + uuid.uuid4().hex + '.json'))
        run = cli('daemon_start', check=False)
        if run.returncode != 0:
            log = state / 'daemon.stderr.log'
            tail = [line for line in log.read_text(encoding='utf-8').splitlines() if 'TOKEN' not in line.upper()][-6:] if log.exists() else []
            assert not check, f'后台起不来：{run.stdout} {tail}'
            return dict(exit=run.returncode, daemon_stderr_tail=tail)
        running = True
        wait_for(lambda: request('pane_layout').get('recovering') is False, '后台恢复未完成', 30)
        manifest = json.loads((state / 'hc-runtime.json').read_text(encoding='utf-8'))
        return dict(exit=0)

    def stop_daemon():
        nonlocal running
        if running:
            cli('daemon_stop', check=False)
            wait_for(lambda: not (state / 'control.sock').exists(), '后台未退出', 20)
            running = False

    def private_hc(*arguments):
        private = dict(env, HC_SESSION=manifest['session'], HC_SOCKET=manifest['socket'],
                       XDG_STATE_HOME=str(state / 'hc/state'), XDG_CONFIG_HOME=str(state / 'hc/config'))
        argv = [str(binary), '--json', *arguments]
        run = subprocess.run(argv, env=private, capture_output=True, text=True, timeout=15, start_new_session=True)
        report['commands'].append(dict(argv=argv, exit=run.returncode, stdout=run.stdout[-1500:], stderr=run.stderr[-1500:]))
        assert run.returncode == 0, run.stderr
        return json.loads(run.stdout)

    def core_alive():
        with socket.socket(socket.AF_UNIX) as probe:
            probe.settimeout(.5)
            try:
                probe.connect(manifest['socket'])
                return True
            except OSError:
                return False

    def processes():
        rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,ppid=,command='], text=True).splitlines()
        return [dict(pid=int(p[0]), ppid=int(p[1]), command=p[2]) for p in (r.split(None, 2) for r in rows)
                if len(p) == 3 and p[2].startswith(str(binary))]

    def holds_lock(pid, lock):
        run = subprocess.run(['/usr/sbin/lsof', '-a', '-p', str(pid), '-Fp', '--', str(lock)], capture_output=True, text=True)
        return f'p{pid}' in run.stdout.split('\n')

    def terminal_env(launch):
        path = marks / f"env-{launch['id']}.json"
        wait_for(path.exists, '终端未写出环境')
        return json.loads(path.read_text(encoding='utf-8'))

    try:
        start_daemon()
        operator = json.loads(Path(env['A2A_OPERATOR_CREDENTIAL']).read_text(encoding='utf-8'))
        opened = request('project_open', operator, repo=str(cwd))
        assert opened['ok'], opened
        project = opened['project']
        launch = cli('shell_start', '--project', project, '--cwd', str(cwd))['launch']
        shell_pid = request('pane_status', thread=launch['thread'])['shell_pid']
        observed = terminal_env(launch)
        report['terminal_env'] = {k: (v is not None) for k, v in observed.items()}
        checks['terminal_has_no_hc_variables'] = all(observed[k] is None for k in HC_KEYS)
        checks['terminal_keeps_a2a_identity'] = observed['A2A_TERMINAL'] == launch['id'] and bool(observed['A2A_TERMINAL_SOCKET'])

        # The race of T-220: the core dies while the daemon runs and the pane's client calls hc at once.
        live = private_hc('server', 'status')
        os.kill(live['pid'], signal.SIGKILL)
        (marks / f"trigger-{launch['id']}").write_text('go')
        wait_for(lambda: (marks / f"agent-{launch['id']}.exit").exists(), '终端里的 hc 调用没结束', 30)
        report['agent_call'] = dict(exit=(marks / f"agent-{launch['id']}.exit").read_text().strip(),
                                    stdout=(marks / f"agent-{launch['id']}.out").read_text()[-1500:],
                                    stderr=(marks / f"agent-{launch['id']}.err").read_text()[-1500:])
        # The call really ran and was answered by the user's own hc (here the fixture HOME's default core), which has
        # no Enchanted terminal: it did not fail before reaching any core.
        try: answer = json.loads(report['agent_call']['stdout'])
        except ValueError: answer = None
        checks['terminal_hc_answered_without_enchanted_terminals'] = (report['agent_call']['exit'] == '0' and
                                                                      isinstance(answer, dict) and answer.get('terminals') == [])
        wait_for(core_alive, '私有 socket 上没有 core', 15)
        back = private_hc('server', 'status')
        parent = next((p['ppid'] for p in processes() if p['pid'] == back['pid']), None)
        private_lock = state / 'hc/state/herdr-core' / manifest['session'] / 'core.lock'
        foreign_state = home / '.local/state/herdr-core' / manifest['session']
        report['private_core_after_race'] = dict(pid=back['pid'], parent=parent, holds_private_lock=holds_lock(back['pid'], private_lock),
                                                 foreign_state_exists=foreign_state.exists(), processes=processes())
        checks['private_core_back_under_controlled_environment'] = parent != 1 and holds_lock(back['pid'], private_lock)
        checks['terminal_did_not_start_foreign_core'] = not foreign_state.exists()
        time.sleep(3)
        checks['original_shell_alive'] = subprocess.run(['/bin/ps', '-p', str(shell_pid)], capture_output=True).returncode == 0

        stop_daemon()
        restarted = start_daemon(check=False)
        report['daemon_restart'] = restarted
        checks['daemon_restarted'] = restarted['exit'] == 0
        if restarted['exit'] == 0:
            status = request('pane_status', thread=launch['thread'])
            events = request('orchestration_events')['events']
            report['after_restart'] = dict(status={k: status.get(k) for k in ('shell_pid', 'lifecycle', 'screen', 'failed')},
                                           events=[e for e in events if e['type'] in ('shell_screen_inexact', 'shell_reattached') and e.get('launch') == launch['id']])
            checks['pane_reattached_same_shell'] = status['shell_pid'] == shell_pid and status['lifecycle'] == 'running'
            checks['pane_screen_inexact'] = status.get('screen') == 'inexact' and any(
                e['type'] == 'shell_screen_inexact' for e in report['after_restart']['events'])
            if args.electron:
                fresh = cli('shell_start', '--project', project, '--cwd', str(cwd))['launch']
                assert request('pane_status', thread=fresh['thread']).get('screen') == 'exact'
                from scripted_claude import Electron
                out = fixture / 'ui-output'
                out.mkdir()
                ui = SimpleNamespace(source=ROOT, env=env, state=state, dir=fixture, out=out)
                electron = Electron(ui, 't230-' + uuid.uuid4().hex[:8])

                def shown(target):
                    selector = f'.pane[data-launch-id="{target["id"]}"]'
                    try:
                        return wait_pane(target, selector)
                    except AssertionError:
                        report['ui_page'] = electron.evaluate('''({rows:[...document.querySelectorAll('[data-agent-launch]')].map(e=>e.dataset.agentLaunch),
                          panes:[...document.querySelectorAll('.pane[data-launch-id]')].map(e=>({id:e.dataset.launchId,restoring:e.querySelector('[data-restoring]')?.dataset.restoring??null,visible:e.offsetParent!==null})),
                          text:document.body.innerText.slice(0,800)})''')
                        raise

                def wait_pane(target, selector):
                    # Click the sidebar row once: each click re-opens the pane, which restores its screen again.
                    electron.until('侧栏行 ' + target['id'], f'''(()=>{{const r=document.querySelector('[data-agent-launch="{target['id']}"]');if(!r)return null;r.click();return true}})()''', 45)
                    ready = f'''(()=>{{
                      const p=document.querySelector({json.dumps(selector)});
                      if(!p||p.offsetParent===null||p.querySelector('[data-restoring]')?.dataset.restoring!=='false')return null;
                      const hint=p.querySelector('[data-screen-inexact]');return {{hint:hint?hint.textContent:''}}}})()'''
                    first = electron.until('窗格 ' + target['id'], ready, 45)
                    time.sleep(1)  # Restored and still restored a second later: the layout has settled.
                    return electron.until('窗格稳定 ' + target['id'], ready, 45) or first
                inexact = shown(launch)
                electron.screenshot(args.output / 'inexact-pane.png')
                exact = shown(fresh)
                electron.screenshot(args.output / 'exact-pane.png')
                report['ui'] = dict(inexact=inexact, exact=exact)
                checks['ui_inexact_pane_says_history_incomplete'] = '历史不完整' in inexact['hint']
                checks['ui_exact_pane_has_no_hint'] = exact['hint'] == ''
        report['status'] = 'PASS' if all(checks.values()) else 'INCOMPLETE'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        if electron:
            try:
                electron.stop()
            except Exception as error:
                report['electron_stop_error'] = str(error)
        try:
            stop_daemon()
        except Exception as error:
            report['stop_error'] = str(error)
        leftovers = processes()
        for p in leftovers:
            try:
                os.kill(p['pid'], signal.SIGKILL)
            except ProcessLookupError:
                pass
        time.sleep(1)
        report['cleanup'] = dict(killed=leftovers, remaining=processes())
        tokens = private_tokens(state)
        for path in (home / '.local/state/herdr-core').glob('*/terminals.json'):
            for terminal in json.loads(path.read_text(encoding='utf-8')).get('terminals', {}).values():
                if terminal.get('restart_env', {}).get('A2A_TERMINAL_TOKEN'):
                    tokens.add(terminal['restart_env']['A2A_TERMINAL_TOKEN'])
        after = user_core_snapshot()
        report['user_core'] = dict(unchanged=before == after, before=before, after=after)
        if before != after:
            report['status'] = 'NO_GO'
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        report['evidence_boundary'] = assert_public_evidence(args.output, tokens)
        if report['status'] == 'PASS' and not report['cleanup']['remaining']:
            shutil.rmtree(fixture)
    print(json.dumps(dict(status=report['status'], checks=checks, error=report.get('error'), output=str(args.output)), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
