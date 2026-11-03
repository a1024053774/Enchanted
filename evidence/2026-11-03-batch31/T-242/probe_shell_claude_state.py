"""T-242 probe: an ordinary project terminal runs `claude` (through the shim, no role), sends one prompt, and after the
reply samples once a second for 20 s: the pane header state, the sidebar row's data-agent-state, the daemon's
sidebar_snapshot state and foreground CLI, and the shell_native_session events (the session the terminal's hooks named).
The model is the scripted API of scripted_claude.Fixture (reply 测试正常。); no real model turn.
Usage: probe_shell_claude_state.py SUMMARY.json"""
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from scripted_claude import Electron, Fixture  # noqa: E402

summary = Path(sys.argv[1])
assert not summary.exists(), '保留既有证据，改用新路径'
report = dict(status='INCOMPLETE', argv=sys.argv, samples=[])
fixture = Fixture('t242-', lambda body: ('unused', [], '测试正常。'))
electron = None


def strip(raw):
    return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))


def screen(launch):
    return strip((fixture.state / 'traces' / launch / 'pty.raw').read_text(encoding='utf-8', errors='replace'))


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
        global sequence
        sequence += 1
        sent = fixture.request('window_input', window['identity'], sequence=sequence, request_id=str(uuid.uuid4()), data=data)
        assert sent['ok'], sent

    row = f"document.querySelector('[data-agent-launch=\"{launch}\"]')"
    electron.until('终端行', f"(()=>{{const r={row};if(r)r.click();const p=document.querySelector('.pane[data-launch-id=\"{launch}\"]');"
                   f"return !!p && p.offsetParent !== null}})()", 30)
    type_in('claude --model claude-haiku-5-5\r')
    fixture.wait('Claude 启动', lambda: 'ClaudeCodev' in screen(launch) and '❯' in screen(launch).split('ClaudeCodev', 1)[1], 60)
    time.sleep(3)
    type_in('只回复：测试正常。')
    time.sleep(1)
    type_in('\r')
    sent_at = time.time()
    # The typed prompt itself contains 测试正常。 once; the reply adds a second one.
    fixture.wait('Claude 回复', lambda: screen(launch).split('只回复', 1)[-1].count('测试正常。') >= 2, 60)
    report['reply_seen_after_s'] = round(time.time() - sent_at, 2)

    def events():
        with sqlite3.connect('file:' + str(fixture.state / 'state.sqlite3') + '?mode=ro', uri=True) as db:
            return [json.loads(r[0]) for r in db.execute("SELECT data FROM orchestration_events WHERE launch=? AND type='shell_native_session' ORDER BY seq", (launch,))]

    for _ in range(20):
        snapshot = fixture.request('sidebar_snapshot')
        backend = next((r for r in snapshot.get('agents', []) + snapshot.get('terminals', []) if r.get('id') == launch), {})
        ui = electron.evaluate(f"(()=>{{const p=document.querySelector('.pane[data-launch-id=\"{launch}\"]');const r={row};"
                               "return {header: p?.querySelector('.pane-state')?.textContent ?? null, header_state: p?.querySelector('.pane-state')?.dataset.state ?? null,"
                               " input_target: p?.querySelector('.input-target')?.textContent ?? null, row_state: r?.dataset.agentState ?? null}})()")
        report['samples'].append(dict(t=round(time.time() - sent_at, 2), ui=ui, backend_state=backend.get('state'), backend_cli=backend.get('cli')))
        time.sleep(1)
    try:
        report['shell_native_session'] = events()
    except (sqlite3.Error, OSError) as error:  # db missing or locked: the samples are still reported
        report['shell_native_session_error'] = f'{type(error).__name__}: {error}'
    electron.screenshot(fixture.out / 'after-reply.png')
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = f'{type(error).__name__}: {error}'
finally:
    try:
        if electron:
            electron.stop()
    finally:
        fixture.stop()
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(json.dumps(dict(status=report['status'], error=report.get('error'), last=report['samples'][-1:] if report['samples'] else None), ensure_ascii=False))
