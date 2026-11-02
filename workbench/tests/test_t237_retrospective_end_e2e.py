"""T-237：复盘的 CLI 退出、或它的终端已不在之后，复盘不再一直显示“进行中”；拿不准时不判结束，并在复盘上留下原因。
真实后台、门禁 CLI、项目终端与 zsh、真实 Electron 窗口（经 DevTools 协议读 Reflect 页）；复盘的 CLI 换成本地替身脚本
（按控制文件决定退出、一直运行、或写出报告后退出），无模型。后台从源码副本运行，以便在副本里给进程查询注入故障。

场景（期望来自 ticket 与第 1 轮审查：CLI 退出或终端关闭有记录时显示已结束；没退出的、写出了报告的、看不清的不判结束）：
A. 替身 1 秒后退出，什么都不写。启动后 5 秒的检查仍算进行中；61 秒的检查记 ended（cli_not_running）。之后补写报告，照常导入。
B. 替身一直运行（zsh 作业控制开着）。始终不判结束，直到第二次重启前它的 core 和程序都被结束：记 ended（terminal_gone）。
C. 替身写出报告后退出。导入，不记 ended。
E. 替身一直运行，zsh 关掉作业控制（unsetopt MONITOR，替身与 shell 同一进程组）。不判结束。
H. 替身退出后，两次检查同时进行：ended 只记一条。
F. 进程查询出错（副本里的查询脚本换成退出码 3）：B 不判结束，复盘上记一条 end_check_unknown（带查询诊断），连查两次不重复；
   查询恢复后记一条 end_check_known。
R. 第一次重启前把 E 终端的凭据弄坏：恢复时接不回 E 的终端（shell_exit_unconfirmed，替身其实还在），E 不判结束，记 unknown；
   接回来的 B 照旧进行中。
U. Reflect 页：A 已完成；B“已结束，没有报告（终端已不在）”；H“……（CLI 已退出或没有启动）”；K（查询出错时启动）进行中并写明无法确认。

失败方式（先列再写）：
1. CLI 退出后一直显示进行中（修前的缺陷）。
2. 终端关闭有记录后仍显示进行中。
3. 过头：还在运行的 CLI 被记成结束——没输出的、作业控制关掉的、恢复时没接回终端的、进程查询出错的。
4. 写完报告再退出的复盘被记成结束而不是导入；已结束的复盘之后写出报告，不导入。
5. 刚启动、CLI 还没 exec 时的检查就记成结束。
6. 重复记 ended（逐次检查，或两次检查重叠）。
7. 查询出错只进后台总日志、复盘上看不到，或每分钟重复记。
8. 页面上仍显示“进行中”，或看不出原因。
--revision 在该版本源码上跑（修前应失败）；--mutant 跑已知坏实现。
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
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
FAKE = r'''#!/usr/bin/python3
import json, os, sys, time
from pathlib import Path
args = sys.argv
out = Path(json.loads(args[args.index('--settings') + 1])['sandbox']['filesystem']['allowWrite'][0])
mode = Path(%r).read_text().strip()
(out / 'fake-pid').write_text(str(os.getpid()))
(out / 'fake-started').write_text(mode)
if mode == 'exit':
    time.sleep(1)
elif mode == 'sleep':
    time.sleep(3600)
elif mode == 'report':
    (out / 'report.md').write_text('# 复盘\n\nT-237 替身报告。\n')
    (out / 'suggestions.json').write_text(json.dumps([{'title': 'T-237 建议', 'body': '', 'kind': 'other'}], ensure_ascii=False))
'''
BROKEN_QUERY = "import sys\nsys.stderr.write('t237 injected query failure\\n')\nsys.exit(3)\n"
LOOP = 'if (!recovering) for (const { run, launch, startedAt } of retrospectives.unfinished()) {'
MUTANTS = {
    # Known-bad: nothing checks the terminal (the defect as reported).
    'no-end-check': [('src/daemon.ts', LOOP, LOOP.replace('retrospectives.unfinished()', '[] as ReturnType<typeof retrospectives.unfinished>'))],
    # Known-bad: an empty prompt ends the run at once, before the CLI had time to start.
    'no-grace': [('src/daemon.ts', ' ||\n        (seen.front === "prompt" && now.getTime() - Date.parse(startedAt) < RETROSPECTIVE_START_GRACE_MS)', '')],
    # Known-bad: a recorded close counts as still running.
    'gone-is-running': [('src/panes.ts', 'if (this.store.lastEvent(launch, ["shell_closed"])) return { front: "gone" };',
                         'if (this.store.lastEvent(launch, ["shell_closed"])) return { front: "program" };')],
    # Known-bad: the end check runs before the import, so a run that wrote its report is also marked ended.
    'end-before-import': [('src/daemon.ts', '    const imported = retrospectives.importFinished();\n', ''),
                          ('src/daemon.ts', '    return { started, imported, ended };', '    const imported = retrospectives.importFinished();\n    return { started, imported, ended };')],
    # Known-bad (review 01, 1): a terminal the daemon could not restore counts as gone.
    'missing-is-gone': [('src/panes.ts', 'if (!pane) return { front: "unknown", reason: "terminal_not_restored" };', 'if (!pane) return { front: "gone" };')],
    # Known-bad (review 01, 2): only a process-group leader in front counts, which misses a program under job control off.
    'job-control-only': [('src/panes.ts', 'return others.some(row => row.pgid === shell.tpgid) ? { front: "program" } : { front: "unknown", reason: "background_only" };',
                          'return others.some(row => row.pid === row.pgid && row.pgid === row.tpgid) ? { front: "program" } : { front: "prompt" };')],
    # Known-bad (review 01, 3): an unanswerable check leaves nothing on the run.
    'unknown-not-recorded': [('src/daemon.ts', '      retrospectives.noteEndCheck(run.id, seen);\n', '')],
    # Known-bad (review 01, 3): the same unanswerable check is recorded every time.
    'unknown-every-check': [('src/retrospective.ts', "if (last?.type !== 'end_check_unknown' || last.data.reason !== seen.reason) ", '')],
    # Known-bad (review 01, 4): no second look after the wait, so overlapping checks both record the end.
    'no-recheck': [('src/daemon.ts', '      if (!retrospectives.unfinished().some(item => item.run.id === run.id)) continue;\n', '')],
    # Known-bad: recovery cannot confirm a terminal that a restarted core no longer has, so it never counts as gone.
    'core-restart-unconfirmed': [('src/hc.ts', "    return record?.state === 'live' ? new HcTerminal(this.connection!, record) : null;",
                                  "    if (!record) throw new Error('recorded hc terminal identity missing');\n    return record.state === 'live' ? new HcTerminal(this.connection!, record) : null;")],
    # Known-bad (review 01, 5): the Reflect page does not show the end or the unknown state (the page as of 82e747f4a).
    'ui-revert': 'app/RetrospectiveSections.tsx@82e747f4a',
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    fixture = Path(tempfile.mkdtemp(prefix='t237-', dir='/private/tmp')).resolve()
    state, home, repo, out = fixture / 'state', fixture / 'home', fixture / 'demo', fixture / 'out'
    for path in (state, home, out):
        path.mkdir()
    nomonitor = fixture / 'nomonitor'
    (home / '.zshrc').write_text(f"PS1='T237% '\n[[ -e {nomonitor} ]] && unsetopt MONITOR\n", encoding='utf-8')
    mutant = MUTANTS.get(args.mutant)
    source = source_tree(fixture, args.revision, mutant if isinstance(mutant, list) else (), copy=True)
    if isinstance(mutant, str):
        relative, revision = mutant.split('@')
        (source / 'workbench' / relative).write_bytes(subprocess.check_output(['git', 'show', f'{revision}:workbench/{relative}'], cwd=ROOT))
    cli = source / 'workbench/src/gates/cli.ts'
    query = source / 'workbench/src/processSnapshot.py'
    query_text = query.read_text(encoding='utf-8')
    mode = fixture / 'mode'
    fake = fixture / 'claude'
    fake.write_text(FAKE % str(mode), encoding='utf-8')
    fake.chmod(0o755)
    (fixture / 'launch-config.json').write_text(json.dumps(dict(claude_bin=str(fake))), encoding='utf-8')
    env = {key: os.environ[key] for key in ['PATH', 'LANG', 'TMPDIR'] if key in os.environ}
    # A copied source tree resolves the hc archive cache inside the fixture; point it at the checkout's cache.
    env['ENCHANTED_HC_CACHE_DIR'] = os.environ.get('ENCHANTED_HC_CACHE_DIR') or str(ROOT.parent / 'hc-cache')
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'),
               GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, fixture=str(fixture), checks=[], observed={})
    running = False
    electron = None

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
        run_cli('daemon_start', '--launch-config', str(fixture / 'launch-config.json'))
        wait('后台恢复结束', lambda: request('pane_layout').get('recovering') is False, 10)
        return json.loads((fixture / 'operator.json').read_text(encoding='utf-8'))

    def stop_daemon():
        run_cli('daemon_stop')
        wait('后台停止', lambda: not (state / 'control.sock').exists(), 15)
        (fixture / 'operator.json').unlink()  # each daemon start issues a new operator credential

    def kill_fixture_processes():
        # Only processes started for this fixture: their command lines name its directory.
        subprocess.run(['pkill', '-f', str(fixture)], check=False)
        wait('夹具进程退出', lambda: subprocess.run(['pgrep', '-f', str(fixture)], capture_output=True).returncode == 1, 15)

    def runs():
        listing = request('retrospective_list', operator, project='demo')
        assert listing['ok'], listing
        return {run['id']: run for run in listing['runs']}

    def events(run_id, kind=None):
        found = runs()[run_id]['events']
        return [event for event in found if event['type'] == kind] if kind else found

    def kinds(run_id):
        return [event['type'] for event in events(run_id)]

    def start(kind):
        mode.write_text(kind, encoding='utf-8')
        started = request('retrospective_start', operator, project='demo', cli='Claude Code', model='fixture-model', effort='low')
        assert started['ok'], started
        run = started['run']
        wait(f'替身 {kind} 启动', lambda: (Path(run['out']) / 'fake-started').exists())
        first = next(e for e in events(run['id']) if e['type'] == 'started')
        return SimpleNamespace(id=run['id'], out=Path(run['out']), launch=first['data']['launch'],
                               at=datetime.fromisoformat(first['created_at'].replace('Z', '+00:00')))

    def tick(when):
        result = request('retrospective_tick', operator, now=when.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z'))
        assert result['ok'], result
        return result

    def pgid(pid):
        return int(subprocess.check_output(['ps', '-o', 'pgid=', '-p', str(pid)], text=True).strip())

    try:
        operator = start_daemon()
        running = True
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True, env=env)
        (repo / 'README.md').write_text('demo\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True, env=env)
        subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'init'], check=True, env=env)
        assert request('project_open', operator, repo=str(repo))['ok']

        a, b = start('exit'), start('sleep')
        nomonitor.write_text('', encoding='utf-8')
        e = start('sleep')
        nomonitor.unlink()
        fake_e = int((e.out / 'fake-pid').read_text())
        parent_e = int(subprocess.check_output(['ps', '-o', 'ppid=', '-p', str(fake_e)], text=True).strip())
        report['observed']['job_control_off'] = dict(fake=fake_e, fake_pgid=pgid(fake_e), shell=parent_e, shell_pgid=pgid(parent_e))
        assert pgid(fake_e) == pgid(parent_e), ('E 的替身应与 shell 同一进程组', report['observed']['job_control_off'])
        time.sleep(3)  # A has exited; B and E are still running.
        tick(a.at + timedelta(seconds=5))
        check('exited_cli_not_ended_within_grace', 'ended' not in kinds(a.id), kinds(a.id))
        # C starts after that check, so its import and its end check fall in the same later check.
        c = start('report')
        time.sleep(3)  # C has written its files and exited.
        late = max(a.at, b.at, c.at, e.at) + timedelta(seconds=61)
        tick(late)
        tick(late + timedelta(seconds=60))
        report['observed']['late'] = {name: events(run.id) for name, run in (('A', a), ('B', b), ('C', c), ('E', e))}
        ended_a = events(a.id, 'ended')
        check('exited_cli_marked_ended', len(ended_a) == 1 and ended_a[0]['data'].get('reason') == 'cli_not_running', ended_a)
        check('running_cli_stays_in_progress', 'ended' not in kinds(b.id), kinds(b.id))
        check('job_control_off_cli_stays_in_progress', 'ended' not in kinds(e.id), kinds(e.id))
        check('reported_run_imported_not_ended', 'imported' in kinds(c.id) and 'ended' not in kinds(c.id), kinds(c.id))

        h = start('exit')
        time.sleep(3)
        with ThreadPoolExecutor(2) as pool:
            list(pool.map(lambda _: tick(h.at + timedelta(seconds=61)), range(2)))
        check('overlapping_checks_end_once', kinds(h.id).count('ended') == 1, kinds(h.id))

        query.write_text(BROKEN_QUERY, encoding='utf-8')
        tick(late + timedelta(seconds=120))
        tick(late + timedelta(seconds=180))
        query.write_text(query_text, encoding='utf-8')
        unknown_b = events(b.id, 'end_check_unknown')
        report['observed']['query_failed_B'] = events(b.id)
        check('query_failure_not_ended', 'ended' not in kinds(b.id), kinds(b.id))
        check('query_failure_recorded_once_with_diagnostics', len(unknown_b) == 1 and unknown_b[0]['data'].get('reason') == 'process_query_failed'
              and 't237 injected query failure' in (unknown_b[0]['data'].get('process_query') or {}).get('stderr', ''), unknown_b)
        tick(late + timedelta(seconds=240))
        check('query_recovery_recorded', kinds(b.id).count('end_check_known') == 1 and 'ended' not in kinds(b.id), kinds(b.id))

        (a.out / 'report.md').write_text('# 复盘\n\nA 迟到的报告。\n', encoding='utf-8')
        (a.out / 'suggestions.json').write_text('[]', encoding='utf-8')
        tick(late + timedelta(seconds=300))
        check('ended_run_imports_later_report', 'imported' in kinds(a.id), kinds(a.id))

        # First restart: E's terminal cannot be reattached (its credential is broken) while its program still runs.
        stop_daemon()
        running = False
        (state / 'shell-credentials' / f'{e.launch}.json').write_text('{}', encoding='utf-8')
        operator = start_daemon()
        running = True
        tick(late + timedelta(seconds=360))
        report['observed']['after_restart_1'] = {name: events(run.id) for name, run in (('B', b), ('E', e))}
        unrestored = [event for event in events(e.id, 'end_check_unknown') if event['data'].get('reason') == 'terminal_not_restored']
        check('unrestored_terminal_not_ended', 'ended' not in kinds(e.id) and len(unrestored) == 1, events(e.id))
        check('restored_running_cli_stays_in_progress', 'ended' not in kinds(b.id), kinds(b.id))

        # Second restart: the fixture's core and programs are gone with the daemon, as in the reported case.
        stop_daemon()
        running = False
        kill_fixture_processes()
        operator = start_daemon()
        running = True
        tick(late + timedelta(seconds=420))
        report['observed']['after_restart_2'] = {name: events(run.id) for name, run in (('A', a), ('B', b), ('E', e))}
        ended_b = events(b.id, 'ended')
        check('gone_terminal_marked_ended', len(ended_b) == 1 and ended_b[0]['data'].get('reason') == 'terminal_gone', ended_b)
        check('ended_recorded_once', kinds(a.id).count('ended') == 1, kinds(a.id))

        k = start('sleep')
        query.write_text(BROKEN_QUERY, encoding='utf-8')
        tick(k.at + timedelta(seconds=5))
        query.write_text(query_text, encoding='utf-8')
        check('query_failure_recorded_for_new_run', len(events(k.id, 'end_check_unknown')) == 1, kinds(k.id))

        electron = Electron(SimpleNamespace(source=source, env=env, out=out, state=state, dir=fixture), 't237-' + fixture.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('Reflect 页签', "!!document.querySelector('[data-reflect-tab]')", 20)
        electron.evaluate("document.querySelector('[data-reflect-tab]').click()")
        ids = [a.id, b.id, h.id, k.id]
        rows = electron.until('复盘列表', "(()=>{const rows=Object.fromEntries([...document.querySelectorAll('tr[data-run-id]')]"
                              ".map(r=>[r.dataset.runId,{state:r.dataset.runState,text:r.textContent}]));"
                              f"return {json.dumps(ids)}.every(id=>rows[id])&&rows}})()", 30)
        report['observed']['reflect'] = {name: rows[run.id] for name, run in (('A', a), ('B', b), ('H', h), ('K', k))}
        electron.screenshot(out / 'reflect.png')
        check('page_ended_run_done_after_report', rows[a.id]['state'] == 'done' and '已完成' in rows[a.id]['text'], rows[a.id])
        check('page_gone_terminal_ended', rows[b.id]['state'] == 'ended' and '已结束，没有报告（终端已不在）' in rows[b.id]['text'], rows[b.id])
        check('page_exited_cli_ended', rows[h.id]['state'] == 'ended' and '已结束，没有报告（CLI 已退出或没有启动）' in rows[h.id]['text'], rows[h.id])
        check('page_unknown_shows_reason', rows[k.id]['state'] == 'running' and '无法确认 CLI 是否还在：读不到终端里的进程' in rows[k.id]['text'], rows[k.id])
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
        try: kill_fixture_processes()
        except Exception as error: report['cleanup_error'] = f"{report.get('cleanup_error', '')} {error}".strip()
        if report['status'] != 'PASS' and (state / 'state.sqlite3').exists():
            # Diagnostics for a failed run: the daemon's terminal recovery events, before the fixture goes.
            rows = subprocess.run(['sqlite3', '-json', str(state / 'state.sqlite3'), "SELECT launch, type, data FROM orchestration_events WHERE type LIKE 'shell_%'"
                                   " AND type NOT IN ('shell_osc7501') ORDER BY seq"], capture_output=True, text=True)
            report['observed']['shell_events'] = json.loads(rows.stdout or '[]') if rows.returncode == 0 else rows.stderr
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        if (out / 'reflect.png').exists():
            (out / 'reflect.png').replace(args.summary.with_suffix('.png'))
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        subprocess.run(['rm', '-rf', str(fixture)], check=False)
    print(json.dumps({key: report[key] for key in ('status', 'checks', 'error') if key in report}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
