"""T-187（ready_rev 2）：agy、opencode 作受管 worker 与审查员。真实后台、门禁、经角色申请批准的终端主控；agy、opencode
用本地原生替身（t187_fake_cli.c 受管模式与 t187_fake_worker.py，不连模型），按 facts.md 实测的报告格式与 agy 信任框画面
输出。真实 CLI 另做实跑。

依据：ticket T-187 ready_rev 2。用户 2026-10-25 选“C 两者都作 worker”，选项原文：“agy 用 --dangerously-skip-permissions
全放开，只靠门禁事后检查；Git 元数据可能被改，每次派发写一次 ~/.gemini”。ticket：“agy 以 --dangerously-skip-permissions
启动；opencode 也按会话放开到能无人值守完成任务”；agy 信任“只允许写 trustedWorkspaces 这一项，由后台在 worker 启动前以 agy
自身的信任流程完成（不靠盲按回车），不写其他键。完成报告列出写入条数”；“审查员仍须只读……用文件权限（chmod）保证只读”；
验收：“两种 CLI 作 worker 时状态（运行中/空闲/等回答）在侧栏正确；做不到的信号在界面上显示‘未知’而不是猜。”

案例：
- deliver（--cli agy 或 opencode）：派一张卡给该 CLI 的 worker，交付、门禁、同 CLI 的独立审查、集成。期望：
  启动参数为 ticket 所定（agy：--dangerously-skip-permissions 与卡上的模型、强度，AGY_CLI_OSC7501=on；opencode：
  --standalone --auto 与卡上的模型）；回合中侧栏为“运行中”，结束后为“空闲”；交付经回合结束转交给门禁；审查 checkout
  只读；集成成功，尾注的模型与强度记为 unknown。agy：worker 与审查员的新目录各确认一次信任，夹具 HOME 的 settings.json
  只多这两个目录、其他键不变，记录的写入条数为 2。
- trust-no（agy）：信任框里选中的是“No, exit”。期望：后台不按键，会话记失败，settings.json 不变，任务没有交付。

失败方式（先列再写）：
1. 修前：任务卡不接受 agy、opencode。
2. 启动参数不是 ticket 所定（缺 --dangerously-skip-permissions、--standalone，模型不是卡上的）。
3. 回合不跟报告走：交付请求没有转交（任务停在 claimed），或侧栏一直“未知”。
4. 信任：不看画面就按回车（trust-no 中写进了 settings.json）；写了 trustedWorkspaces 以外的键；条数不对。
5. 审查员可以写审查 checkout（没有 chmod），门禁仍放行。
6. 尾注检查拒绝 unknown 的模型或强度，集成失败。
--revision 在该版本源码上跑；--mutant 跑已知坏实现。
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Fixture  # noqa: E402

HERE = Path(__file__).resolve().parent
MUTANTS = {
    # The reviewer's checkout keeps its write permission.
    'reviewer-writable': [('src/panes.ts', '      treeWritable(review.workspace, false);\n', '')],
    # Enter goes without reading the dialog.
    'trust-unchecked': [('src/panes.ts', '      if (dialog < 0 || yes < dialog || yes < no) throw new Refusal("agy_trust_dialog_unrecognised");\n', '')],
    # Delivery requires an observed model and effort, as for Claude and Codex.
    'facts-required': [('src/gates/core.ts', '(unobserved || facts.model', '(facts.model')],
}
FILES = {'README.md': 'fixture\n', 'check.py': 'from pathlib import Path\nassert Path("done.txt").read_text() == "done\\n"\n'}
SETTINGS = {'security': {'auth': {'selectedType': 'fixture'}}, 'trustedWorkspaces': ['/already/trusted']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--cli', choices=['agy', 'opencode'], required=True)
    parser.add_argument('--case', choices=['deliver', 'trust-no'], default='deliver')
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=MUTANTS)
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    assert not (args.case == 'trust-no' and args.cli != 'agy'), 'trust-no 只适用于 agy'
    report = dict(status='INCOMPLETE', argv=sys.argv, cli=args.cli, case=args.case, revision=args.revision, mutant=args.mutant,
                  real_model_turns=0, checks=[], failed=[], observed={})

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    fixture = Fixture('t187w-', lambda body: ('unused', [], '好的。'), revision=args.revision, patches=MUTANTS.get(args.mutant, []))
    report['fixture'] = str(fixture.dir)
    fake = fixture.dir / 'fake-bin'
    settings = fixture.home / '.gemini/antigravity-cli/settings.json'

    def events(kind=None):
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as db:
            rows = db.execute('SELECT type, launch, data FROM orchestration_events ORDER BY seq').fetchall()
        return [dict(type=t, launch=l, data=json.loads(d)) for t, l, d in rows if kind is None or t == kind]

    def launch_record(launch):
        with sqlite3.connect(f'file:{fixture.state / "state.sqlite3"}?mode=ro', uri=True) as db:
            return json.loads(db.execute('SELECT data FROM launch_records WHERE id=?', (launch,)).fetchone()[0])

    def status():
        return fixture.request('status', fixture.operator, task='demo+T-1')['task']

    def sidebar_state(launch):
        snapshot = fixture.request('sidebar_snapshot')
        return next((r.get('state') for r in snapshot.get('agents', []) if r.get('id') == launch), None)

    def watch_states(launch, until, seconds):
        seen, deadline = [], time.time() + seconds
        while time.time() < deadline:
            state = sidebar_state(launch)
            if not seen or seen[-1] != state:
                seen.append(state)
            if until():
                break
            time.sleep(0.3)
        return seen

    try:
        fake.mkdir()
        subprocess.run(['cc', '-O2', '-o', str(fake / 'agy'), str(HERE / 't187_fake_cli.c')], check=True)
        os.link(fake / 'agy', fake / 'opencode')
        shutil.copy2(HERE / 't187_fake_worker.py', fake / 't187_fake_worker.py')
        settings.parent.mkdir(parents=True)
        settings.write_text(json.dumps(SETTINGS, indent=2), encoding='utf-8')
        if args.case == 'trust-no':
            (fixture.home / '.t187-trust-no').write_text('', encoding='utf-8')
        fixture.start(args.claude, FILES, launch_config=dict(agy_bin=str(fake / 'agy'), opencode_bin=str(fake / 'opencode')))
        card = fixture.out / 'T-1.json'
        card.write_text(json.dumps(dict(id='T-1', source=None, goal='在仓库根目录加 done.txt', non_goals=['不改别的文件'],
            paths=dict(allow=['done.txt'], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
            red_commands=[], task_type='测试', repair_target=None, complexity='S',
            executor=dict(cli=args.cli, model='fixture-model', effort='high'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
        saved = fixture.request('card_save', fixture.terminal, task='T-1', card=str(card), expected_version=0)
        report['observed']['card_save'] = {k: saved.get(k) for k in ('ok', 'error', 'details')}
        check('card_accepts_cli', saved.get('ok') is True, report['observed']['card_save'])
        assert saved.get('ok'), saved
        assert fixture.request('create', fixture.terminal, task='T-1', project='demo', repo=str(fixture.repo),
                               branch='refs/heads/main', card_version=1)['ok']
        main_before = fixture.git('rev-parse', 'refs/heads/main')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        report['observed']['dispatch'] = {k: dispatched.get(k) for k in ('ok', 'error', 'details')}
        assert dispatched.get('ok'), dispatched
        thread = dispatched['attempt']['thread_id']
        worker = fixture.run_cli('pane_status', '--thread', thread)['launch']
        record = launch_record(worker)
        report['observed']['worker_argv'] = record['argv']
        expected_argv = (['--dangerously-skip-permissions', '--model', 'fixture-model', '--effort', 'high'] if args.cli == 'agy'
                         else ['--standalone', '--auto', dispatched['attempt']['workspace']])
        check('worker_argv', record['argv'][1:] == expected_argv and record['cli'] == args.cli and record['sandbox'] == 'none',
              dict(argv=record['argv'], cli=record['cli'], sandbox=record['sandbox']))
        check('worker_env', record['env'].get('AGY_CLI_OSC7501') == 'on' if args.cli == 'agy'
              else json.loads(record['env'].get('OPENCODE_CONFIG_CONTENT', '{}')) == {'model': 'fixture-model'},
              {k: record['env'].get(k) for k in ('AGY_CLI_OSC7501', 'OPENCODE_CONFIG_CONTENT')})

        if args.case == 'trust-no':
            fixture.wait('信任失败', lambda: events('agy_trust_failed'), 30)
            time.sleep(2)
            check('trust_no_failed', bool(events('agy_trust_failed')) and not events('agy_trust_confirm_intent'),
                  [e['data'] for e in events('agy_trust_failed')])
            check('trust_no_settings_unchanged', json.loads(settings.read_text(encoding='utf-8')) == SETTINGS, settings.read_text())
            check('trust_no_not_delivered', status()['state'] != 'submitted' and not events('turn_start_signal'), status()['state'])
            check('trust_no_sidebar_unknown', sidebar_state(worker) == 'unknown', sidebar_state(worker))
        else:
            seen = watch_states(worker, lambda: status()['state'] == 'submitted', 120)
            report['observed']['worker_states'] = seen
            check('submitted', status()['state'] == 'submitted', status()['state'])
            check('sidebar_running_during_turn', 'running' in seen, seen)
            idle = watch_states(worker, lambda: sidebar_state(worker) == 'idle', 20)
            check('sidebar_idle_after_turn', idle[-1] == 'idle', idle)
            verified = fixture.request('verify', fixture.terminal, task='T-1')
            report['observed']['verify'] = {k: verified.get(k) for k in ('ok', 'error', 'details')}
            check('verify_started', verified.get('ok') is True, report['observed']['verify'])
            assert verified.get('ok'), verified
            review = fixture.wait('审查开始', lambda: status().get('review'), 60)
            reviewer = fixture.run_cli('pane_status', '--thread', review['thread_id'])['launch']
            reviewed = fixture.wait('审查结束', lambda: status()['review'].get('state') in ('passed', 'needs_fix', 'failed') and status(), 120)
            report['observed']['review'] = {k: reviewed['review'].get(k) for k in ('state', 'result', 'failure')}
            report['observed']['review_events'] = [e['type'] for e in events() if e['launch'] == reviewer][-12:]
            check('review_passed', reviewed['state'] == 'verified' and reviewed['review']['state'] == 'passed', report['observed']['review'])
            check('review_checkout_read_only', any(e['launch'] == reviewer for e in events('review_checkout_read_only')))
            if args.cli == 'agy':
                written = events('agy_trust_written')
                trusted = json.loads(settings.read_text(encoding='utf-8'))
                report['observed']['trust'] = dict(written=[e['data'] for e in written], settings=trusted)
                check('trust_two_entries', sum(e['data']['entries_written'] for e in written) == 2 and
                      {e['launch'] for e in written} == {worker, reviewer}, report['observed']['trust'])
                check('trust_only_trusted_workspaces', {k: v for k, v in trusted.items() if k != 'trustedWorkspaces'} ==
                      {k: v for k, v in SETTINGS.items() if k != 'trustedWorkspaces'} and
                      trusted['trustedWorkspaces'] == SETTINGS['trustedWorkspaces'] + [record['worktree'], launch_record(reviewer)['worktree']],
                      trusted)
            fixture.wait('审查会话回收', lambda: any(e['type'] == 'review_reclaimed' for e in
                                                  fixture.request('events', fixture.operator, task='demo+T-1')['events']), 60)
            score = fixture.out / 'score.json'
            score.write_text(json.dumps(dict(result='通过', boundary_discipline=3, boundary_reason='夹具', engineering_taste=3,
                                             engineering_reason='夹具', notes='T-187 managed worker fixture'), ensure_ascii=False), encoding='utf-8')
            integrated = fixture.request('integrate', fixture.terminal, task='T-1', score_file=str(score))
            report['observed']['integrate'] = {k: integrated.get(k) for k in ('ok', 'error', 'details')}
            head = fixture.git('rev-parse', 'refs/heads/main')
            check('integrated', integrated.get('ok') is True and status()['state'] == 'accepted' and head != main_before and
                  fixture.git('show', f'{head}:done.txt') == 'done', report['observed']['integrate'])
            trailers = fixture.git('log', '-1', '--format=%B', status()['candidate_commit'])
            report['observed']['trailers'] = trailers
            check('trailers_unknown_model_effort', 'A2A-Model: unknown' in trailers and 'A2A-Effort: unknown' in trailers, trailers)
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()[-2500:]
    finally:
        fixture.stop()
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        if report['status'] == 'PASS':
            shutil.rmtree(fixture.dir, ignore_errors=True)
    print(json.dumps(dict(status=report['status'], failed=[f['name'] for f in report['failed']], error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
