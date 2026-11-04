"""T-242：没有角色的普通终端里，Claude Code 的回合状态取自 Enchanted 钩子，只在内存里，不记录。
真实后台、私有 hc core、Electron 窗口与经包装脚本运行的真实 Claude Code；模型由夹具的脚本化 API 应答（没有真实模型回合）。

失败方式（先列再写）：
1. 回合中、回复后仍显示未知（修前的设计，T-191）。
2. 回复后停在运行中：Stop 钩子没有把状态改回空闲。
3. 状态进了记录：出现 terminal_turn 事件，或提示词出现在状态库里（T-133：普通终端的提示词不进记录）。
4. 标题栏与侧栏、后台不一致；焦点标签仍写“正在输入”，被读成回合状态。
5. 旧状态沿用到下一个 CLI：Claude 退出后再起一个，第一次提交前就显示上一个的空闲。
另记 Esc 中断后的状态变化（Claude Code 被中断时不发 Stop），只观察不判定。

--revision 在该版本的隔离源码上跑（修前应失败于 1）；--mutant keep-turn 改为显示最后报告的进程的状态，不看前台，也不在进程退出后清掉（应失败于 5）。事件交错由 test_by_process.ts 穷举。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from scripted_claude import Electron, Fixture  # noqa: E402

# Both ways a state leaves another process: shown only for the process in front, and dropped once that process exits.
KEEP_TURN = [('src/byProcess.ts', 'const report = this.front && this.byPid.get(this.front.pid);', 'const report = [...this.byPid.values()].at(-1);'),
             ('src/byProcess.ts', 'return report && report.at >= this.front!.started ? report.value : null;', 'return report ? report.value : null;'),
             ('src/byProcess.ts', '  private prune() {\n', '  private prune() { return;\n')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--mutant', choices=['keep-turn'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, checks=[], samples=[])
    marker = 'T242-' + uuid.uuid4().hex[:12]
    hold = threading.Event()
    held = []

    def plan(body):
        # The main request of a turn waits until the test lets it reply, so the turn is observable while it runs.
        held.append(time.time())
        hold.wait(90)
        return ('turn', [], '测试正常。')

    fixture = Fixture('t242-', plan, revision=args.revision,
                      patches=KEEP_TURN if args.mutant == 'keep-turn' else ())
    report['fixture'] = str(fixture.dir)
    electron = None
    started = time.time()

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def strip(raw):
        return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))

    try:
        fixture.start(shutil.which('claude') or str(Path.home() / '.local/bin/claude'), {'README.md': 'demo\n'})
        assert fixture.request('role_release', fixture.terminal)['ok']
        claude_json = json.loads((fixture.home / '.claude.json').read_text(encoding='utf-8'))
        claude_json['projects'] = {str(fixture.repo): {'hasTrustDialogAccepted': True}}
        (fixture.home / '.claude.json').write_text(json.dumps(claude_json), encoding='utf-8')
        electron = Electron(fixture, 't242-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        launch = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert window['ok'], window
        sequence = 0

        def type_in(data):
            nonlocal sequence
            sequence += 1
            sent = fixture.request('window_input', window['identity'], sequence=sequence, request_id=str(uuid.uuid4()), data=data)
            assert sent['ok'], sent

        def screen():
            return strip((fixture.state / 'traces' / launch / 'pty.raw').read_text(encoding='utf-8', errors='replace'))

        row = f"document.querySelector('[data-agent-launch=\"{launch}\"]')"
        electron.until('终端行', f"(()=>{{const r={row};if(r)r.click();const p=document.querySelector('.pane[data-launch-id=\"{launch}\"]');"
                       f"return !!p && p.offsetParent !== null}})()", 30)

        def sample(label):
            snapshot = fixture.request('sidebar_snapshot')
            backend = next((r for r in snapshot.get('agents', []) + snapshot.get('terminals', []) if r.get('id') == launch), {})
            ui = electron.evaluate(f"(()=>{{const p=document.querySelector('.pane[data-launch-id=\"{launch}\"]');const r={row};"
                                   "return {header_state: p?.querySelector('.pane-state')?.dataset.state ?? null,"
                                   " input_target: p?.querySelector('.input-target')?.textContent ?? null, row_state: r?.dataset.agentState ?? null}})()")
            value = dict(label=label, t=round(time.time() - started, 2), backend=backend.get('state'), cli=backend.get('cli'), **ui)
            report['samples'].append(value)
            return value

        def settled(label, state, timeout, cli='claude'):
            """All three readings agree on state, with cli in front; returns the sample."""
            deadline = time.time() + timeout
            while True:
                value = sample(label)
                if value['backend'] == state and value['header_state'] == state and value['row_state'] == state and value['cli'] == cli:
                    return value
                if time.time() > deadline:
                    raise AssertionError(f'{label}: 期待 {state}，实际 {value}')
                time.sleep(.5)

        def start_claude(label):
            before = screen().count('ClaudeCodev')
            type_in('claude --model claude-haiku-5-5\r')
            fixture.wait(f'{label} Claude 启动', lambda: screen().count('ClaudeCodev') > before and '❯' in screen().rsplit('ClaudeCodev', 1)[1], 60)
            time.sleep(8)  # past the 5 s foreground recheck, so the backend has read the CLI in front

        def submit(text):
            type_in(text)
            time.sleep(1)
            type_in('\r')

        # 5 (first half) / 1: a fresh Claude before its first turn has no state yet.
        start_claude('第一个')
        check('before_first_turn_unknown', settled('第一次提交前', 'unknown', 5))

        # 1: during the turn, running.
        submit(f'只回复：测试正常。{marker}-1')
        fixture.wait('第一回合开始请求模型', lambda: len(held) >= 1, 30)
        check('running_during_turn', settled('回合中', 'running', 10))
        hold.set()
        fixture.wait('Claude 回复', lambda: screen().split(f'{marker}-1', 1)[-1].count('测试正常。') >= 1, 60)
        # 2: Stop brings it back to idle.
        check('idle_after_reply', settled('回复后', 'idle', 10))
        # 4: the focus label is not a state word.
        labels = {value['input_target'] for value in report['samples']}
        check('focus_label_not_typing', '正在输入' not in labels, labels)
        electron.screenshot(fixture.out / 'after-reply.png')

        # Esc while a turn runs: observed only (the gap note in sidebar.ts).
        hold.clear()
        submit(f'只回复：测试正常。{marker}-2')
        fixture.wait('第二回合开始请求模型', lambda: len(held) >= 2, 30)
        settled('中断前', 'running', 10)
        type_in('\x1b')
        interrupted = time.time()
        esc = []
        while time.time() - interrupted < 75:
            value = sample('Esc 之后')
            esc.append(dict(after_s=round(time.time() - interrupted, 1), backend=value['backend']))
            if value['backend'] != 'running':
                break
            time.sleep(3)
        report['esc'] = esc
        hold.set()

        # 3: nothing of these turns reached the records.
        with sqlite3.connect('file:' + str(fixture.state / 'state.sqlite3') + '?mode=ro', uri=True) as db:
            turns = db.execute("SELECT COUNT(*) FROM orchestration_events WHERE type='terminal_turn'").fetchone()[0]
            dump = '\n'.join(db.iterdump())
        check('no_terminal_turn_event', turns == 0, turns)
        check('prompt_not_recorded', marker not in dump)

        # 5: Claude exits, another starts; the first one's state is not carried over.
        # Esc put the interrupted prompt back into the input box; Ctrl-C clears it before /exit is typed.
        type_in('\x03')
        time.sleep(1)
        type_in('/exit')
        time.sleep(1)
        type_in('\r')
        check('idle_after_exit', settled('Claude 退出后', 'idle', 20, cli='zsh'))
        start_claude('第二个')
        check('next_cli_starts_unknown', settled('第二个 Claude 第一次提交前', 'unknown', 5))
        report['status'] = 'PASS'
    except Exception as error:
        report.update(status='INCOMPLETE', error=f'{type(error).__name__}: {error}')
    finally:
        hold.set()
        try:
            if electron:
                electron.stop()
        finally:
            try:
                fixture.stop()
                report['core_cleanup'] = fixture.core_cleanup
            except AssertionError as error:
                report.update(status='INCOMPLETE', residue=str(error))
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            if report['status'] == 'PASS':
                shutil.rmtree(fixture.dir)
    print(json.dumps({'status': report['status'], 'checks': report['checks'], 'error': report.get('error'), 'esc': report.get('esc')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
