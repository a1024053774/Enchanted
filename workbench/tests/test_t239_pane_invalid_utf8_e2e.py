"""T-239：项目终端的输出里有不完整或无效的 UTF-8 时，界面窗格照常显示，不报 TextDecoder 解码错误、不停止读取。
真实后台（源码副本）、门禁 CLI、项目终端与 zsh、hc core、一次后台重启，真实 Electron 窗口经 DevTools 协议读 xterm 的 buffer。

触发（修前在 T-237 的 Computer Use 复验里出现）：终端输出停在半个字符上时，后台重启接回终端，记录里在这半个字符后面追加
重绘的 `ESC c`；界面从头回放这段记录，用 fatal 模式的 TextDecoder 解码，读到这里就抛错，窗格显示错误并停止读取。

场景（期望来自 ticket：同一场景历史窗格正常显示，不再报解码错误；终端照常显示无效字节）：
A. 窗格 A 打印 `T239-A1`，接着只打印“中”的前两个字节并停在 sleep 上；后台停止再启动（core 不停），接回 A（记录里出现
   “半个字符 + ESC c”）。之后在 A 里打印 `T239-A2`。再停后台并结束夹具的 core 与 shell、启动后台：A 的终端已不在，只能从头回放。
   Electron 打开 A：无错误提示，回放结束，buffer 里有 A1 与 A2。（终端还在时，界面打开窗格先让它重绘，跳过旧记录，不经过这段字节。）
B. Electron 已在显示窗格 B 时，B 打印一个无效字节 0xff 夹在 `T239-B1` 与 `T239-B2` 之间，再打印 `T239-B3`：无错误提示，三段都在。
C. 窗格 C 一次打印 30000 个“中”（超过一次读取的 65536 字节，必然在字符中间分块）和 `T239-C-END`：buffer 里没有替换字符 U+FFFD。

失败方式（先列再写）：
1. 回放到“半个字符 + ESC c”时解码抛错，窗格显示错误、停在回放中（修前的缺陷）。
2. 实时输出里的无效字节让窗格停止读取，之后的输出看不到。
3. 过头：正常的多字节字符在分块边界被拆坏，显示成替换字符。
4. 错误被吞掉但读取停了：没有错误提示，可无效字节之后的输出不显示。
5. 触发条件没有真的出现（记录里没有“半个字符 + ESC c”），测试空跑。
--revision 在该版本源码上跑（修前应失败）；--mutant 跑已知坏实现。
"""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, source_tree  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
STRICT = "new TextDecoder('utf-8', { fatal: true, ignoreBOM: true })"
MUTANTS = {
    # Known-bad: the strict decoder as before the fix.
    'fatal': [('app/renderer.tsx', "    let decoder = new TextDecoder('utf-8', { ignoreBOM: true });", '    let decoder = ' + STRICT + ';'),
              ('app/renderer.tsx', "            decoder = new TextDecoder('utf-8', { ignoreBOM: true });", '            decoder = ' + STRICT + ';')],
    # Known-bad: each chunk decoded on its own, so a character split between two reads is broken.
    'no-stream': [('app/renderer.tsx', 'decoder.decode(bytes, { stream: true })', 'decoder.decode(bytes)')],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t239-', dir='/private/tmp')).resolve()
    state, home, repo, out = fixture / 'state', fixture / 'home', fixture / 'demo', fixture / 'out'
    for path in (state, home, out):
        path.mkdir()
    (home / '.zshrc').write_text("PS1='T239> '\n", encoding='utf-8')
    source = source_tree(fixture, args.revision, MUTANTS.get(args.mutant, ()), copy=True)
    cli = source / 'workbench/src/gates/cli.ts'
    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'TMPDIR'] if key in os.environ}
    env['ENCHANTED_HC_CACHE_DIR'] = os.environ.get('ENCHANTED_HC_CACHE_DIR') or str(ROOT.parent / 'hc-cache')
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'),
               GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, fixture=str(fixture), checks=[], observed={})
    running = False
    electron = None
    windows = {}

    def run_cli(*arguments):
        run = subprocess.run(['node', str(cli), '--state', str(state), *arguments], env=env, capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, f'{arguments[0]}: {run.stderr or run.stdout}'
        return json.loads(run.stdout)

    def request(command, identity=None, **data):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(60)
            connection.connect(str(state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)) + '\n').encode())
            response = b''
            while b'\n' not in response:
                part = connection.recv(65536)
                assert part, 'daemon 在回执前断开'
                response += part
        return json.loads(response.split(b'\n', 1)[0])

    def wait(label, predicate, timeout=30):
        deadline = time.monotonic() + timeout
        while not (value := predicate()):
            assert time.monotonic() < deadline, f'超时：{label}'
            time.sleep(.2)
        return value

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def start_daemon():
        run_cli('daemon_start')
        wait('后台恢复结束', lambda: request('pane_layout').get('recovering') is False, 15)
        return json.loads((fixture / 'operator.json').read_text(encoding='utf-8'))

    def stop_daemon():
        run_cli('daemon_stop')
        wait('后台停止', lambda: not (state / 'control.sock').exists(), 15)
        (fixture / 'operator.json').unlink()  # each daemon start issues a new operator credential
        windows.clear()

    def trace(launch):
        return (state / 'traces' / launch / 'pty.raw').read_bytes()

    def window(launch):
        if launch not in windows:
            opened = request('window_open', operator, launch=launch, project='demo')
            assert opened['ok'], opened
            windows[launch] = [opened['identity'], 0]

    def send(launch, data):
        window(launch)
        windows[launch][1] += 1
        result = request('window_input', windows[launch][0], sequence=windows[launch][1], request_id=str(uuid.uuid4()), data=data)
        assert result['ok'], result

    def shell():
        launch = run_cli('shell_start', '--project', 'demo', '--cwd', str(repo))['launch']['id']
        window(launch)
        try: wait('提示符', lambda: b'T239> ' in trace(launch), 20)
        except AssertionError: raise AssertionError(f'超时：提示符 {trace(launch)[-400:]!r}')
        return launch

    def buffer(launch):
        # The xterm Terminal held in React state for this pane, and the pane's error and restoring markers.
        selector = json.dumps(f'.pane[data-launch-id="{launch}"]')
        return electron.evaluate(f'''(()=>{{
          const r=document.querySelector('[data-agent-launch="{launch}"]');
          const p=document.querySelector({selector});
          if(!p||p.offsetParent===null){{r?.click();return null}}
          const key=Object.keys(p).find(k=>k.startsWith('__reactFiber$'));let f=p[key];
          for(;f;f=f.return)for(let h=f.memoizedState;h&&h.memoizedState!==undefined;h=h.next){{
            const t=h.memoizedState;if(t?.buffer?.active?.getLine){{const b=t.buffer.active;
              return {{text:Array.from({{length:b.length}},(_,i)=>b.getLine(i)?.translateToString(true)??'').join('\\n'),
                restoring:p.querySelector('[data-restoring]')?.dataset.restoring??null,
                errors:[...p.querySelectorAll('.connection-error')].map(e=>e.textContent)}}}}
          }}return null}})()''')

    def shown(launch, label, markers, timeout=30):
        # Settled: the replay reached the live end with every marker on screen, or the pane shows an error.
        def ready():
            value = buffer(launch)
            if value and (value['errors'] or (value['restoring'] == 'false' and all(m in value['text'] for m in markers))):
                return value
            return None
        try:
            return wait(label, ready, timeout)
        except AssertionError:
            report['observed'].setdefault('dom', electron.evaluate("[...document.querySelectorAll('[data-terminal-launch],[data-launch-id]')]"
                ".map(e=>[e.tagName,e.dataset.terminalLaunch||'',e.dataset.launchId||'',e.offsetParent!==null])"))
            return buffer(launch) or {}

    try:
        operator = start_daemon()
        running = True
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True, env=env)
        (repo / 'README.md').write_text('demo\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True, env=env)
        subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'init'], check=True, env=env)
        opened = request('project_open', operator, repo=str(repo))
        assert opened['ok'] and opened['project'] == 'demo', opened

        a = shell()
        # "中" is e4 b8 ad: stop after two of its three bytes, with the program still in front.
        send(a, "printf 'T239-A1\\n\\344\\270'; sleep 3600\r")
        wait('A 停在半个字符上', lambda: trace(a).endswith(b'\xe4\xb8'), 20)
        stop_daemon()
        running = False
        operator = start_daemon()
        running = True
        wait('A 接回并重绘', lambda: b'\xe4\xb8\x1bc' in trace(a), 20)
        check('trigger_present_half_character_before_paint', True)
        send(a, '\x03')
        send(a, "print T239-''A2\r")
        wait('A2 已输出', lambda: b'T239-A2' in trace(a), 20)
        # As in the reported case, the terminal is gone after the next restart: the pane only replays its record from the start.
        stop_daemon()
        running = False
        subprocess.run(['pkill', '-f', str(fixture)], check=False)
        wait('夹具进程退出', lambda: subprocess.run(['pgrep', '-f', str(fixture)], capture_output=True).returncode == 1, 15)
        operator = start_daemon()
        running = True
        closed = [e for e in request('orchestration_events')['events'] if e['type'] == 'shell_closed' and e.get('launch') == a]
        check('history_only_pane', len(closed) == 1, closed)

        c = shell()
        send(c, "/usr/bin/python3 -c \"print('中'*30000); print('T239-C-END')\"\r")
        wait('C 已输出', lambda: b'T239-C-END\r\n' in trace(c), 20)
        report['observed']['C_trace_bytes'] = len(trace(c))

        b = shell()
        electron = Electron(SimpleNamespace(source=source, env=env, out=out, state=state, dir=fixture), 't239-' + fixture.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")

        seen_a = shown(a, 'A 回放', ['T239-A1', 'T239-A2'])
        report['observed']['A'] = dict(errors=seen_a.get('errors'), restoring=seen_a.get('restoring'), tail=(seen_a.get('text') or '').strip()[-300:])
        electron.screenshot(out / 'pane-a.png')
        check('replayed_history_no_decode_error', seen_a.get('errors') == [], seen_a.get('errors'))
        check('replayed_history_reaches_live_end', seen_a.get('restoring') == 'false' and all(m in seen_a.get('text', '') for m in ('T239-A1', 'T239-A2')), report['observed']['A'])

        wait('B 在窗口里显示', lambda: (buffer(b) or {}).get('restoring') == 'false', 30)
        send(b, "printf 'T239-B1 \\377 T239-B2\\n'; print T239-''B3\r")
        seen_b = shown(b, 'B 实时输出', ['T239-B1', 'T239-B2', 'T239-B3'])
        report['observed']['B'] = dict(errors=seen_b.get('errors'), tail=(seen_b.get('text') or '').strip()[-300:])
        check('live_invalid_byte_no_decode_error', seen_b.get('errors') == [], seen_b.get('errors'))
        check('output_after_invalid_byte_shown', all(m in seen_b.get('text', '') for m in ('T239-B1', 'T239-B2', 'T239-B3')), report['observed']['B'])

        seen_c = shown(c, 'C 回放', ['T239-C-END'])
        text_c = seen_c.get('text', '')
        report['observed']['C'] = dict(errors=seen_c.get('errors'), han=text_c.count('中'), replacement=text_c.count('�'))
        check('split_characters_decoded_intact', seen_c.get('errors') == [] and 'T239-C-END' in text_c and text_c.count('�') == 0
              and text_c.count('中') > 0, report['observed']['C'])
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        if electron:
            try: electron.stop()
            except Exception as error: report['cleanup_error'] = f'electron: {error}'
        if running:
            try:
                run_cli('daemon_stop')
                deadline = time.monotonic() + 10
                while (state / 'control.sock').exists() and time.monotonic() < deadline:
                    time.sleep(.05)
            except Exception as error:
                report['cleanup_error'] = f"{report.get('cleanup_error', '')} {error}".strip()
        # Only processes started for this fixture: their command lines name its directory.
        subprocess.run(['pkill', '-f', str(fixture)], check=False)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        if (out / 'pane-a.png').exists():
            (out / 'pane-a.png').replace(args.summary.with_suffix('.png'))
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        subprocess.run(['rm', '-rf', str(fixture)], check=False)
    print(json.dumps({key: report[key] for key in ('status', 'checks', 'error') if key in report}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
