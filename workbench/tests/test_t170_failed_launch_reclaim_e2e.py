"""T-170：Codex CLI 在建立原生会话前启动失败，attempt 无法回收。真实后台 / 门禁 / PTY；Codex 换成
重放 T-164 第三轮 B a2 原始终端输出的替身（不发任何模型请求）。

失败方式（先列再写）：
1. 启动失败的 attempt（launch_failed、原生会话为空、进程已退出）reclaim 被拒 identity_conflict，
   任务永远停在 claimed，不能修订后重派。
2. 修复放得太宽：原生会话为空但 CLI 仍在运行（启动卡住）时也被回收，正在跑的进程被当成死的。
3. 回收后工作区或分支残留，或任务仍占着该 attempt，后续派发被挡。
4. 用重试、超时或改状态绕过门禁取得表面成功。
5. 把夹具自身的启动错误算成产品红态，或覆盖旧证据。

期望来自 T-170 ticket：已确认退出、从未建立原生会话、没有回合的 attempt 可以经门禁回收，
回收后任务可再派发；原生会话为空但进程还活着时仍拒绝。
--revision 只选择产品源码（修前运行应复现红态）。
--scenario failed（默认）：替身打印原始启动画面与报错后退出 1。
--scenario fast：替身不停顿，立刻打印报错退出 1；进程可能在 leader 被观察到、dispatch 回执之前就退出
（2026-10-24 全量回归负载下出现）。
--scenario hang：替身打印启动画面后一直不退出（反例）。
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

from scripted_claude import Fixture


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'evidence/2026-10-23-batch24/T-170/b-a2-pty.raw'
# A compiled stand-in: the pane's leader is the process whose command path is the
# launched executable, as with the real codex binary (an interpreted script would not match).
FAKE = r'''#include <stdio.h>
#include <string.h>
#include <unistd.h>
static const char *RAW = "%s";
int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) if (!strcmp(argv[i], "--version")) { puts("codex-cli 0.164.0"); return 0; }
  FILE *f = fopen(RAW, "rb"); static char buf[65536]; size_t n = fread(buf, 1, sizeof buf, f); fclose(f);
  const char *marker = "Error: account/read failed"; size_t cut = 0;
  for (size_t i = 0; i + strlen(marker) <= n; i++) if (!memcmp(buf + i, marker, strlen(marker))) { cut = i; break; }
  write(1, buf, cut); sleep(%d);
  if (%d) for (;;) sleep(60);
  write(1, buf + cut, n - cut); return 1;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude'))
    parser.add_argument('--revision')
    parser.add_argument('--scenario', choices=['failed', 'fast', 'hang'], default='failed')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, scenario=args.scenario,
                  product_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  vendor_model_turns=0, red_reproduced=False, checks=[], observed={}, errors=[])
    fixture = None

    def record(name, passed, detail=None):
        report['checks'].append(dict(name=name, passed=bool(passed), detail=detail))

    try:
        fixture = Fixture('t170-', lambda _: (_ for _ in ()).throw(AssertionError('禁止模型请求')), revision=args.revision)
        report['fixture'] = str(fixture.dir)
        fake = fixture.dir / 'fake-codex'
        (fixture.dir / 'fake-codex.c').write_text(FAKE % (RAW, 0 if args.scenario == 'fast' else 3, int(args.scenario == 'hang')), encoding='utf-8')
        subprocess.run(['cc', '-o', str(fake), str(fixture.dir / 'fake-codex.c')], check=True)
        codex_home = fixture.home / '.codex'
        codex_home.mkdir()
        original_cli = fixture.run_cli

        def configured_cli(*arguments):
            if arguments[0] == 'daemon_start':
                path = fixture.dir / 'launch-config.json'
                config = json.loads(path.read_text(encoding='utf-8'))
                config.update(codex_bin=str(fake), codex_home=str(codex_home))
                path.write_text(json.dumps(config), encoding='utf-8')
            return original_cli(*arguments)

        fixture.run_cli = configured_cli
        fixture.start(args.claude, {'README.md': 'T-170 fixture\n', 'check.py': 'raise SystemExit(0)\n'})
        task = 'T-X'
        card = fixture.out / 'T-X.json'
        card.write_text(json.dumps(dict(id=task, source=None, goal='启动失败后回收', non_goals=['不改文件'],
            paths=dict(allow=['note.txt'], deny=[]), oracle_paths=['check.py'], completion_conditions=[dict(argv=['python3', 'check.py'])],
            red_commands=[], task_type='测试', repair_target=None, complexity='S',
            executor=dict(cli='Codex', model='zcode/GLM-5.3-Flash', effort='max'), base_commit=None, writer=None), ensure_ascii=False), encoding='utf-8')
        for result in [fixture.request('card_save', fixture.terminal, task=task, card=str(card), expected_version=0),
                       fixture.request('create', fixture.terminal, task=task, project='demo', repo=str(fixture.repo), branch='refs/heads/main', card_version=1)]:
            assert result.get('ok'), result
        dispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
        report['observed']['dispatch'] = dict(ok=dispatched.get('ok'), error=dispatched.get('error'))
        # A CLI that dies inside the dispatch window makes dispatch itself answer run_blocked;
        # the claimed attempt is then read back through status.
        attempt = dispatched['attempt'] if dispatched.get('ok') else \
            fixture.request('status', fixture.operator, task='demo+' + task)['task']['current_attempt']
        report['observed']['attempt'] = attempt
        assert attempt, dispatched

        def events():
            return [event for event in fixture.request('orchestration_events', task='demo+' + task)['events']
                    if event['type'] in ('launch_failed', 'pane_exit', 'pane_leader_observed')]

        if args.scenario != 'hang':
            fixture.wait('替身启动失败被记录', lambda: any(event['type'] == 'launch_failed' for event in events()), 60)
            fixture.wait('窗格进程退出', lambda: any(event['type'] == 'pane_exit' for event in events()), 30)
        else:
            fixture.wait('替身成为窗格前台进程', lambda: any(event['type'] == 'pane_leader_observed' for event in events()), 60)
            time.sleep(5)  # Past the replayed banner; the stand-in now just stays alive.
            record('scenario_cli_still_running', not any(event['type'] in ('launch_failed', 'pane_exit') for event in events()))
        status = fixture.request('status', fixture.operator, task='demo+' + task)['task']
        report['observed']['before'] = status['current_attempt']
        record('no_native_session', (status['current_attempt']['runtime_identity'] or {}).get('native_session') is None)
        reclaimed = fixture.request('reclaim', fixture.terminal, task='demo+' + task, attempt=attempt['attempt_id'])
        report['observed']['reclaim'] = reclaimed
        after = fixture.request('status', fixture.operator, task='demo+' + task)['task']
        report['observed']['after'] = dict(state=after['state'], current_attempt=after['current_attempt'])
        workspace = Path(attempt['workspace'])
        if args.scenario != 'hang':
            record('reclaim_accepted', reclaimed.get('ok'), reclaimed)
            record('attempt_reclaimed', bool(after['current_attempt'] and after['current_attempt'].get('reclaimed')) or after['current_attempt'] is None,
                   after['current_attempt'])
            record('workspace_removed', not workspace.exists(), str(workspace))
            again = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
            # The stand-in fails every launch, so a fast redispatch is itself run_blocked; what matters is
            # that the gate took the task again with a new attempt instead of answering already_claimed.
            current = fixture.request('status', fixture.operator, task='demo+' + task)['task']['current_attempt']
            report['observed']['redispatch'] = dict(ok=again.get('ok'), error=again.get('error'),
                                                    attempt=current and current['attempt_id'])
            record('task_dispatchable_again', (again.get('ok') or again.get('error') == 'run_blocked') and current and
                   current['attempt_id'] != attempt['attempt_id'], report['observed']['redispatch'])
            report['red_reproduced'] = bool(not reclaimed.get('ok') and reclaimed.get('error') == 'identity_conflict')
        else:
            record('live_cli_not_reclaimed', not reclaimed.get('ok'), reclaimed)
            record('workspace_kept', workspace.exists(), str(workspace))
        report['status'] = 'PASS' if all(check['passed'] for check in report['checks']) else 'INCOMPLETE'
    except Exception as error:
        report['errors'].append(dict(error=str(error), traceback=traceback.format_exc()))
    finally:
        if fixture:
            try:
                report['observed']['timeline'] = [dict(seq=e['seq'], type=e['type']) for e in fixture.request(
                    'orchestration_events', task='demo+T-X')['events'] if e['type'] != 'terminal_output']
            except Exception as error:
                report['errors'].append(dict(diagnostics=str(error)))
            try:
                fixture.stop()
            except Exception as error:
                report['status'] = 'INCOMPLETE'
                report['errors'].append(dict(cleanup='fixture', error=str(error)))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status=report['status'], red_reproduced=report['red_reproduced'], summary=str(args.summary)), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
