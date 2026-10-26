"""T-187（ready_rev 2）验收第 2 条：真实 agy、opencode 走完一遍主控派发。项目终端里启动一种 CLI 作主控 → 经角色申请批准 →
派卡给另一种 CLI 的 worker → 同 CLI 的独立审查 → 门禁集成。隔离后台、Electron；CLI 用用户自己的安装与 HOME（用户 2026-10-25：
“用我电脑原生的就行,隔离 HOME 可能不太行”），不登录、不复制凭据。

ticket 验收原话：“真实各跑一遍：agy 主控派 opencode worker，opencode 主控派 agy worker（项目终端→申请主控→批准→派给另一种 CLI
的 worker→独立审查→门禁集成），留截图与记录”；“两种 CLI 作 worker 时状态（运行中/空闲/等回答）在侧栏正确；做不到的信号在界面上
显示‘未知’而不是猜”；agy 信任“完成报告列出写入条数”。

主控的命令由测试写成脚本（dispatch.sh、verify.sh、integrate.sh），提示里让主控运行它：命令仍以主控自己的终端身份执行，脚本只免去
模型手抄 JSON 引号。agy 主控用 `agy --dangerously-skip-permissions`（--mode auto 下每条 shell 命令都弹权限框、agy 没有按会话的命令
白名单；用户 2026-10-25 选“主控也用全放开”），项目目录放在已信任的 /private/tmp/t187-probe/repo，主控不新增信任项；
agy worker 与审查员各在新目录，由后台按信任流程各写一条。

失败方式（先列再写）：
1. 主控没有运行申请或脚本（模型行为），或申请记成别的 CLI。
2. worker 没有交付（回合没跟上、交付请求没转交），任务停在 claimed。
3. 审查员没写结果文件、写错格式，或能写审查 checkout。
4. 集成失败，或尾注不是 unknown。
5. 信任写入了预期以外的目录或键。
6. 侧栏 worker 状态从不出现“运行中”，或结束后不是“空闲”。
登录、额度、模型错误如实记录，不判通过。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import traceback
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture  # noqa: E402

TRUSTED_PROBE = Path('/private/tmp/t187-probe/repo')
GEMINI = Path.home() / '.gemini/antigravity-cli/settings.json'
WORKER = dict(agy=dict(model='gemini-3.8-flash-high', effort='high'), opencode=dict(model='opencode/big-pickle', effort='high'))
FILES = {'README.md': '# demo\n', 'check.py': 'from pathlib import Path\nassert Path("done.txt").read_text() == "done\\n"\n'}


def trusted():
    return json.loads(GEMINI.read_text(encoding='utf-8')).get('trustedWorkspaces', [])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--controller', choices=['agy', 'opencode'], required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    worker_cli = 'opencode' if args.controller == 'agy' else 'agy'
    report = dict(status='INCOMPLETE', argv=sys.argv, controller=args.controller, worker=worker_cli, real_prompts=0,
                  checks=[], failed=[], observed={}, states=[])

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    if args.controller == 'agy':
        assert str(TRUSTED_PROBE) in trusted(), '主控目录不在已信任列表里'
        assert not TRUSTED_PROBE.exists(), f'{TRUSTED_PROBE} 已存在，先核对再删'
        TRUSTED_PROBE.parent.mkdir(exist_ok=True)
    fixture = Fixture('t187x-', lambda body: ('unused', [], '好的。'), home=Path.home(),
                      repo=TRUSTED_PROBE if args.controller == 'agy' else None)
    report['fixture'] = str(fixture.dir)
    trusted_before = trusted()
    electron = None

    def raw(launch):
        return (fixture.state / 'traces' / launch / 'pty.raw').read_text(encoding='utf-8', errors='replace')

    def text(launch):
        return re.sub(r'[ \t]+', ' ', re.sub(r'\x1b\[[0-9;?<>=]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw(launch)))

    def reports(launch):
        return re.findall(r'\x1b\]7501;([^\x07\x1b]*)', raw(launch))

    def type_in(term, data):
        term['sequence'] += 1
        sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
        assert sent['ok'], sent

    def prompt(term, words):
        term['mark'] = len(reports(term['launch']))
        type_in(term, words)
        time.sleep(1)
        type_in(term, '\r')
        report['real_prompts'] += 1

    def row(launch):
        snapshot = fixture.request('sidebar_snapshot')
        return next((r for r in snapshot.get('agents', []) + snapshot.get('terminals', []) if r.get('id') == launch), {})

    def status():
        return fixture.request('status', fixture.operator, task=f'{fixture.project}+T-1').get('task') or {}

    def events(kind):
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as db:
            rows = db.execute('SELECT launch, data FROM orchestration_events WHERE type=? ORDER BY seq', (kind,)).fetchall()
        return [dict(launch=l, data=json.loads(d)) for l, d in rows]

    def controller_idle(term, seconds):
        """Wait until the controller's last report ends a turn (agy: done, opencode: clear, either: idle) after a working report since the last prompt was sent."""
        start = term['mark']
        fixture.wait('主控回合结束', lambda: any(r.startswith('state=working') for r in reports(term['launch'])[start:]) and
                     reports(term['launch'])[-1].startswith(('state=idle', 'state=clear', 'state=done')), seconds)

    def watch_worker(label, until, seconds):
        deadline, last = time.time() + seconds, None
        while time.time() < deadline:
            task = status()
            thread = (task.get('current_attempt') or {}).get('thread_id')
            # While the attempt is preparing its thread id exists before its pane does.
            launch = fixture.request('pane_status', fixture.operator, thread=thread).get('launch') if thread else None
            state = row(launch).get('state') if launch else None
            current = (task.get('state'), state)
            if current != last:
                report['states'].append(dict(phase=label, t=round(time.time(), 1), task=current[0], worker=current[1]))
                last = current
            if until(task):
                return task
            time.sleep(1)
        raise AssertionError(f'超时：{label}，最后 {last}')

    try:
        fixture.start(args.claude, FILES, launch_config=dict(agy_bin=shutil.which('agy'), opencode_bin=shutil.which('opencode')))
        assert fixture.request('role_release', fixture.terminal)['ok']
        electron = Electron(fixture, 't187x-' + fixture.dir.name[6:])
        electron.until('项目出现', f"!!document.querySelector('[data-project-id=\"{fixture.project}\"]')")
        electron.evaluate(f"document.querySelector('[data-project-id=\"{fixture.project}\"]').click()")
        launch = fixture.run_cli('shell_start', '--project', fixture.project, '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project=fixture.project)
        assert window['ok'], window
        term = dict(launch=launch, identity=window['identity'], sequence=0)
        electron.until('终端窗格', f"(()=>{{const r=document.querySelector('[data-agent-launch=\"{launch}\"]');if(r)r.click();"
                       f"return !!document.querySelector('.pane[data-launch-id=\"{launch}\"]')}})()", 30)
        type_in(term, ('agy --dangerously-skip-permissions' if args.controller == 'agy' else 'opencode') + '\r')
        fixture.wait(f'{args.controller} 就绪', lambda: any(r.startswith('state=idle') for r in reports(launch)), 120)
        time.sleep(3)

        # 1. The controller asks for the role; the user approves in the app.
        prompt(term, '你来当执行主控。申请生效以后先停下，什么都不要派，只回复“已就绪”。')
        pending = fixture.wait('角色申请', lambda: [r for r in fixture.request('sidebar_snapshot').get('role_requests', [])
                                                   if r.get('launch') == launch], 300)
        report['observed']['request_cli'] = pending[0].get('cli')
        check('request_cli', pending[0].get('cli') == args.controller, pending[0])
        assert fixture.request('role_request_decide', fixture.operator, role_request=pending[0]['id'], approved=True)['ok']
        fixture.wait('角色生效', lambda: row(launch).get('role') == 'controller' or None, 120)
        controller_idle(term, 300)

        # 2. Dispatch to the other CLI.
        card = fixture.out / 'T-1.json'
        card.write_text(json.dumps(dict(id='T-1', source=None, goal='在仓库根目录新建 done.txt，内容只有一行 done', non_goals=['不改别的文件'],
            paths=dict(allow=['done.txt'], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
            red_commands=[], task_type='测试', repair_target=None, complexity='S',
            executor=dict(cli=worker_cli, **WORKER[worker_cli]), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
        call = lambda body: "a2a call '" + json.dumps(body, ensure_ascii=False) + "'"
        scripts = {
            'dispatch.sh': ' && '.join([call(dict(command='card_save', task='T-1', card=str(card), expected_version=0)),
                                        call(dict(command='create', task='T-1', project=fixture.project, repo=str(fixture.repo),
                                                  branch='refs/heads/main', card_version=1)),
                                        call(dict(command='dispatch', task='T-1', runtimeMode='workspace-write', **WORKER[worker_cli]))]),
            'verify.sh': call(dict(command='verify', task='T-1')),
            'integrate.sh': call(dict(command='integrate', task='T-1', score_file=str(fixture.out / 'score.json'))),
        }
        for name, body in scripts.items():
            (fixture.out / name).write_text('set -e\n' + body + '\n', encoding='utf-8')
        (fixture.out / 'score.json').write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='只加了 done.txt',
            engineering_taste=3, engineering_reason='最小改动', notes='T-187 real run'), ensure_ascii=False), encoding='utf-8')
        prompt(term, f'运行 sh {fixture.out}/dispatch.sh ，它依次保存任务卡、建任务、派发给 {worker_cli} worker。输出都是 ok 后只回复“已派发”，不要做别的。')
        fixture.wait('派发', lambda: status().get('current_attempt'), 300)
        task = watch_worker('worker', lambda t: t.get('state') == 'submitted', 1200)
        worker = fixture.run_cli('pane_status', '--thread', task['current_attempt']['thread_id'])['launch']
        electron.screenshot(fixture.out / 'worker-submitted.png')
        check('worker_running_seen', any(s['phase'] == 'worker' and s['worker'] == 'running' for s in report['states']), report['states'])
        fixture.wait('worker 空闲', lambda: row(worker).get('state') == 'idle', 120)
        check('worker_idle_after_turn', row(worker).get('state') == 'idle', row(worker))
        controller_idle(term, 300)

        # 3. Verify: the gate's checks and an independent review by the same CLI.
        prompt(term, f'运行 sh {fixture.out}/verify.sh ，开始门禁验收与独立审查。输出 ok 后只回复“已开始验收”，不要做别的。')
        reviewed = watch_worker('review', lambda t: (t.get('review') or {}).get('state') in ('passed', 'needs_fix', 'failed'), 1500)
        report['observed']['review'] = {k: reviewed['review'].get(k) for k in ('state', 'result', 'failure')}
        check('review_passed', reviewed['review']['state'] == 'passed' and reviewed['state'] == 'verified', report['observed']['review'])
        fixture.wait('审查会话回收', lambda: any(e['type'] == 'review_reclaimed' for e in
                                                  fixture.request('events', fixture.operator, task=f'{fixture.project}+T-1')['events']), 120)
        controller_idle(term, 300)

        # 4. Integrate with the score.
        main_before = fixture.git('rev-parse', 'refs/heads/main')
        prompt(term, f'运行 sh {fixture.out}/integrate.sh ，把通过验收的交付集成。输出 ok 后只回复“已集成”，不要做别的。')
        done = fixture.wait('集成', lambda: status().get('state') in ('accepted', 'failed') and status(), 300)
        head = fixture.git('rev-parse', 'refs/heads/main')
        check('integrated', done['state'] == 'accepted' and head != main_before and fixture.git('show', f'{head}:done.txt') == 'done', done['state'])
        trailers = fixture.git('log', '-1', '--format=%B', done['candidate_commit'])
        report['observed']['trailers'] = trailers
        check('trailers', f'A2A-Tool: ' in trailers and 'A2A-Model: unknown' in trailers and 'A2A-Effort: unknown' in trailers, trailers)
        controller_idle(term, 300)
        electron.screenshot(fixture.out / 'integrated.png')

        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as db:
            argv = json.loads(db.execute('SELECT data FROM launch_records WHERE id=?', (worker,)).fetchone()[0])['argv']
        report['observed']['worker_argv'] = argv
        written = events('agy_trust_written')
        added = [p for p in trusted() if p not in trusted_before]
        report['observed']['trust'] = dict(written=[e['data'] for e in written], added=added,
                                           entries_written=sum(e['data']['entries_written'] for e in written))
        expected = 2 if worker_cli == 'agy' else 0
        check('trust_entries', len(added) == expected == report['observed']['trust']['entries_written'] and
              set(added) == {e['data']['folder'] for e in written}, report['observed']['trust'])
        check('review_checkout_read_only', bool(events('review_checkout_read_only')))
        (fixture.out / 'controller-screen.txt').write_text(text(launch)[-20000:], encoding='utf-8')
        (fixture.out / 'worker-screen.txt').write_text(text(worker)[-20000:], encoding='utf-8')
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()[-2500:]
        try:
            report['observed']['last_task'] = {k: status().get(k) for k in ('state', 'review', 'failure')}
            report['observed']['trust_added'] = [p for p in trusted() if p not in trusted_before]
        except Exception as detail:
            report['observed']['last_task'] = str(detail)
    finally:
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(status=report['status'], failed=[f['name'] for f in report['failed']], error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
